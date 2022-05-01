from datetime import datetime
import time
import json
import os
import sys
import pandas as pd
import requests
from app import get_user, single_repos_meta_single_repos_pyanalysis


curdir = os.path.dirname(os.path.realpath(__file__))
cpath = os.path.dirname(curdir)
if not cpath in sys.path:
    sys.path.append(cpath)



from modules.strapi_methods import get_table_data_strapi, insert_data_strapi, update_data_strapi, upload_to_strapi    
from modules.Category_Dict import Metrics_Summary_Dict
from modules.analyzer_utils import get_break_points, get_df, get_df_dict, get_github_analysis_dict, get_id_userid_df, get_metric_category, get_metric_summary_dict, get_rank_dict, get_repo_df_dict, get_repo_meta_pyanalysis, get_repo_names, normalize_repo_data

if os.path.exists(".env/secret.json"):
    with open(".env/secret.json", "r") as s:
        secret = json.load(s)
        try:
            github_token = secret["github_token"]
        except:
            github_token = None
else:
    github_token = None


if github_token:
    trainee_url = "https://dev-cms.10academy.org/api/{}"
    trainee_plural_api = "trainees"
    trainee_dict = get_table_data_strapi(trainee_url.format(trainee_plural_api))

    # check if trainee_dict was returned
    if "error" not in trainee_dict:
        trainee_df = get_id_userid_df(trainee_dict)



        # read in the data
        #dt_user = pd.read_csv("data/github_usernames.csv")
        #dt_repo = pd.read_csv("data/github_repos_wk1.csv")
        #github_df = dt_user.merge(dt_repo, on="trainee_id")
        
        github_df = pd.read_csv("data/try.csv")

        starter_code_url = "https://github.com/10xac/Twitter-Data-Analysis"




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
        metrics_list = ["additions","avg_lines_per_class","avg_lines_per_function","avg_lines_per_method",
                        "cc","difficulty",'effort','lloc','loc','mi','num_classes','num_functions','num_methods',
                        'sloc','time']
        
        sum_list =  ["additions","difficulty",'effort','lloc','loc','num_classes','num_functions','num_methods',
                     'sloc','time']

        user_df_cols = ["trainee_id",'avatar_url', 'bio', 'commits', 'email', 'followers', 'following', 'html_url', 
                        'issues', 'name', 'public_repos', 'pull_requests']

        user_df_cols_default = {"trainee_id":"",'avatar_url':"", 'bio':"", 'commits':-999, 'email':"", 'followers':-999, 'following':-999, 'html_url':"", 
                        'issues':-999, 'name':"", 'public_repos':-999, 'pull_requests':-999}

        repo_df_cols = ["repo_name","trainee_id",'branches', 'contributors', 'description', 'forks', 'html_url', 'languages', 'total_commits', 
                        "interested_files", "num_ipynb", "num_js", "num_py", "num_dirs", "num_files"]


        repo_df_cols_default = {"repo_name":"","trainee_id":"",'branches':-999, 'contributors':[], 'description':"", 'forks':-999, 'html_url':"", 'languages':[], 'total_commits':-999, 
                        "interested_files":[], "num_ipynb":-999, "num_js":-999, "num_py":-999, "num_dirs":-999, "num_files":-999}


        repo_analysis_df_cols = ["trainee_id",'additions', 'avg_lines_per_class', 'avg_lines_per_function', 'avg_lines_per_method',
                                'blank', 'cc', 'cc_rank', 'comments', 'difficulty', 'effort', 'lloc', 'loc', 'mi', 
                                'mi_rank', 'multi', 'num_classes', 'num_functions', 'num_methods', 'single_comments',
                                'sloc', 'time']

        repo_analysis_df_cols_default = {"trainee_id":"",'additions':-999, 'avg_lines_per_class':-999.0, 'avg_lines_per_function':-999.0, 'avg_lines_per_method':-999.0,
                                'blank':-999, 'cc':-999.0, 'cc_rank':"", 'comments':-999, 'difficulty':-999.0, 'effort':-999.0, 'lloc':-999, 'loc':-999, 'mi':-999.0, 
                                'mi_rank':"", 'multi':-999, 'num_classes':-999, 'num_functions':-999, 'num_methods':-999, 'single_comments':-999,
                                'sloc':-999, 'time':-999.0}
        

        repo_metrics_cols = ["trainee_id", 'additions', 'avg_lines_per_class', 'avg_lines_per_function', 'avg_lines_per_method', 
                            'cc', 'difficulty', 'effort', 'lloc', 'loc', 'mi', 'num_classes', 'num_functions', 
                            'num_methods', 'sloc', 'time']


        trainee_id_list = list(github_df["trainee_id"].values)


        # get the github analysis dict
        
        print("Retrieving data from API...\n")
        
        #github_analysis_dict = get_github_analysis_dict(github_df, github_token)


        # retrive user and repo data
        counter = 0
        user_error_dict = {"trainee_id":[], "user":[], "repo_name":[], "error":[]}
        repo_meta_error_dict = {"trainee_id":[], "user":[], "repo_name":[], "error":[]}
        repo_metric_error_dict = {"trainee_id":[], "user":[], "repo_name":[], "error":[]}
        entry_made_into_analysis_table = False

        week="week0"
        batch = 5

        for _, trainee_id, user, repo_name in github_df.itertuples():
            print("Retrieving data for user: {} and repo: {}...".format(user, repo_name))
            hld = dict()
            if counter != 0 and counter%5 == 0:
                print(user)
                print("Sleeping for 60 seconds\n")
                time.sleep(60)
                print("Resumed...\n")

            # get repo meta data and analysis data
            repo_meta_repo_pyanalysis = get_repo_meta_pyanalysis(user, github_token, repo_name)

            hld["repo_meta"] = repo_meta_repo_pyanalysis["repo_meta"]

            hld["repo_anlysis_metrics"] = repo_meta_repo_pyanalysis["repo_anlysis_metrics"]


            if len(trainee_df[trainee_df["trainee_id"]==trainee_id]) == 0:
                print("User: {} not found in trainee_df\n".format(user))
                continue

            trainee = int(trainee_df[trainee_df["trainee_id"]==trainee_id].trainee.values[0])

            # get user data from github api
            hld["user"] = get_user(user, github_token, api=False)

            _dict = dict()
            _dict[trainee_id] =  hld
            
            counter += 1
            


            ###############################################################################################
            print("Data for user: {} and repo: {} retrieved\n".format(user, repo_name))

            if "error" not in hld["user"]:
                # get the user data dict
                print("Creating user data dict...\n")
                user_dict = {col:(_dict[trainee_id]["user"][col]
                    if col in _dict[trainee_id]["user"].keys() else user_df_cols_default[col])  for col in user_df_cols}

                user_dict["trainee_id"] = trainee_id
                user_dict["trainee"] = trainee

                print("User data dict created\n")

                # check for entry in strapi
                headers = {"Content-Type": "application/json"}
                pluralapi = "github-user-metas"
                q_url = "https://dev-cms.10academy.org/api/{}?filters[trainee][id][$eq]={}".format(pluralapi, trainee)
                
                r = get_table_data_strapi(q_url)
                
                """try:
                    r = requests.get(
                                    q_url,
                                    headers = headers
                                    ).json()
                except Exception as e:
                    print("Error in getting user meta data from strapi: {}\n".format(e))
                    user_error_dict["trainee_id"].append(trainee_id)
                    user_error_dict["user"].append(user)
                    user_error_dict["repo_name"].append(repo_name)
                    user_error_dict["error"].append(e)
                    continue"""

                # check if entry exists
                print("Checking if entry exists in strapi...\n")

                if len(r) == 0:
                    r_list = []
                elif  "error" not in r[0]:
                    r_list = [d for d in r if d["attributes"]["week"] == week]
                else:
                    print("Error in getting user meta data from strapi: {}\n".format(r[0]))
                    user_error_dict["trainee_id"].append(trainee_id)
                    user_error_dict["user"].append(user)
                    user_error_dict["repo_name"].append(repo_name)
                    user_error_dict["error"].append(r[0])
                    continue


                if len(r_list) == 0:
                    print("Entry does not exist in strapi...\n")
                    
                    # create entry
                    print("Creating entry in strapi...\n\n")

                    # get the user meta entry
                    user_dict = json.loads(json.dumps({col:(user_dict[col] if not isinstance(user_dict[col], float) 
                            else round(user_dict[col],10)) for col in user_df_cols}))

                    user_dict["week"] = week
                    user_dict["trainee"] = trainee

                    insert_data_strapi(data=user_dict, pluralapi=pluralapi)
                    # create entry in strapi
                
                else:
                    #check if entry is the same
                    print("Entry exists in strapi...\n")
                    print("Checking if entry is the same...\n\n")
                    
                    # get the strapi entry
                    srapi_dict = {col:r_list[0]['attributes'][col] if not isinstance(r_list[0]['attributes'][col], float) 
                            else round(r_list[0]['attributes'][col],10) for col in user_df_cols}
                    
                    # get the user meta entry
                    user_dict = json.loads(json.dumps({col:(user_dict[col] if not isinstance(user_dict[col], float) 
                            else round(user_dict[col],10)) for col in user_df_cols}))

                    if srapi_dict == user_dict:
                        print("Entry is the same...\n")
                        pass
                    else:
                        print("Entry is not the same...\n")
                        # update entry
                        print("Updating entry in strapi...\n\n")
                        
                        # update entry in strapi
                        user_dict["week"] = week
                        user_dict["trainee"] = trainee
                        update_data_strapi(data=user_dict, pluralapi=pluralapi, entry_id=r_list[0]['id'])         

            else:
                print("Error retrieving user data for user: {} and repo: {}\n".format(user, repo_name))
                user_error_dict["trainee_id"].append(trainee_id)
                user_error_dict["repo_name"].append(repo_name)
                user_error_dict["user"].append(user)
                user_error_dict["error"].append(hld["user"])


            ###############################################################################################
            # get the repo data dict
            if "error" not in hld["repo_meta"]:
                print("Creating repo data dict...\n")

                repo_dict = {col:(_dict[trainee_id]["repo_meta"][col]
                    if col in _dict[trainee_id]["repo_meta"].keys() else None)  for col in repo_df_cols}

                if starter_code_ref_basevalues:
                    # normalize the repo data
                    print("Normalizing repo_meta data...\n")
                    repo_dict = normalize_repo_data(repo_dict, starter_code_ref_basevalues)

                repo_dict = {col:(repo_dict[col]
                    if col in _dict[trainee_id]["repo_meta"].keys() else repo_df_cols_default[col])  for col in repo_df_cols}


                repo_dict["trainee_id"] = trainee_id
                repo_dict["trainee"] = trainee

                print("Repo data dict created\n")

                # check for entry in strapi
                headers = {"Content-Type": "application/json"}
                pluralapi = "github-repo-metas"
                week = week
                q_url = "https://dev-cms.10academy.org/api/{}?filters[trainee][id][$eq]={}".format(pluralapi, trainee)

                r = get_table_data_strapi(q_url)

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
                if len(r) == 0:
                    r_list = []
                elif "error" not in r[0]:
                    r_list = [d for d in r if d["attributes"]["week"] == week]
                else:
                    print("Error in getting repo meta data from strapi: {}\n".format(r[0]))
                    repo_meta_error_dict["trainee_id"].append(trainee_id)
                    repo_meta_error_dict["user"].append(user)
                    repo_meta_error_dict["repo_name"].append(repo_name)
                    repo_meta_error_dict["error"].append(r[0])
                    continue

                if len(r_list) == 0:
                    # create entry
                    print("Entry does not exist in strapi...\n")
                    print("Creating entry in strapi...\n\n")
                    
                    # create entry in strapi
                    repo_dict = json.loads(json.dumps({col:(repo_dict[col] if not isinstance(repo_dict[col], float) 
                            else round(repo_dict[col],10)) for col in repo_df_cols}))

                    repo_dict["week"] = week
                    repo_dict["trainee"] = trainee

                    insert_data_strapi(data=repo_dict, pluralapi=pluralapi)
                
                else:
                    #check if entry is the same
                    print("Entry exists in strapi...\n")
                    print("Checking if entry is the same...\n")
                    
                    # get the strapi entry
                    srapi_dict = {col:r_list[0]['attributes'][col] if not isinstance(r_list[0]['attributes'][col], float) 
                            else round(r_list[0]['attributes'][col],10) for col in repo_df_cols}
                    
                    # get the repo meta entry
                    repo_dict = json.loads(json.dumps({col:(repo_dict[col] if not isinstance(repo_dict[col], float) 
                            else round(repo_dict[col],10)) for col in repo_df_cols}))

                    if srapi_dict == repo_dict:
                        print("Entry is the same...\n\n")
                        pass
                    else:
                        # update entry
                        print("Entry is not the same...\n")
                        print("Updating entry in strapi...\n\n")
                        
                        # update entry in strapi
                        repo_dict["week"] = week
                        repo_dict["trainee"] = trainee
                        update_data_strapi(data=repo_dict, pluralapi=pluralapi, entry_id=r_list[0]['id'])

                

            else:
                print("Error retrieving repo data for user: {} and repo: {}\n".format(user, repo_name))
                repo_meta_error_dict["trainee_id"].append(trainee_id)
                repo_meta_error_dict["repo_name"].append(repo_name)
                repo_meta_error_dict["user"].append(user)
                repo_meta_error_dict["error"].append(hld["repo_meta"])
            

            ###############################################################################################
            if len(hld["repo_anlysis_metrics"]) > 0:
                print("Creating repo analysis dict...\n")
                
                repo_analysis_dict = {col:(_dict[trainee_id]["repo_anlysis_metrics"][col]
                                      if col in _dict[trainee_id]["repo_anlysis_metrics"].keys() else None)  
                                      for col in repo_analysis_df_cols}
                
                # normalize the repo analysis data
                if starter_code_ref_basevalues:
                    print("Normalizing repo analysis data...\n")
                    repo_analysis_dict = normalize_repo_data(repo_analysis_dict, starter_code_ref_basevalues)

                repo_analysis_dict = {col:(repo_analysis_dict[col]
                                      if col in _dict[trainee_id]["repo_anlysis_metrics"].keys() else repo_analysis_df_cols_default[col])  
                                      for col in repo_analysis_df_cols}

                repo_analysis_dict["trainee_id"] = trainee_id
                repo_analysis_dict["trainee"] = trainee

                print("Repo analysis dict created\n")


                # check for entry in strapi
                headers = {"Content-Type": "application/json"}
                pluralapi = "github-repo-metrics"
                week = week
                q_url = "https://dev-cms.10academy.org/api/{}?filters[trainee][id][$eq]={}".format(pluralapi, trainee)

                r = get_table_data_strapi(q_url)
                
                """try:
                    r = requests.get(
                                    q_url,
                                    headers = headers
                                    ).json()
                except Exception as e:
                    print("Error in getting repo analysis data from strapi: {}\n".format(e))
                    repo_metric_error_dict["trainee_id"].append(trainee_id)
                    repo_metric_error_dict["user"].append(user)
                    repo_metric_error_dict["repo_name"].append(repo_name)
                    repo_metric_error_dict["error"].append(e)
                    continue"""

                # check if entry exists
                print("Checking if entry exists...\n")

                if len(r) == 0:
                    r_list = []
                elif "error" not in r[0]:
                    r_list = [d for d in r if d["attributes"]["week"] == week]
                else:
                    print("Error in getting repo analysis data from strapi: {}\n".format(r[0]))
                    repo_metric_error_dict["trainee_id"].append(trainee_id)
                    repo_metric_error_dict["user"].append(user)
                    repo_metric_error_dict["repo_name"].append(repo_name)
                    repo_metric_error_dict["error"].append(r[0])
                    continue

                if len(r_list) == 0:
                    # create entry
                    print("Entry does not exist...\n")
                    print("Creating entry in strapi...\n")
                    
                    # create entry in strapi
                    repo_analysis_dict = json.loads(json.dumps({col:(repo_analysis_dict[col] if not isinstance(repo_analysis_dict[col], float)
                            else round(repo_analysis_dict[col],10)) for col in repo_analysis_df_cols}))

                    repo_analysis_dict["week"] = week
                    repo_analysis_dict["trainee"] = trainee

                    insert_data_strapi(data=repo_analysis_dict, pluralapi=pluralapi)

                    entry_made_into_analysis_table = True
                else:
                    #check if entry is the same
                    print("Entry exists in strapi...\n")
                    print("Checking if entry is the same...\n")
                    
                    # get the strapi entry
                    srapi_dict = {col:r_list[0]['attributes'][col] if not isinstance(r_list[0]['attributes'][col], float) 
                            else round(r_list[0]['attributes'][col],10) for col in repo_analysis_df_cols}
                    
                    # get the repo analysis entry
                    repo_analysis_dict = json.loads(json.dumps({col:(repo_analysis_dict[col] if not isinstance(repo_analysis_dict[col], float) 
                            else round(repo_analysis_dict[col],10)) for col in repo_analysis_df_cols}))

                    if srapi_dict == repo_analysis_dict:
                        print("Entry is the same...\n")
                        pass
                    else:
                        print("Entry is not the same...\n")
                        # update entry
                        print("Updating entry in strapi...\n\n")
                        
                        # update entry in strapi
                        repo_analysis_dict["week"] = week
                        repo_analysis_dict["trainee"] = trainee
                        update_data_strapi(data=repo_analysis_dict, pluralapi=pluralapi, entry_id=r_list[0]['id'])

                        entry_made_into_analysis_table = True   
            else:
                print("Error retrieving repo analysis data for user: {} and repo: {}\n".format(user, repo_name))
                repo_metric_error_dict["trainee_id"].append(trainee_id)
                repo_metric_error_dict["repo_name"].append(repo_name)
                repo_metric_error_dict["user"].append(user)
                repo_metric_error_dict["error"].append(hld["repo_anlysis_metrics"])


        ########################################################################################################################

        # Save users with Github User analysis error
        if len(user_error_dict["user"]) > 0:

            print("Saving users with Github User analysis error\n")
            user_error_df = pd.DataFrame(user_error_dict)
            output_dir = "data"
            now = datetime.now()
            user_error_df.to_csv("{}/users_with_github_user_analysis_error_{}.csv".format(output_dir, now.strftime("%Y_%m_%d__%H_%M_%S")), index=False)
    
        # Save users with Github Repo analysis error
        if len(repo_meta_error_dict["user"]) > 0:

            print("Saving users with Github Repo meta analysis error\n")
            repo_meta_error_df = pd.DataFrame(repo_meta_error_dict)
            output_dir = "data"
            now = datetime.now()
            repo_meta_error_df.to_csv("{}/users_with_github_repo_meta_analysis_error_{}.csv".format(output_dir, now.strftime("%Y_%m_%d__%H_%M_%S")), index=False)

        
        # Save users with Github Repo analysis error
        if len(repo_metric_error_dict["user"]) > 0:

            print("Saving users with Github Repo analysis error\n")
            repo_metric_error_df = pd.DataFrame(repo_metric_error_dict)
            output_dir = "data"
            now = datetime.now()
            repo_metric_error_df.to_csv("{}/users_with_github_repo_analysis_error_{}.csv".format(output_dir, now.strftime("%Y_%m_%d__%H_%M_%S")), index=False)
            
            
        if len(user_error_dict["user"]) == 0 and len(repo_meta_error_dict["user"]) == 0 and len(repo_metric_error_dict["user"]) == 0:
            print("No errors found\n\n")
    
        ########################################################################################################################

        if entry_made_into_analysis_table:
            print("Entry made into analysis table\n\n")
                
            # Compute the Analysis Metrics Summary
            print("Computing Analysis Metrics Summary...\n")

            # get the analysis metrics summary
            headers = {"Content-Type": "application/json"}
            pluralapi = "github-repo-metrics"
            q_url = "https://dev-cms.10academy.org/api/{}?filters[week][$eq]={}".format(pluralapi, week)
            
            r = get_table_data_strapi(q_url)
            
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
                            # ignore place holders for null values
                            if (isinstance(entry["attributes"][col],float) and entry["attributes"][col] != -999.0) or (isinstance(entry["attributes"][col],int) and entry["attributes"][col] != -999):
                                df_dict[col].append(entry["attributes"][col])
                            else:
                                df_dict[col].append(None)

                    cat_df = pd.DataFrame(df_dict)

                    cat_dict = {col:{"max":None, "min":None, "sum":None, "break_points":None} for col in metrics_list}

                    for col in metrics_list:
                        _min = cat_df[[col]].min().to_list()[0]
                        _max = cat_df[[col]].max().to_list()[0]
                        cat_dict[col]["max"] = _max
                        cat_dict[col]["min"] = _min
                        cat_dict[col]["break_points"] = get_break_points(_min, _max)
                       
                        # compute sum for eligible columns
                        if col in sum_list:
                            cat_dict[col]["sum"] = cat_df[[col]].sum().to_list()[0]

                    # create rannk dict
                    rank_dict = {col:[] for col in repo_metrics_cols}

                    for i,row in cat_df.iterrows():
                        for col in repo_metrics_cols:
                            if col == "trainee_id":
                                rank_dict[col].append(row[col])
                            else:
                                val = row[col]
                                if val != None:
                                    break_points = cat_dict[col]["break_points"]
                                    if col != "cc":
                                        rank_dict[col].append(get_metric_category(val=val, break_points=break_points, reverse=False))
                                    else:
                                        rank_dict[col].append(get_metric_category(val=val, break_points=break_points, reverse=True))
                                else:
                                    rank_dict[col].append(None)

                    # create rank df
                    rank_df = pd.DataFrame(rank_dict)
                    rank_df["week"] = week
                    rank_df = rank_df.merge(trainee_df, on="trainee_id")

                    rank_data = json.loads(rank_df.to_json(orient="records"))

                    # load data into strapi
                    pluralapi = "github-repo-metric-ranks"

                    for r in rank_data:
                        print("Loading data into strapi...\n")
                        # check if entry exists
                        print("Checking if entry exists...\n")
                        headers = {"Content-Type": "application/json"}
                        q_url = "https://dev-cms.10academy.org/api/{}?filters[week][$eq]={}&filters[trainee_id][$eq]={}".format(pluralapi, week, r["trainee_id"])
                        
                        r_list = get_table_data_strapi(q_url)
                        
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
                                print("Entry already exists for user: {} and week: {}\n".format(r["trainee_id"], week))
                                # update entry in strapi
                                print("Updating entry for user user: {} and week: {}\n".format(r["trainee_id"], week))
                                update_data_strapi(data=r, pluralapi=pluralapi, entry_id=r_list[0]['id'])
                            else:
                                print("Error checking if entry exists for user: {} and week: {}\n".format(r["trainee_id"], week))
                                print(r_list[0])
                                print("\n")
                        else:
                            # create entry in strapi
                            print("Entry does not exist for user: {} and week: {}\n".format(r["trainee_id"], week))
                            print("Creating entry in strapi...\n")
                            insert_data_strapi(data=r, pluralapi=pluralapi)

                            
                    
                    ########################################################################################################################
                    # get summary metrics dict
                    cat_dict = get_metric_summary_dict(cat_dict)

                    # create summary metrics df
                    cat_df = pd.DataFrame(cat_dict)
                    cat_df["week"] = week
                    cat_df["batch"] = batch

                    # create summary metrics data
                    cat_data = json.loads(cat_df.to_json(orient="records"))

                    # load data into strapi
                    pluralapi = "github-metrics-summaries"
                    
                    for r in cat_data:
                        print("Loading data into strapi...\n")
                        # check if entry exists
                        print("Checking if entry exists...\n")
                        headers = {"Content-Type": "application/json"}
                        q_url = "https://dev-cms.10academy.org/api/{}?filters[week][$eq]={}&filters[metrics][$eq]={}".format(pluralapi, week, r["metrics"])
                        

                        r_list = get_table_data_strapi(q_url)
                        
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
                                print("Entry already exists for week: {}\n".format(week))
                                # update entry in strapi
                                update_data_strapi(data=r, pluralapi=pluralapi, entry_id=r_list[0]['id'])
                            else:
                                print("Error checking if entry exists for week: {}\n".format(week))
                                print(r_list[0])
                                print("\n")
                        else:
                            # create entry in strapi
                            print("Entry does not exist for week: {}\n".format(week))
                            print("Creating entry in strapi...\n")
                            insert_data_strapi(data=r, pluralapi=pluralapi)


                else:
                    print("Error getting data from strapi...\n")
                    print(r[0])
                    print("\n")


            except Exception as e:
                print("Error retrieving analysis metrics summary for week: {}\n".format(week))
                print(e)


        else:  
            print("No entry made into analysis table. Hence no entries to be made into metric rank and metric summary tables\n\n")
        
    else:
        # if trainee data is not returned
        print("Error: trainee data was not returned")
        sys.exit(1)

else:
    # if token is not returned
    print("Error: github token was not found")
    sys.exit(1)


    