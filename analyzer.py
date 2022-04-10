import json
import os
import sys
import pandas as pd


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
        github_df = dt_user.merge(dt_repo, on="userId").head(2)


        # set needed variables
        metrics_list = ["additions","avg_lines_per_class","avg_lines_per_function","avg_lines_per_method",
                            "cc","difficulty",'effort','lloc','loc','mi','num_classes','num_functions','num_methods',
                            'sloc','time']

        user_df_cols = ['avatar_url', 'bio', 'commits', 'email', 'followers', 'following', 'html_url', 
                        'issues', 'name', 'public_repos', 'pull_requests']

        repo_df_cols = ['branches', 'clones', 'contributors', 'description', 'forks', 'html_url', 
                        'languages', 'total_commits', 'visitors']

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
        
        github_analysis_dict = get_github_analysis_dict(github_df, github_token)

        print("Retrieving data from API completed\n")

        
        """with open("data/wk1_gihub_data_updated_.json", "w") as f:
            github_analysis_dict = json.dump(github_analysis_dict,f)"""

        # get list of repo names
        repo_name_list = get_repo_names(userid_list, github_analysis_dict)

        # create the metrics summary dict
        cat_dict = Metrics_Summary_Dict(metrics_list, github_analysis_dict).get_metrics_summary_dict()

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
        print("Loading data into strapi tables completed\n")

    else:
        # if trainee data is not returned
        print("Error: trainee data was not returned")
        sys.exit(1)

else:
    # if token is not returned
    print("Error: github token was not found")
    sys.exit(1)