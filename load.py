from datetime import datetime
import json
import os
import sys
import pandas as pd
import pickle
from modules.dup_load_to_strapi import Load_To_Strapi
from modules.Prepare_Assignment_Submissions import PrepareAssignmentDf
from modules.Treat_Assignment_Response import Get_Assignment_Data


# curdir = os.path.dirname(os.path.realpath(__file__))
# cpath = os.path.dirname(curdir)
# if not cpath in sys.path:
#     sys.path.append(cpath)


  
from modules.analyzer_utils import  get_repo_meta_pyanalysis



platform = "dev"

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

    current_week = datetime.now().isocalendar()[1] - 5
    training_week = current_week - 18
    
    week= "week{}".format(training_week)
    print("\nCurrent week is {}\n".format(week))
    batch = state_dict["batch"]
    state_run_number = state_dict["run_number"]
    run_number = "b{}_r{}".format(batch, state_run_number)

    base_url = state_dict["base_url"][platform]
    previous_analyzed_assignments = state_dict["previously_analyzed_assignments"]

    client_url = base_url + "/graphql"
    
    assgn = Get_Assignment_Data(week, batch, base_url, strapi_token, previous_analyzed_assignments)

    assignmnent_data_df = assgn.filtered_data_df()

    # check if assignmnent_data_df was returned
    if isinstance(assignmnent_data_df, pd.DataFrame) and not assignmnent_data_df.empty:
        #trainee_df = get_id_userid_df(trainee_dict)



        # read in the data
        #dt_user = pd.read_csv("data/github_usernames.csv")
        #dt_repo = pd.read_csv("data/github_repos_wk1.csv")
        #github_df = dt_user.merge(dt_repo, on="trainee_id")
        #github_df = pd.read_csv("data/try.csv")
        #github_df = pd.read_csv("data/week_data/batch4/b4_wk{}.csv".format(training_week))
        #github_df = pd.read_csv("data/week_data/batch5/b5_week0_github_df.csv")

        #gd = gsheet(sheetid="1gtkfGAmH9HR05_i7g6t2tF9t8LHfopybIhEqYdrxCSg",fauth='gdrive_10acad_auth.json')
        #gsheet_df = gd.get_sheet_df("b5_github_submissions")


        prep_assn = PrepareAssignmentDf(assignmnent_data_df, run_number, "root_url")

        now_date = datetime.now()
        now_folder = now_date.strftime("%Y-%m-%d")
        now_str = now_date.strftime("%Y-%m-%d_%H-%M-%S")
        
        week_submission_dir = "data/week_data/batch{}/{}/{}/{}/run{}".format(batch, week, platform,now_folder,run_number)
        week_submission_path = week_submission_dir + "/b{}_{}_{}_run{}_{}.csv".format(batch, week, platform, run_number, now_str)
        
        if not os.path.isdir(week_submission_dir):
            os.makedirs(week_submission_dir)

        github_df = prep_assn.get_df(week_submission_path)

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


        to_strapi = Load_To_Strapi(platform, week, batch, run_number, base_url, github_df, github_token, strapi_token)

        to_strapi.run_to_load()  
          
    else:
        # if trainee data is not returned
        if isinstance(assignmnent_data_df, pd.DataFrame):
            print("No assignment data returned. Hence no entries to be made into metric rank and metric summary tables\n\n")
            sys.exit(1)
        
        else:
            print("There was an error retrieving assignment data".format(assignmnent_data_df["error"]))
            sys.exit(1)

else:
    # if token is not returned
    print("Error: Github and Strapi tokens were not found")
    sys.exit(1)


    