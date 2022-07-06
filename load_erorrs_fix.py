from ast import literal_eval
from datetime import datetime
import json
import os
import sys
import numpy as np
import pandas as pd
import pickle
from modules.Load_to_starpi import Load_To_Strapi


curdir = os.path.dirname(os.path.realpath(__file__))
cpath = os.path.dirname(curdir)
if not cpath in sys.path:
    sys.path.append(cpath)

 
from modules.analyzer_utils import get_repo_meta_pyanalysis 



platform = "stage"

if os.path.exists(".env/secret.json"):
    with open(".env/secret.json", "r") as s:
        secret = json.load(s)
        try:
            github_token = secret["github_token"]
            strapi_token = secret["strapi_token"][platform]
        except:
            github_token = None
            strapi_token = None
else:
    github_token = None
    strapi_token = None


if github_token and strapi_token:

    state_path = "data/api_state/week/week_state.pk"
    
    if os.path.exists(state_path):
        with open(state_path, "rb") as s_d:
            state_dict = pickle.load(s_d)
    
    else:
        print("\nThe state file does not exit and system will exit now...\n")
        sys.exit(1)

    current_week = datetime.now().isocalendar()[1] - 3
    training_week = current_week - 18
    
    week= "week{}".format(training_week)
    print("\nCurrent week is {}\n".format(week))
    batch = state_dict["batch"]
    state_run_number = state_dict["run_number"]
    run_number = "b{}_r{}".format(batch, state_run_number)

    base_url = state_dict["base_url"][platform]

    client_url = base_url + "/graphql"

    
    
    
    error_fix_file_path = "data/error_fix/b{}_{}_run{}_error_fix.csv".format(batch, week, run_number)
    github_df = pd.read_csv(error_fix_file_path)
    github_df = github_df.drop_duplicates(subset=["trainee_id"])
    github_df = github_df.replace({np.nan: None})

    github_df["assignments_ids"] = github_df["assignments_ids"].apply(lambda x: literal_eval(x))
    github_df["trainee"] = github_df["trainee"].apply(lambda x: int(x))



    # check if github_df was returned
    if isinstance(github_df, pd.DataFrame) and not github_df.empty:
        

        starter_code_url = None #"https://github.com/10xac/Twitter-Data-Analysis"




        # get reference data
        if starter_code_url:
            print("Computing values for starter code...\n")
            try:
                # get the repo name
                starter_user_name = starter_code_url.split("/")[-2]
                starter_repo_name = starter_code_url.split("/")[-1]

                print("Starter code user name: ", starter_user_name, "\n")
                print("Starter code repo name: ", starter_repo_name, "\n")

                # set the inerested repo keys
                interested_repo_meta_keys = ["num_ipynb", "num_js", "num_py", "num_dirs", "num_files", "total_commits"]
                
                interested_repo_analysis_keys = ['avg_lines_per_class', 'avg_lines_per_function', 'avg_lines_per_method', 
                                                'difficulty', 'effort', 'lloc', 'loc', 'num_classes', 'num_functions', 
                                                'num_methods', 'sloc', 'time']
                combined_keys = interested_repo_meta_keys + interested_repo_analysis_keys

                # get the repo analysis data
                starter_repo_data = get_repo_meta_pyanalysis(starter_user_name, github_token, starter_repo_name)
                starter_code_data = dict()
                
                if len(starter_repo_data["repo_meta"]) > 1:
                    starter_code_data.update(starter_repo_data["repo_meta"])
                
                if len(starter_repo_data["repo_anlysis_metrics"]) > 1:
                    starter_code_data.update(starter_repo_data["repo_anlysis_metrics"])

                starter_code_data = {k: v for k, v in starter_code_data.items() if k in combined_keys}

                # set the base values

                starter_code_ref_basevalues = {col: starter_code_data[col] for col in combined_keys if col in starter_code_data}
            
            except Exception as e:
                print("Error getting starter code data \n")
                print("Error: ", e)
                starter_code_ref_basevalues = None

        else:
            starter_code_ref_basevalues = None 


        to_strapi = Load_To_Strapi(platform=platform, week=week, batch=batch, run_number=run_number, base_url=base_url, github_df=github_df, github_token=github_token, strapi_token=strapi_token, run_type="fix")

        to_strapi.run_to_load()
        
    else:
        # if trainee data is not returned
        if isinstance(github_df, pd.DataFrame):
            print("No assignment data returned. Hence no entries to be made into metric rank and metric summary tables\n\n")
            sys.exit(1)
        
        else:
            print("There was an error retrieving assignment data")
            sys.exit(1)

else:
    # if token is not returned
    print("Error: Github and Strapi tokens were not found")
    sys.exit(1)


    