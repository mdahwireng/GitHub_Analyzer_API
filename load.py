from datetime import datetime
import time
import json
import os
import sys
from inflection import pluralize
import pandas as pd
import pickle
import numpy as np
from app import get_user
from modules.Prepare_Assignment_Submissions import PrepareAssignmentDf
from modules.Treat_Assignment_Response import Get_Assignment_Data


curdir = os.path.dirname(os.path.realpath(__file__))
cpath = os.path.dirname(curdir)
if not cpath in sys.path:
    sys.path.append(cpath)



from modules.strapi_methods import get_table_data_strapi, get_trainee_data, insert_data_strapi, update_data_strapi   
from modules.analyzer_utils import get_break_points, get_id_userid_df, get_metric_category, get_metric_summary_dict, get_repo_meta_pyanalysis,normalize_repo_data
from modules.gdrive import gsheet
from modules.Prepare_Github_Submissions import PrepareGithubDf

if os.path.exists(".env/secret.json"):
    with open(".env/secret.json", "r") as s:
        secret = json.load(s)
        try:
            github_token = secret["github_token"]
            strapi_token = secret["strapi_token"]["dev"]
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

    current_week = datetime.now().isocalendar()[1] - 6
    training_week = current_week - 18
    
    week= "week{}".format(training_week)
    batch = state_dict["batch"]
    run_number = state_dict["run_number"]

    base_url = "https://dev-cms.10academy.org"
    
    assgn = Get_Assignment_Data(week, batch, base_url, strapi_token)

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
        
        week_submission_dir = "data/week_data/batch{}".format(batch)
        week_submission_path = week_submission_dir + "/b{}_{}.csv".format(batch, week)
        
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


        # set needed variables
        repo_df_cols = ["html_url", "week"]

        metrics_list = ["additions","avg_lines_per_class","avg_lines_per_function","avg_lines_per_method",
                        "cc","difficulty",'effort','lloc','loc','mi','num_classes','num_functions','num_methods',
                        'sloc','time']
        
        sum_list =  ["additions","difficulty",'effort','lloc','loc','num_classes','num_functions','num_methods',
                     'sloc','time']

        user_df_cols = ["trainee_id",'avatar_url', 'bio', 'commits', 'email', 'followers', 'following', 'html_url', 
                        'issues', 'name', 'public_repos', 'pull_requests', "run_number"]

        repo_analysis_df_cols = ["trainee_id",'additions', 'avg_lines_per_class', 'avg_lines_per_function', 'avg_lines_per_method',
                                'blank', 'cc', 'cc_rank', 'comments', 'difficulty', 'effort', 'lloc', 'loc', 'mi', 
                                'mi_rank', 'multi', 'num_classes', 'num_functions', 'num_methods', 'single_comments',
                                'sloc', 'time', "run_number"]

        repo_metrics_cols = ["trainee_id", 'additions', 'avg_lines_per_class', 'avg_lines_per_function', 'avg_lines_per_method', 
                            'cc', 'difficulty', 'effort', 'lloc', 'loc', 'mi', 'num_classes', 'num_functions', 
                            'num_methods', 'sloc', 'time']
        
        repo_meta_df_cols = ["repo_name","trainee_id",'branches', 'contributors', 'description', 'forks', 'html_url', 'languages', 'total_commits', 
                        "interested_files", "num_ipynb", "num_js", "num_py", "num_dirs", "num_files", "commit_stamp", "run_number"]
            
        commit_history_df_cols = ["commit_history", "contribution_counts", "commits_on_branch", "commits_on_default_to_branch", "num_contributors", "branch", "default_branch", "repo_name", "html_link", "trainee_id", "file_level", "run_number"]

        
        
        # set default values

        repo_df_cols_default = {"html_url": ""}

        user_df_cols_default = {"trainee_id":"",'avatar_url':"", 'bio':"", 'commits':-999, 'email':"", 'followers':-999, 'following':-999, 'html_url':"", 
                        'issues':-999, 'name':"", 'public_repos':-999, 'pull_requests':-999, "run_number":-999}

        
        repo_meta_df_cols_default = {"repo_name":"","trainee_id":"",'branches':-999, 'contributors':[], 'description':"", 'forks':-999, 'html_url':"", 'languages':[], 'total_commits':-999, 
                        "interested_files":[], "num_ipynb":-999, "num_js":-999, "num_py":-999, "num_dirs":-999, "num_files":-999, "commit_stamp":[], "run_number":-999}


        repo_analysis_df_cols_default = {"trainee_id":"",'additions':-999, 'avg_lines_per_class':-999.0, 'avg_lines_per_function':-999.0, 'avg_lines_per_method':-999.0,
                                'blank':-999, 'cc':-999.0, 'cc_rank':"", 'comments':-999, 'difficulty':-999.0, 'effort':-999.0, 'lloc':-999, 'loc':-999, 'mi':-999.0, 
                                'mi_rank':"", 'multi':-999, 'num_classes':-999, 'num_functions':-999, 'num_methods':-999, 'single_comments':-999,
                                'sloc':-999, 'time':-999.0, "run_number":-999}
        
        commit_history_df_cols_default = {"commit_history":[], "contribution_counts":[], "commits_on_branch":-999, "commits_on_default_to_branch":-999, "num_contributors":-999, "branch":"", "default_branch":"", "repo_name":"", "html_link":"", "trainee_id":"", "file_level":[], "run_number":-999}
        



        trainee_id_list = list(github_df["trainee_id"].values)


        # get the github analysis dict
        
        print("Retrieving data from API...\n")
        
        #github_analysis_dict = get_github_analysis_dict(github_df, github_token)


        # retrive user and repo data
        counter = 0
        repo_table_error_dict = {"trainee_id":[], "user":[], "repo_name":[], "branch":[], "error":[]}
        assignment_table_error_dict = {"trainee_id":[], "user":[], "repo_name":[], "branch":[], "error":[]}
        user_error_dict = {"trainee_id":[], "user":[], "repo_name":[], "branch":[], "error":[]}
        repo_meta_error_dict = {"trainee_id":[], "user":[], "repo_name":[], "branch":[], "error":[]}
        commit_history_error_dict = {"trainee_id":[], "user":[], "repo_name":[], "branch":[], "error":[]}
        repo_metric_error_dict = {"trainee_id":[], "user":[], "repo_name":[], "branch":[], "error":[]}
        entry_made_into_analysis_table = False

        trainee_repo_id_dict = {}


        for i, row in github_df.iterrows():
            counter += 1
            user = row["gh_username"]
            repo_name = row["repo_name"]
            trainee_id = row["trainee_id"]
            run_number = row["run_number"]
            branch = row["branch_name"]
            trainee = row["trainee"]
            assignments_ids = row["assignments_ids"]

            print("\n\n\nRetrieving data for user: {} and repo: {}...".format(user, repo_name))
            print("\n")
            hld = dict()
            if counter != 0 and counter%5 == 0:
                print(user)
                print("Sleeping for 20 seconds\n")
                time.sleep(20)
                print("Resumed...\n")

            # get repo meta data and analysis data
            repo_meta_repo_pyanalysis = get_repo_meta_pyanalysis(user, github_token, repo_name, branch)

            hld["repo_meta"] = repo_meta_repo_pyanalysis["repo_meta"]

            hld["repo_anlysis_metrics"] = repo_meta_repo_pyanalysis["repo_anlysis_metrics"]

            hld["commit_history"] = repo_meta_repo_pyanalysis["commit_history"]


            """if len(trainee_df[trainee_df["trainee_id"]==trainee_id]) == 0:
                print("User: {} not found in trainee_df\n".format(user))
                continue

            trainee = int(trainee_df[trainee_df["trainee_id"]==trainee_id].trainee.values[0])"""

            # get user data from github api
            hld["user"] = get_user(user, github_token, api=False)

            _dict = dict()
            _dict[trainee_id] =  hld
            
            counter += 1

            ##############################################################################################

            #Repo meta and repo table population

            ###############################################################################################
            # get the repo meta data dict
            if "error" not in hld["repo_meta"]:
                print("creating repo_table data dict...\n")

                repo_table_dict = {col:(_dict[trainee_id]["repo_meta"][col]
                    if col in _dict[trainee_id]["repo_meta"].keys() else None)  for col in repo_df_cols}

                repo_table_dict["week"] = week

                #fill in the default values where necessary
                """repo_table_dict = {col:(repo_dict[col]
                    if col in _dict[trainee_id]["repo_meta"].keys() and repo_dict[col] != None
                    else repo_df_cols_default[col])  for col in repo_df_cols}"""


                print("Repo table data dict created...\n")

                #check if the entry already exists in the repo table
                pluralapi = "repos"
                q_url = "https://dev-cms.10academy.org/api/{}?filters[html_url][$eq]={}".format(pluralapi, repo_table_dict["html_url"])

                r = get_table_data_strapi(q_url, token=strapi_token)

                #if the entry already exist retrieve the id

                if len(r) > 0:
                    repo_id = r[0]["id"]
                    print("Repo already exists in repo table...\n")
                else:
                    print("Repo does not exist in repo table...\n")
                    #create a new entry in the repo table
                    print("Creating new entry in repo table...\n")

                    r = insert_data_strapi(data=repo_table_dict, token=strapi_token, pluralapi=pluralapi)
                    
                    if "error" in r:
                        print("Error creating entry in repo table...\n")
                        
                        repo_table_error_dict["trainee_id"].append(trainee_id)
                        repo_table_error_dict["user"].append(user)
                        repo_table_error_dict["repo_name"].append(repo_name)
                        repo_table_error_dict["branch"].append(branch)
                        repo_table_error_dict["error"].append(r["error"])
                        continue
                   
                    else:
                        repo_id = r["id"]
                        print("New entry created in repo table...\n")

                        #update assignment table with the new repo id
                        print("Updating assignment table with new repo id...\n")
                        pluralapi = "assignments"
                        data = {"repo":repo_id}

                        for a_id in assignments_ids:
                            r = update_data_strapi(data=data, token=strapi_token, pluralapi=pluralapi, entry_id=a_id)

                            if "error" in r:
                                print("Error updating assignment table...\n")

                                assignment_table_error_dict["trainee_id"].append(trainee_id)
                                assignment_table_error_dict["user"].append(user)
                                assignment_table_error_dict["repo_name"].append(repo_name)
                                assignment_table_error_dict["branch"].append(branch)
                                assignment_table_error_dict["error"].append(r["error"])
                                
                                continue
                            else:
                                print("Assignment table updated...\n")

                        
                        # insert trainee_id and repo_id into trainee_repo_id dict
                        trainee_repo_id_dict[trainee_id] = repo_id
                                






                ###############################################################################################
                #get repo meta dict
                


                print("Repo meta data dict created\n")

                # check for entry in strapi
                pluralapi = "github-repo-metas"
                week = week
                q_url = "https://dev-cms.10academy.org/api/{}?filters[trainee][id][$eq]={}".format(pluralapi, trainee)

                r = get_table_data_strapi(q_url, token=strapi_token)

                """try:
                    r = requests.get(
                                    q_url,
                                    headers = headers
                                    ).json()
                except Exception as e:
                    print("Error in getting repo meta data from strapi: {}\n".format(e))
                    repo_meta_error_dict["trainee_id"].append(trainee_id)
                    repo_meta_error_dict["user"].append(user)
                    repo_meta_error_dict["repo_name"].append(repo_name)
                    repo_meta_error_dict["error"].append(e)
                    continue"""
                

                # check if entry exists
                r_filtered = [r_i for r_i in r if r_i["attributes"]["trainee_id"] == trainee_id and r_i["attributes"]["run_number"] == run_number and r_i["attributes"]["week"]== week]
                if len(r_filtered) == 0:
                    print("Creating repo meta data dict...\n")
                    print("Entry does not exist in strapi...\n")
                    print("Creating entry in strapi...\n\n")

                    repo_meta_dict = {col:(_dict[trainee_id]["repo_meta"][col]
                        if col in _dict[trainee_id]["repo_meta"].keys() else None)  for col in repo_meta_df_cols}


                    if starter_code_ref_basevalues:
                        # normalize the repo data
                        print("Normalizing repo_meta data...\n")
                        repo_dict = normalize_repo_data(repo_meta_dict, starter_code_ref_basevalues)

                    #fill in the default values where necessary
                    repo_meta_dict = {col:(repo_meta_dict[col]
                        if col in _dict[trainee_id]["repo_meta"].keys() and repo_meta_dict[col] != None
                        else repo_meta_df_cols_default[col])  for col in repo_meta_df_cols}


                    repo_meta_dict["trainee_id"] = trainee_id
                    repo_meta_dict["trainee"] = trainee
                    repo_meta_dict["run_number"] = run_number
                    repo_meta_dict["repo"] = repo_id
                    repo_meta_dict["week"] = week

                    _r = insert_data_strapi(data=repo_meta_dict, pluralapi=pluralapi, token=strapi_token)

                    if "error" in _r:
                        print("Error creating entry in repo meta table...\n")
                        repo_meta_error_dict["trainee_id"].append(trainee_id)
                        repo_meta_error_dict["user"].append(user)
                        repo_meta_error_dict["repo_name"].append(repo_name)
                        repo_meta_error_dict["branch"].append(branch)
                        repo_meta_error_dict["error"].append(_r["error"])
                        
                
                else:
                    print("Error creating entry in repo meta table...\n")
                    print("Entry already exists in strapi...\n")
                    repo_meta_error_dict["trainee_id"].append(trainee_id)
                    repo_meta_error_dict["user"].append(user)
                    repo_meta_error_dict["repo_name"].append(repo_name)
                    repo_meta_error_dict["branch"].append(branch)
                    repo_meta_error_dict["error"].append("Repo meta already exists in repo meta table")
                    

            else:
                print("Error retrieving repo data for user: {} and repo: {}\n".format(user, repo_name))
                repo_meta_error_dict["trainee_id"].append(trainee_id)
                repo_meta_error_dict["repo_name"].append(repo_name)
                repo_meta_error_dict["user"].append(user)
                repo_meta_error_dict["branch"].append(branch)
                repo_meta_error_dict["error"].append(hld["repo_meta"])
            

            ############################################################################################### 

            #get user meta data dict

            ###############################################################################################
            print("Data for user: {} and repo: {} retrieved\n".format(user, repo_name))

            if "error" not in hld["user"]:
                # get the user data dict
                user_dict = hld["user"]

                # check for entry in strapi
                pluralapi = "github-user-metas"
                q_url = "https://dev-cms.10academy.org/api/{}?filters[trainee][id][$eq]={}".format(pluralapi, trainee)

                r = get_table_data_strapi(q_url, token=strapi_token)

                """try:
                    r = requests.get(
                                    q_url,
                                    headers = headers
                                    ).json()
                except Exception as e:
                    print("Error in getting user meta data from strapi: {}\n".format(e))
                    user_meta_error_dict["trainee_id"].append(trainee_id)
                    user_meta_error_dict["user"].append(user)
                    user_meta_error_dict["repo_name"].append(repo_name)
                    user_meta_error_dict["error"].append(e)
                    continue"""

                # check if entry exists
                r_filtered = [r_i for r_i in r if r_i["attributes"]["trainee_id"] == trainee_id and r_i["attributes"]["run_number"] == run_number and r_i["attributes"]["week"]== week]
                if len(r_filtered) == 0:
                    print("Creating user meta data dict...\n")
                    print("Entry does not exist in strapi...\n")
                    print("Creating entry in strapi...\n\n")

                    user_dict = {col:(_dict[trainee_id]["user"][col]
                        if col in _dict[trainee_id]["user"].keys() else None)  for col in user_df_cols}

                    #fill in the default values where necessary
                    user_dict = {col:(user_dict[col]
                        if col in _dict[trainee_id]["user"].keys() and user_dict[col] != None
                        else user_df_cols_default[col])  for col in user_df_cols}


                    user_dict["trainee_id"] = trainee_id
                    user_dict["trainee"] = trainee
                    user_dict["run_number"] = run_number
                    user_dict["week"] = week
                    user_dict["repo"] = repo_id
                    
                    _r = insert_data_strapi(data=user_dict, pluralapi=pluralapi, token=strapi_token)
                    
                    if "error" in _r:
                        print("Error creating entry in user meta table...\n")
                        user_error_dict["trainee_id"].append(trainee_id)
                        user_error_dict["user"].append(user)
                        user_error_dict["repo_name"].append(repo_name)
                        user_error_dict["branch"].append(branch)
                        user_error_dict["error"].append(_r["error"])
                      

                else:
                    print("Error creating entry in user meta table...\n")
                    print("Entry already exists in user meta table...\n")
                    user_error_dict["trainee_id"].append(trainee_id)
                    user_error_dict["user"].append(user)
                    user_error_dict["repo_name"].append(repo_name)
                    user_error_dict["branch"].append(branch)
                    user_error_dict["error"].append("User meta already exists in user meta table")
                    

            else:
                print("Error retrieving user data for user: {} and repo: {}\n".format(user, repo_name))
                user_error_dict["trainee_id"].append(trainee_id)
                user_error_dict["user"].append(user)
                user_error_dict["repo_name"].append(repo_name)
                user_error_dict["branch"].append(branch)
                user_error_dict["error"].append(hld["user"])


            ###############################################################################################
                
            #get repo commmit history dict

            ###############################################################################################
            
            if "error" not in hld["commit_history"]:
                # get the repo commit history dict
                repo_commit_history_dict = hld["commit_history"]

                # check for entry in strapi
                pluralapi = "github-branch-commit-histories"
                q_url = "https://dev-cms.10academy.org/api/{}?filters[trainee][id][$eq]={}".format(pluralapi, trainee)

                r = get_table_data_strapi(q_url, token=strapi_token)

                """try:
                    r = requests.get(
                                    q_url,
                                    headers = headers
                                    ).json()
                except Exception as e:
                    print("Error in getting repo commit history data from strapi: {}\n".format(e)) 
                    repo_commit_history_error_dict["trainee_id"].append(trainee_id)
                    repo_commit_history_error_dict["user"].append(user)
                    repo_commit_history_error_dict["repo_name"].append(repo_name)
                    repo_commit_history_error_dict["error"].append(e)
                    continue"""

                # check if entry exists
                r_filtered = [r_i for r_i in r if r_i["attributes"]["trainee_id"] == trainee_id and r_i["attributes"]["run_number"] == run_number and r_i["attributes"]["week"]== week]
                if len(r_filtered) == 0:
                    print("Creating repo commit history dict...\n")
                    print("Entry does not exist in strapi...\n")
                    print("Creating entry in strapi...\n\n")

                    commit_history_dict = {col:(_dict[trainee_id]["commit_history"][col]
                        if col in _dict[trainee_id]["commit_history"].keys() else None)  for col in commit_history_df_cols}

                    #fill in the default values where necessary
                    commit_history_dict = {col:(commit_history_dict[col]
                        if col in _dict[trainee_id]["commit_history"].keys() and commit_history_dict[col] != None
                        else commit_history_df_cols_default[col])  for col in commit_history_df_cols}

                    commit_history_dict["trainee_id"] = trainee_id
                    commit_history_dict["trainee"] = trainee
                    commit_history_dict["run_number"] = run_number
                    commit_history_dict["week"] = week
                    commit_history_dict["repo"] = repo_id

                    _r = insert_data_strapi(data=commit_history_dict, pluralapi=pluralapi, token=strapi_token)

                    if "error" in _r:
                        print("Error creating entry in repo commit history table...\n")
                        commit_history_error_dict["trainee_id"].append(trainee_id)
                        commit_history_error_dict["user"].append(user)
                        commit_history_error_dict["repo_name"].append(repo_name)
                        commit_history_error_dict["branch"].append(branch)
                        commit_history_error_dict["error"].append(_r["error"])
                        

                else:
                    print("Error creating entry in repo commit history table...\n")
                    print("Entry already exists in repo commit history table...\n")
                    commit_history_error_dict["trainee_id"].append(trainee_id)
                    commit_history_error_dict["user"].append(user)
                    commit_history_error_dict["repo_name"].append(repo_name)
                    commit_history_error_dict["branch"].append(branch)
                    commit_history_error_dict["error"].append("Repo commit history already exists in repo commit history table")
                    

            else:
                print("Error retrieving repo commit history data for user: {} and repo: {}\n".format(user, repo_name))
                commit_history_error_dict["trainee_id"].append(trainee_id)
                commit_history_error_dict["user"].append(user)
                commit_history_error_dict["repo_name"].append(repo_name)
                commit_history_error_dict["branch"].append(branch)
                commit_history_error_dict["error"].append(hld["commit_history"])

        

            ###############################################################################################

            #get repo analysis metrics dict

            ###############################################################################################

            if "error" not in hld["repo_anlysis_metrics"]:
                # get the repo analysis metrics dict
                repo_analysis_metrics_dict = hld["repo_anlysis_metrics"]

                # check for entry in strapi
                pluralapi = "github-repo-metrics"
                q_url = "https://dev-cms.10academy.org/api/{}?filters[trainee][id][$eq]={}".format(pluralapi, trainee)

                r = get_table_data_strapi(q_url, token=strapi_token)

                """try:
                    r = requests.get(
                                    q_url,
                                    headers = headers
                                    ).json()
                except Exception as e:
                    print("Error in getting repo analysis metrics data from strapi: {}\n".format(e))
                    repo_analysis_metrics_error_dict["trainee_id"].append(trainee_id)
                    repo_analysis_metrics_error_dict["user"].append(user)
                    repo_analysis_metrics_error_dict["repo_name"].append(repo_name)
                    repo_analysis_metrics_error_dict["error"].append(e)
                    continue"""

                # check if entry exists
                r_filtered = [r_i for r_i in r if r_i["attributes"]["trainee_id"] == trainee_id and r_i["attributes"]["run_number"] == run_number and r_i["attributes"]["week"]== week]
                if len(r_filtered) == 0:
                    print("Creating repo analysis metrics dict...\n")
                    print("Entry does not exist in strapi...\n")
                    print("Creating entry in strapi...\n\n")

                    analysis_metrics_dict = {col:(_dict[trainee_id]["repo_anlysis_metrics"][col]
                        if col in _dict[trainee_id]["repo_anlysis_metrics"].keys() else None)  for col in repo_analysis_df_cols}

                    #fill in the default values where necessary
                    analysis_metrics_dict = {col:(analysis_metrics_dict[col]
                        if col in _dict[trainee_id]["repo_anlysis_metrics"].keys() and analysis_metrics_dict[col] != None
                        else repo_analysis_df_cols_default[col])  for col in repo_analysis_df_cols}

                    analysis_metrics_dict["trainee_id"] = trainee_id
                    analysis_metrics_dict["trainee"] = trainee
                    analysis_metrics_dict["run_number"] = run_number
                    analysis_metrics_dict["week"] = week
                    analysis_metrics_dict["repo"] = repo_id

                    _r = insert_data_strapi(data=analysis_metrics_dict, pluralapi=pluralapi, token=strapi_token)
                    entry_made_into_analysis_table = True

                    if "error" in _r:
                        print("Error creating entry in repo analysis metrics table...\n")
                        repo_metric_error_dict["trainee_id"].append(trainee_id)
                        repo_metric_error_dict["user"].append(user)
                        repo_metric_error_dict["repo_name"].append(repo_name)
                        repo_metric_error_dict["branch"].append(branch)
                        repo_metric_error_dict["error"].append(_r["error"])

                else:
                    print("Error creating entry in repo analysis metrics table...\n")
                    print("Entry already exists in repo analysis metrics table...\n")
                    repo_metric_error_dict["trainee_id"].append(trainee_id)
                    repo_metric_error_dict["user"].append(user)
                    repo_metric_error_dict["repo_name"].append(repo_name)
                    repo_metric_error_dict["branch"].append(branch)
                    repo_metric_error_dict["error"].append("Repo analysis metrics already exists in repo analysis metrics table")

            else:
                print("Error retrieving repo analysis metrics data for user: {} and repo: {}\n".format(user, repo_name))
                repo_metric_error_dict["trainee_id"].append(trainee_id)
                repo_metric_error_dict["user"].append(user)
                repo_metric_error_dict["repo_name"].append(repo_name)
                repo_metric_error_dict["branch"].append(branch)
                repo_metric_error_dict["error"].append(hld["repo_anlysis_metrics"])

            






        ###############################################################################################

        #save error dicts to csv files

        ###############################################################################################
        
        now = datetime.now()
        output_dir = "data/run_errors" + now.strftime("%Y-%m-%d_%H-%M-%S")

        
        
        # Save users with Github User analysis error
        if len(user_error_dict["user"]) > 0:

            print("Saving trainees with Github User analysis error\n")
            user_error_df = pd.DataFrame(user_error_dict)

            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

            
            user_error_df.to_csv("{}/b{}_{}_trainees_with_github_user_analysis_error_{}.csv".format(output_dir, batch, week, now.strftime("%Y_%m_%d__%H_%M_%S")), index=False)

        
        
        # Save users with Github Repo analysis error
        if len(repo_meta_error_dict["user"]) > 0:

            print("Saving trainees with Github Repo meta analysis error\n")
            repo_meta_error_df = pd.DataFrame(repo_meta_error_dict)

            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

            now = datetime.now()
            repo_meta_error_df.to_csv("{}/b{}_{}_trainees_with_github_repo_meta_analysis_error_{}.csv".format(output_dir, batch, week, now.strftime("%Y_%m_%d__%H_%M_%S")), index=False)



        # Save users with commit history error
        if len(commit_history_error_dict["user"]) > 0:
                
                print("Saving trainees with commit history error\n")
                commit_history_error_df = pd.DataFrame(commit_history_error_dict)

                if not os.path.isdir(output_dir):
                    os.makedirs(output_dir)

                now = datetime.now()
                commit_history_error_df.to_csv("{}/b{}_{}_trainees_with_commit_history_error_{}.csv".format(output_dir, batch, week, now.strftime("%Y_%m_%d__%H_%M_%S")), index=False)
        
       
        # Save users with Github Repo analysis error
        if len(repo_metric_error_dict["user"]) > 0:

            print("Saving trainees with Github Repo analysis error\n")
            repo_metric_error_df = pd.DataFrame(repo_metric_error_dict)

            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

            now = datetime.now()
            repo_metric_error_df.to_csv("{}/b{}_{}_trainees_with_github_repo_analysis_error_{}.csv".format(output_dir, batch, week, now.strftime("%Y_%m_%d__%H_%M_%S")), index=False)
            
        
        
        
        
        if len(user_error_dict["user"]) == 0 and len(repo_meta_error_dict["user"]) == 0 and len(repo_metric_error_dict["user"]) == 0 and len(commit_history_error_dict["user"]) == 0:
            print("No errors found\n\n")  






    
        ########################################################################################################################

        #metric summary computation

        ########################################################################################################################

        if entry_made_into_analysis_table:
            print("Entry made into analysis table\n\n")
                
            # Compute the Analysis Metrics Summary
            print("Computing Analysis Metrics Summary...\n")

            # get the analysis metrics summary
            pluralapi = "github-repo-metrics"
            q_url = "https://dev-cms.10academy.org/api/{}?filters[week][$eq]={}&filters[run_number][$eq]={}".format(pluralapi, week, run_number)
            
            r = get_table_data_strapi(q_url, token=strapi_token)
            
            try:
                """r = requests.get(
                            q_url,
                            headers = headers
                            ).json()"""
                            
                if "error" not in r[0]:
                    r_data = r
                    df_dict = {col:[] for col in repo_metrics_cols}

                    for col in repo_metrics_cols:
                        for entry in r_data:
                            if entry["attributes"]["trainee_id"] in trainee_id_list:
                                # ignore place holders for null values
                                if (isinstance(entry["attributes"][col],float) and entry["attributes"][col] != -999.0) or (isinstance(entry["attributes"][col],int) and entry["attributes"][col] != -999) or (isinstance(entry["attributes"][col],str)):
                                    df_dict[col].append(entry["attributes"][col])
                                else:
                                    df_dict[col].append(None)

                    cat_df = pd.DataFrame(df_dict)

                    cat_dict = {col:{"max":None, "min":None, "sum":None, "break_points":None} for col in metrics_list}

                    for col in metrics_list:
                        
                        rev = False
                        series = cat_df[col]
                        if col == "cc":
                            rev = True
                            
                            # remove zero values for cyclomatic complexity analysis
                            series = cat_df[col][cat_df[col] != 0]
                        
                        if col in sum_list:
                            cat_dict[col]["break_points"], cat_dict[col]["min"], cat_dict[col]["max"], cat_dict[col]["sum"] = get_break_points(series = series, cat_list=[0.99, 0.9, 0.75, 0.5], reverse=rev, _add=True)

                        else:
                            cat_dict[col]["break_points"], cat_dict[col]["min"], cat_dict[col]["max"] = get_break_points(series = series, cat_list=[0.99, 0.9, 0.75, 0.5], reverse=rev, _add=False)
                        
                        """_min = cat_df[[col]].min().to_list()[0]
                        _max = cat_df[[col]].max().to_list()[0]
                        cat_dict[col]["max"] = _max
                        cat_dict[col]["min"] = _min
                        cat_dict[col]["break_points"] = get_break_points(_min, _max)
                       
                        # compute sum for eligible columns
                        if col in sum_list:
                            cat_dict[col]["sum"] = cat_df[[col]].sum().to_list()[0]"""


                    # create rannk dict
                    rank_dict = {col:[] for col in repo_metrics_cols}

                    cat_df.fillna(-999, inplace=True)
                    

                    for i,row in cat_df.iterrows():
                        for col in repo_metrics_cols:
                            if col == "trainee_id":
                                rank_dict[col].append(row[col])

                                if "repo" not in rank_dict:
                                    rank_dict["repo"] = []
                                    
                                if row[col] not in trainee_repo_id_dict:

                                    pluralapi = "github-repo-metas"
                                    q_url = "https://dev-cms.10academy.org/api/{}?filters[trainee_id][$eq]={}&filters[week][$eq]={}&filters[run_number][$eq]={}".format(pluralapi, row[col], week, run_number)
                                    r = get_table_data_strapi(q_url, token=strapi_token)

                                    if "error" not in r[0]:
                                        repo_lnk = r[0]["attributes"]["html_url"]
                                        # retrieve repo_id from strapi
                                        pluralapi = "repos"

                                        q_url = "https://dev-cms.10academy.org/api/{}?filters[html_url][$eq]={}".format(pluralapi, repo_lnk)
                                        r = get_table_data_strapi(q_url, token=strapi_token)

                                        
                                        if "error" not in r[0]:
                                            
                                            trainee_repo_id_dict[row[col]] = r[0]["id"]
                                            
                                        else:
                                            trainee_repo_id_dict[row[col]] = None
                                            print("Error in retrieving repo realtion from repo table for for trainee {}".format(row[col]))
                                            print("\n")
                                    
                                    else:
                                        trainee_repo_id_dict[row[col]] = None
                                        print("Error in retrieving repo link from repo metas table for trainee {}".format(row[col]))

                                
                                repo_rel = trainee_repo_id_dict[row[col]]
                                rank_dict["repo"].append(repo_rel)
                            
                            else:
                                val = row[col]
                                if val != None:
                                    break_points = cat_dict[col]["break_points"]
                                    if col != "cc":
                                        rank_dict[col].append(get_metric_category(val=val, break_points=break_points, reverse=False))
                                    else:
                                        rank_dict[col].append(get_metric_category(val=val, break_points=break_points, reverse=True))
                                else:
                                    rank_dict[col].append(get_metric_category(val=-999, break_points=break_points, reverse=False))

                    # create rank df
                    rank_df = pd.DataFrame(rank_dict)
                    rank_df["week"] = week
                    rank_df["run_number"] = run_number
                    rank_df = rank_df.merge(github_df[["trainee_id","trainee"]], on="trainee_id")

                    rank_data = json.loads(rank_df.to_json(orient="records"))

                    # load data into strapi
                    pluralapi = "github-repo-metric-ranks"

                    for r in rank_data:
                        print("Loading data into strapi...\n")
                        # check if entry exists
                        print("Checking if entry exists...\n")
                        q_url = "https://dev-cms.10academy.org/api/{}?filters[week][$eq]={}&filters[trainee_id][$eq]={}&filters[run_number][$eq]={}".format(pluralapi, week, r["trainee_id"], run_number)
                        
                        r_list = get_table_data_strapi(q_url, token=strapi_token)
                        
                        """try:
                            r_list = requests.get(
                                            q_url,
                                            headers = headers
                                            ).json()
                        
                        except Exception as e:
                            print("Error: Retrieving data from {} for trainee_id {} and week {}\n".format(pluralapi, r["trainee_id"], week))
                            continue"""


                        if len(r_list) > 0: 
                            if "error" not in r_list[0]:
                                print("Entry already exists for user: {} for week: {}\n".format(r["trainee_id"], week))
                                print("Updating entry...\n")

                                # update entry
                                r = update_data_strapi(data=r, pluralapi=pluralapi, token=strapi_token, entry_id=r_list[0]["id"])
                                print("Entry updated.\n")


                            else:
                                print("Error checking if entry exists for user: {} for week: {}\n".format(r["trainee_id"], week))
                                print(r_list[0])
                                print("\n")
                        else:
                            # create entry in strapi
                            print("Entry does not exist for user: {}, week: {} and run_number: {}\n".format(r["trainee_id"], week, run_number))
                            print("Creating entry in strapi...\n")
                            r = insert_data_strapi(data=r, pluralapi=pluralapi, token=strapi_token)

                            
                    
                    ########################################################################################################################
                    
                    # get summary metrics dict

                    ########################################################################################################################
                    cat_dict = get_metric_summary_dict(cat_dict)

                    # create summary metrics df
                    cat_df = pd.DataFrame(cat_dict)
                    cat_df["week"] = week
                    cat_df["batch"] = batch
                    cat_df["run_number"] = run_number

                    # create summary metrics data
                    cat_data = json.loads(cat_df.to_json(orient="records"))

                    # load data into strapi
                    pluralapi = "github-metrics-summaries"
                    
                    for r in cat_data:
                        print("Loading data into strapi...\n")
                        # check if entry exists
                        print("Checking if entry exists...\n")
                        q_url = "https://dev-cms.10academy.org/api/{}?filters[week][$eq]={}&filters[metrics][$eq]={}&filters[batch][$eq]={}&filters[run_number][$eq]={}".format(pluralapi, week, r["metrics"], r["batch"], run_number)
                        

                        r_list = get_table_data_strapi(q_url, token=strapi_token)
                        
                        """try:
                            r_list = requests.get(
                                        q_url,
                                        headers = headers
                                        ).json()
                        except Exception as e:
                            print("Error: Retrieving data from {} for metrics {} and week {}\n".format(pluralapi, r["metrics"], week))
                            continue"""

                        if len(r_list) > 0:
                            if "error" not in r_list[0]:
                                print("Entry already exists for batch {} metrics:{} for week: {} and run_number {}\n".format(r["batch"], r["metrics"], week, run_number))

                                # update entry in strapi
                                print("Updating entry in strapi...\n")


                                r = update_data_strapi(data=r, pluralapi=pluralapi, token=strapi_token, entry_id=r_list[0]["id"])
            
                            else:
                                print("Error checking if entry exists for batch {} metrics:{} for week: {} and run_number {}\n".format(r["batch"], r["metrics"], week, run_number))
                                print(r_list[0])
                                print("\n")
                        else:
                            # create entry in strapi
                            print("Entry does not exist for week: {}\n".format(week))
                            print("Creating entry in strapi...\n")
                            r = insert_data_strapi(data=r, pluralapi=pluralapi, token=strapi_token)


                else:
                    print("Error getting data from strapi...\n")
                    print(r[0])
                    print("\n")


            except Exception as e:
                print("Error retrieving analysis metrics summary for week: {}, batch {}, and run_number {}\n".format(week, batch, run_number))
                print(repr(e))


        else:  
            print("No entry made into analysis table. Hence no entries to be made into metric rank and metric summary tables\n\n")
        
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


    