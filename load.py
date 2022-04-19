from datetime import time
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



from modules.strapi_methods import get_table_data_strapi, upload_to_strapi    
from modules.Category_Dict import Metrics_Summary_Dict
from modules.analyzer_utils import get_df, get_df_dict, get_github_analysis_dict, get_id_userid_df, get_metric_summary_dict, get_rank_dict, get_repo_df_dict, get_repo_names

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

    trainee_dict = get_table_data_strapi("trainees")

    # check if trainee_dict was returned
    if "error" not in trainee_dict:
        trainee_df = get_id_userid_df(trainee_dict)

        # read in the data
        dt_user = pd.read_csv("data/github_usernames.csv")
        dt_repo = pd.read_csv("data/github_repos_wk1.csv")
        github_df = dt_user.merge(dt_repo, on="userId").head(1)


        # set needed variables
        metrics_list = ["additions","avg_lines_per_class","avg_lines_per_function","avg_lines_per_method",
                        "cc","difficulty",'effort','lloc','loc','mi','num_classes','num_functions','num_methods',
                        'sloc','time']
        
        sum_list =  ["additions","difficulty",'effort','lloc','loc','num_classes','num_functions','num_methods',
                     'sloc','time']

        user_df_cols = ['avatar_url', 'bio', 'commits', 'email', 'followers', 'following', 'html_url', 
                        'issues', 'name', 'public_repos', 'pull_requests']

        repo_df_cols = ['branches', 'contributors', 'description', 'forks', 'html_url', 'languages', 'total_commits', 
                        "interested_files", "num_ipynb", "num_js", "num_py", "num_dirs", "num_files"]

        repo_analysis_df_cols = ['additions', 'avg_lines_per_class', 'avg_lines_per_function', 'avg_lines_per_method',
                                'blank', 'cc', 'cc_rank', 'comments', 'difficulty', 'effort', 'lloc', 'loc', 'mi', 
                                'mi_rank', 'multi', 'num_classes', 'num_functions', 'num_methods', 'single_comments',
                                'sloc', 'time']

        repo_metrics_cols = ['additions', 'avg_lines_per_class', 'avg_lines_per_function', 'avg_lines_per_method', 
                            'cc', 'difficulty', 'effort', 'lloc', 'loc', 'mi', 'num_classes', 'num_functions', 
                            'num_methods', 'sloc', 'time']


        userid_list = list(github_df["userId"].values)


        # get the github analysis dict
        
        print("Retrieving data from API...\n")
        
        #github_analysis_dict = get_github_analysis_dict(github_df, github_token)


        # retrive user and repo data
        counter = 0
        user_error_dict = {"userid":[], "repo_name":[], "user":[], "error":[]}
        repo_meta_error_dict = {"userid":[], "repo_name":[], "repo":[], "error":[]}
        repo_metric_error_dict = {"userid":[], "repo_name":[], "repo":[], "error":[]}

        for _, userid, user, repo_name in github_df.itertuples():
            print("Retrieving data for user: {} and repo: {}...".format(user, repo_name))
            hld = dict()
            if counter != 0 and counter%5 == 0:
                print(user)
                print("Sleeping for 60 seconds\n")
                time.sleep(60)
                print("Resumed...\n")

            # get repo meta data and analysis data
            repo_meta_repo_pyanalysis = single_repos_meta_single_repos_pyanalysis(user, github_token, repo_name, api=False)

            
            hld["repo_meta"] = repo_meta_repo_pyanalysis["repo_meta"][repo_name]

            try:
                hld["repo_anlysis_metrics"] = repo_meta_repo_pyanalysis["analysis_results"]["repo_summary"]
            except:
                hld["repo_anlysis_metrics"] = repo_meta_repo_pyanalysis["analysis_results"]

            trainee = trainee_df[trainee_df["userId"]==userid].trainee.values[0]

            # get user data from github api
            hld["user"] = get_user(user, github_token, api=False)

            _dict = dict()
            _dict[userid] =  hld
            
            counter += 1
            
            print("Data for user: {} and repo: {} retrieved\n".format(user, repo_name))

            if "error" not in hld["user"]:
                # get the user data dict
                print("Creating user data dict...\n")
                user_dict = {col:(_dict[userid]["user"][col]
                    if col in _dict[userid]["user"].keys() else None)  for col in user_df_cols}

                user_dict["userId"] = userid
                user_dict["trainee"] = trainee

                print("User data dict created\n")

                # check for entry in strapi
                headers = {"Content-Type": "application/json"}
                pluralapi = "github-user-metas"
                week = "week1"
                q_url = "https://dev-cms.10academy.org/api/{}?filters[trainee][id][$eq]={}&pagination[start]=0&pagination[limit]=100".format(pluralapi, trainee)

                r = requests.get(
                                q_url,
                                headers = headers
                                ).json()

                if "error" not in r:
                    # check if entry exists
                    print("Checking if entry exists in strapi...\n")

                    if len(r["data"]) == 0:
                        r_list = []
                    else:
                        r_list = [d for d in r['data'] if d["attributes"]["week"] == week]

                    if len(r_list) == 0:
                        # create entry
                        print("Creating entry in strapi...\n")
                        ######################################
                        # create entry in strapi
                    else:
                        #check if entry is the same
                        print("Checking if entry is the same...\n")
                        
                        # get the strapi entry
                        srapi_dict = {col:r_list[0]['attributes'][col] if not isinstance(r_list[0]['attributes'][col], float) 
                                else round(r_list[0]['attributes'][col],10) for col in user_df_cols}
                        
                        # get the repo analysis entry
                        user_dict = json.loads(json.dumps({col:(user_dict[col] if not isinstance(user_dict[col], float) 
                                else round(user_dict[col],10)) for col in user_df_cols}))

                        if srapi_dict == user_dict:
                            print("Entry is the same...\n")
                            pass
                        else:
                            print("Entry is not the same...\n")
                            # update entry
                            print("Updating entry in strapi...\n")
                            ######################################
                            # update entry in strapi
            else:
                print("Error retrieving user data for user: {} and repo: {}\n".format(user, repo_name))
                user_error_dict["userid"].append(userid)
                user_error_dict["repo_name"].append(repo_name)
                user_error_dict["user"].append(user)
                user_error_dict["error"].append(hld["user"])

            # get the repo data dict
            if "error" not in hld["repo_meta"]:
                print("Creating repo data dict...\n")
                repo_dict = {col:(_dict[userid]["repo_meta"][col]
                    if col in _dict[userid]["repo_meta"].keys() else None)  for col in repo_df_cols}

                repo_dict["userId"] = userid
                repo_dict["trainee"] = trainee

                print("Repo data dict created\n")

                # check for entry in strapi
                headers = {"Content-Type": "application/json"}
                pluralapi = "github-repo-metas"
                week = "week1"
                q_url = "https://dev-cms.10academy.org/api/{}?filters[trainee][id][$eq]={}&pagination[start]=0&pagination[limit]=100".format(pluralapi, trainee)

                r = requests.get(
                                q_url,
                                headers = headers
                                ).json()

                if "error" not in r:
                    # check if entry exists
                    if len(r["data"]) == 0:
                        r_list = []
                    else:
                        r_list = [d for d in r['data'] if d["attributes"]["week"] == week]

                    if len(r_list) == 0:
                        # create entry
                        print("Creating entry in strapi...\n")
                        ######################################
                        # create entry in strapi
                    else:
                        #check if entry is the same
                        print("Checking if entry is the same...\n")
                        
                        # get the strapi entry
                        srapi_dict = {col:r_list[0]['attributes'][col] if not isinstance(r_list[0]['attributes'][col], float) 
                                else round(r_list[0]['attributes'][col],10) for col in repo_df_cols}
                        
                        # get the repo analysis entry
                        repo_dict = json.loads(json.dumps({col:(repo_dict[col] if not isinstance(repo_dict[col], float) 
                                else round(repo_dict[col],10)) for col in repo_df_cols}))

                        if srapi_dict == repo_dict:
                            print("Entry is the same...\n")
                            pass
                        else:
                            print("Entry is not the same...\n")
                            # update entry
                            print("Updating entry in strapi...\n")
                            ######################################
                            # update entry in strapi
            else:
                print("Error retrieving repo data for user: {} and repo: {}\n".format(user, repo_name))
                repo_meta_error_dict["userid"].append(userid)
                repo_meta_error_dict["repo_name"].append(repo_name)
                repo_meta_error_dict["repo"].append(user)
                repo_meta_error_dict["error"].append(hld["repo_meta"])
            
            
            if "error" not in hld["repo_anlysis_metrics"]:
                print("Creating repo analysis dict...\n")
                
                repo_analysis_dict = {col:(_dict[userid]["repo_anlysis_metrics"][col]
                                      if col in _dict[userid]["repo_anlysis_metrics"].keys() else None)  
                                      for col in repo_analysis_df_cols}

                repo_analysis_dict["userId"] = userid
                repo_analysis_dict["trainee"] = trainee

                print("Repo analysis dict created\n")


                # check for entry in strapi
                headers = {"Content-Type": "application/json"}
                pluralapi = "github-repo-metrics"
                week = "week1"
                q_url = "https://dev-cms.10academy.org/api/{}?filters[trainee][id][$eq]={}&pagination[start]=0&pagination[limit]=100".format(pluralapi, trainee)

                r = requests.get(
                                q_url,
                                headers = headers
                                ).json()

                if "error" not in r:
                    # check if entry exists
                    print("Checking if entry exists...\n")

                    if len(r["data"]) == 0:
                        r_list = []
                    else:
                        r_list = [d for d in r['data'] if d["attributes"]["week"] == week]

                    if len(r_list) == 0:
                        # create entry
                        print("Entry does not exist...\n")
                        print("Creating entry in strapi...\n")
                        ######################################
                        # create entry in strapi
                    else:
                        #check if entry is the same
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
                            print("Updating entry in strapi...\n")
                            ######################################
                            # update entry in strapi

            else:
                print("Error retrieving repo analysis data for user: {} and repo: {}\n".format(user, repo_name))
                repo_metric_error_dict["userid"].append(userid)
                repo_metric_error_dict["repo_name"].append(repo_name)
                repo_metric_error_dict["repo"].append(user)
                repo_metric_error_dict["error"].append(hld["repo_anlysis_metrics"])


            """
        

            print("Retrieving data from API completed\n")

            
            "with open("data/wk1_gihub_data_updated_.json", "w") as f:
                github_analysis_dict = json.dump(github_analysis_dict,f)"

            # get list of repo names
            repo_name_list = get_repo_names(userid_list, github_analysis_dict)

            # create the metrics summary dict
            cat_dict = Metrics_Summary_Dict(metrics_list, github_analysis_dict, sum_list).get_metrics_summary_dict()

            rank_dict = get_rank_dict(github_analysis_dict, cat_dict)

            # Update the github analysis dict with the computed ranks
            for _id,ranks in rank_dict.items():
                github_analysis_dict[_id]["metrics_rank"] = ranks

            # get the user dataframe
            print("Creating user dataframe...")
            user_dict = get_df_dict(user_df_cols, "user", userid_list, github_analysis_dict)
            user_df = get_df("week1", user_dict).merge(trainee_df, on="userId")
            # drop userid column
            user_df.drop(["userId"],axis=1, inplace=True)
            print("Creating user dataframe completed\n")


            # get the repo meta data dataframe
            print("Creating repo meta data dataframe...")
            repo_meta_dict = get_repo_df_dict(repo_df_cols, "repo_meta", userid_list, repo_name_list, github_analysis_dict)
            repo_meta_df = get_df("week1", repo_meta_dict).merge(trainee_df, on="userId")
            # drop userid column
            repo_meta_df.drop(["userId"],axis=1, inplace=True)
            print("Creating repo meta data dataframe completed\n")

            # get repo analysis dataframe
            print("Creating repo analysis dataframe...")
            repo_analysis_dict = get_df_dict(repo_analysis_df_cols, "repo_anlysis_metrics", userid_list, github_analysis_dict)
            repo_analysis_df = get_df("week1", repo_analysis_dict).merge(trainee_df, on="userId")
            # drop userid column
            repo_analysis_df.drop(["userId"],axis=1, inplace=True)
            print("Creating repo analysis dataframe completed\n")

            # get repo metrics dataframe
            print("Creating repo metrics dataframe...")
            repo_metrics_dict = get_df_dict(repo_metrics_cols, "metrics_rank", userid_list, github_analysis_dict)
            repo_metrics_df = get_df("week1", repo_metrics_dict).merge(trainee_df, on="userId")
            # drop userid column
            repo_metrics_df.drop(["userId"],axis=1, inplace=True)
            print("Creating repo metrics dataframe completed\n")

            # metrics summary dataframe
            print("Creating metrics summary dataframe...")
            metrics_summary_dict = get_metric_summary_dict(cat_dict)
            metrics_summary_df = get_df("week1", metrics_summary_dict)
            print("Creating metrics summary dataframe completed\n")

            # strapi_table and dataframe pairing
            strapi_table_pairing = {
                                    "github-metrics-summaries":metrics_summary_df, "github-repo-metas":repo_meta_df, 
                                    "github-repo-metrics":repo_analysis_df, "github-repo-metric-ranks":repo_metrics_df,
                                    "github-user-metas":user_df
                                    }


            # load data into strapi tables
            print("Loading data into strapi tables...\n")
            upload_to_strapi(strapi_table_pairing, token=False)
            print("Loading data into strapi tables completed\n")"""

    else:
        # if trainee data is not returned
        print("Error: trainee data was not returned")
        sys.exit(1)

else:
    # if token is not returned
    print("Error: github token was not found")
    sys.exit(1)