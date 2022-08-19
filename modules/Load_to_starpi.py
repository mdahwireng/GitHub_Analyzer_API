from datetime import datetime
import os
import sys
import time
import pandas as pd
from app import get_user
import pytz
from dateutil import parser

from modules.analyzer_utils import get_break_points, get_metric_category, get_metric_summary_dict, get_repo_meta_repo_analysis, send_graphql_query
from modules.strapi_methods import get_table_data_strapi, get_trainee_data, insert_data_strapi, update_data_strapi







# set needed variables

metrics_detail_dict = {
               "Python":{
                   "metrics_descriptions":
                    {
                        "additions": "added lines of code",
                        "avg_lines_per_class": "average lines of code per class",
                        "avg_lines_per_function": "average lines of code per function",
                        "avg_lines_per_method": "average lines of code per method",
                        "blank": "blank lines",
                        "cc": "cyclomatic complexity score",
                        "cc_rank": "cyclomatic complexity rank",
                        "comments": "lines of comments",
                        "difficulty": "quantified level of difficulty in writing the code",
                        "effort": "quantified effort invested in writing the codes",
                        "lloc": "logical lines of code",
                        "loc": "lines of code",
                        "mi": "maintainability index score",
                        "mi_rank": "maintainability index rank",
                        "multi": "multi-line comments",
                        "num_classes": "number of classes",
                        "num_functions": "number of functions",
                        "num_methods": "number of methods",
                        "single_comments": "single-line comments",
                        "sloc": "source lines of code",
                        "time": "quantified time spent in writing the code"
    
                    },
                    "sum_list": ["additions","difficulty",'effort','lloc','loc','num_classes','num_functions','num_methods','sloc','time'],

                    "metrics_list": ["additions","avg_lines_per_class","avg_lines_per_function","avg_lines_per_method",
                                    "cc","difficulty",'effort','lloc','loc','mi','num_classes','num_functions','num_methods',
                                    'sloc','time']

                        },
                "JavaScript":{
                    "metrics_descriptions":
                    {
                        "additions": "added lines of code",
                        "avg_lines_per_function": "average lines of code per function",
                        "cc": "cyclomatic complexity score",
                        "cc_rank": "cyclomatic complexity rank",
                        "comments": "lines of comments",
                        "nloc": "lines of code (excluding comments)",
                        "num_functions": "number of functions",
                        "token_count": "number of tokens",
                        "tot_lines": "total lines of code",
                    },
                        
                    "sum_list": ["additions","nloc","num_functions","token_count"],

                    "metrics_list": ["additions","avg_lines_per_function","cc","nloc","num_functions","token_count"]   
                            }
                        }

cat_list = [0.99,0.9,0.75,0.5]


repo_df_cols = ["html_url", "week", "run_number"]

user_df_cols = ["trainee_id",'avatar_url', 'bio', 'commits', 'email', 'followers', 'following', 'html_url', 
                'issues', 'name', 'public_repos', 'pull_requests', "run_number"]

repo_meta_df_cols = ["repo_name","trainee_id",'branches', 'contributors', 'description', 'forks', 'html_url', 'languages', 'total_commits', 
                "interested_files", "num_dirs", "num_files", "commit_stamp", "run_number"]
    
commit_history_df_cols = ["commit_history", "contribution_counts", "commits_on_branch", "commits_on_default_to_branch", "num_contributors", "branch", "default_branch", "repo_name", "html_link", "trainee_id", "file_level", "run_number"]



# set default values

repo_df_cols_default = {"html_url": "", "run_number":""}

user_df_cols_default = {"trainee_id":"",'avatar_url':"", 'bio':"", 'commits':-999, 'email':"", 'followers':-999, 'following':-999, 'html_url':"", 
                'issues':-999, 'name':"", 'public_repos':-999, 'pull_requests':-999, "run_number":""}


repo_meta_df_cols_default = {"repo_name":"","trainee_id":"",'branches':-999, 'contributors':[], 'description':"", 'forks':-999, 'html_url':"", 'languages':[], 'total_commits':-999, 
                "interested_files":[], "num_ipynb":-999, "num_js":-999, "num_py":-999, "num_dirs":-999, "num_files":-999, "commit_stamp":[], "run_number":""}


repo_analysis_df_cols_default = {"trainee_id":"","run_number":"", "analysis_details":[]}

commit_history_df_cols_default = {"commit_history":[], "contribution_counts":[], "commits_on_branch":-999, "commits_on_default_to_branch":-999, "num_contributors":-999, "branch":"", "default_branch":"", "repo_name":"", "html_link":"", "trainee_id":"", "file_level":[], "run_number":""}


columns_dict = {"repo_df": repo_df_cols, "user_df": user_df_cols, "repo_meta_df": repo_meta_df_cols, "commit_history_df": commit_history_df_cols}
default_vals_dict = {"repo_df": repo_df_cols_default, "user_df": user_df_cols_default, "repo_analysis_df": repo_analysis_df_cols_default, "repo_meta_df": repo_meta_df_cols_default, "commit_history_df": commit_history_df_cols_default}


class Load_To_Strapi:
    """
    This class is used to load data to Strapi.

    methods:
        __init__: initializes the class
        get_analysis_data: Gets analysis data from api
                            Returns a dictionary of analysis data with repo meta, repo_analysis_metrics, commit_history and user as keys
        load_repo_meta_and_repo_to_strapi: Loads data to repo and repo_meta tables in strapi
        load_user_meta_to_strapi: Loads user meta data to strapi
        load_commit_history_to_strapi: Loads commit history data to strapi
        populate_lang_val_dict: Populate the language value dict with the data from the github api
        update_lang_val_dict: Updates the language value dict with already existing data in the database
        create_analysis_dict: Creates the analysis dict with the data from the lang val dicty
        create_analysis_strapi_records: Creates records form analysis dict to be uploaded into strapi
        save_errors: Saves errors encountered during uploads
        load_entries_to_strapi: Loads entries to strapi
        run_to_load: Runs the complete load process.

    """

    def __init__(self, platform, week, batch, run_number, base_url, github_df, github_token, strapi_token, columns_dict=columns_dict, default_vals_dict=default_vals_dict, run_type="main", metrics_detail_dict=metrics_detail_dict, cat_list=cat_list) -> None:
        """
        Initialize the class
        
        Args:
            platform (str): platform name
            week (str): week number
            batch (str): batch number
            run_number (str): run number
            base_url (str): base url of the platform
            github_df (pd.DataFrame): github dataframe
            github_token (str): github token
            strapi_token (str): strapi token
            columns_dict (dict): columns dictionary
            default_vals_dict (dict): default values dictionary
            run_type (str): run type, indicates if the run is for main or for error fixing run, default is main
            metrics_detail_dict (dict): metrics detail dictionary
            cat_list (list): category list
            
        Returns:
            None
        """
        
        run_type_dict = {"main": "main_run_errors", "fix":"error_fixes_run_errors"}
        
        self.batch = batch
        self.platform = platform
        self.week = week
        self.run_number = run_number
        self.base_url = base_url
        self.client_url = self.base_url + "/graphql"
        self.github_df = github_df
        self.github_token = github_token
        self.strapi_token = strapi_token
        self.columns_dict = columns_dict
        self.default_vals_dict = default_vals_dict
        self.entry_made_into_analysis_table = False
        self.run_type = run_type_dict[run_type]
        self.metrics_detail_dict = metrics_detail_dict
        
        lang_val_dict = {
                lang:{
                    key:[] for key in ["trainee","trainee_id","repo"] + list(self.metrics_detail_dict[lang]["metrics_descriptions"].keys())
                     } for lang in self.metrics_detail_dict.keys()
                             }
        for lang in lang_val_dict.keys():
            lang_val_dict[lang]["status"] = []
        
        self.lang_val_dict = lang_val_dict
        self.cat_list = cat_list


    def get_analysis_data(self, user, repo_name, branch) -> dict:
        """
        Gets analysis data from api
        Returns a dictionary of analysis data with repo meta, repo_analysis_metrics, commit_history and user as keys
        
        Args:
            user (str): user name
            repo_name (str): repo name
            branch (str): branch name

        Returns:
            dict: analysis data
        """
        # get repo meta data and analysis data
        hld = dict()
        repo_meta_repo_analysis = get_repo_meta_repo_analysis(user, self.github_token, repo_name, branch)

        hld["repo_meta"] = repo_meta_repo_analysis["repo_meta"]

        hld["repo_anlysis_metrics"] = repo_meta_repo_analysis["repo_anlysis_metrics"]

        hld["commit_history"] = repo_meta_repo_analysis["commit_history"]


        """if len(trainee_df[trainee_df["trainee_id"]==trainee_id]) == 0:
            print("User: {} not found in trainee_df\n".format(user))
            continue

        trainee = int(trainee_df[trainee_df["trainee_id"]==trainee_id].trainee.values[0])"""

        # get user data from github api
        hld["user"] = get_user(user, self.github_token, api=False)
       
        return hld


    def load_repo_meta_and_repo_to_strapi(self, _dict, hld, repo_meta_error_dict, repo_table_error_dict, assignment_table_error_dict, trainee_id, repo_name, branch, user, trainee, assignments_ids) -> None:
        """
        Loads data to repo and repo_meta tables in strapi

        Args:
            _dict (dict): dictionary of raw data with trainee_id as key
            hld (dict): Raw data retrieved from api
            repo_meta_error_dict (dict): repo meta error dictionary
            repo_table_error_dict (dict): repo table error dictionary
            assignment_table_error_dict (dict): assignment table error dictionary
            trainee_id (str): trainee id of the user
            repo_name (str): repo name
            branch (str): branch name
            user (str): user name
            trainee (int): strapi trainee table index for trainee
            assignments_ids (list): strapi assignment table index for assignments

        Returns:
            None
        """

        client_url = self.client_url
        base_url = self.base_url
        strapi_token = self.strapi_token
        week = self.week
        run_number = self.run_number

        repo_id = None
        
        
        if "error" not in hld["repo_meta"]:
            print("creating repo_table data dict...\n")

            repo_table_dict = {col:(_dict[trainee_id]["repo_meta"][col]
                if col in _dict[trainee_id]["repo_meta"].keys() else None)  for col in repo_df_cols}

            repo_table_dict["week"] = week
            repo_table_dict["trainees"] = trainee
            repo_table_dict["run_number"] = run_number

            #fill in the default values where necessary
            """repo_table_dict = {col:(repo_dict[col]
                if col in _dict[trainee_id]["repo_meta"].keys() and repo_dict[col] != None
                else repo_df_cols_default[col])  for col in repo_df_cols}"""


            print("Repo table data dict created...\n")

            #check if the entry already exists in the repo table
            

            q_query = """query getRepoDetails($html_link: String!,$run_number:String!) 
            {
                repos
                    (
                        pagination: { start: 0, limit: 300 }
                        filters: 
                        {
                            html_url:{eq:$html_link}, 
                            run_number:{ eq: $run_number }
                        }
                    ) 
                    {
                        data 
                        {
                            id
                            attributes
                            {
                                trainees 
                                    {
                                        data 
                                            {
                                                id
                                            }
                                    }
                            }
                        }
                    }
                
            }"""

            q_variables = {"html_link": repo_table_dict["html_url"], "run_number": run_number}
            
            r = send_graphql_query(client_url = client_url, query = q_query, variables= q_variables, token=strapi_token)


            if "error" not in r and "erros" not in r:
                num_entries = len(r["data"]["repos"]["data"])
                if num_entries > 0:
                    print("Repo already exists in repo table...\n")

                    if num_entries > 1:
                        print("More than one entry found for a particular repo in repo table...\n")
                        print("Data intergrity breach, please check...\n")
                        print("System will now exit...\n")
                        sys.exit(1)
                    

                    repo_id = int(r["data"]["repos"]["data"][0]["id"])
                    existing_trainees_resp = r["data"]["repos"]["data"][0]["attributes"]["trainees"]["data"]
                    
                    existing_trainees = [int(trainee["id"]) for trainee in existing_trainees_resp]

                    same_trainee = trainee in existing_trainees
                    
                    
                    if not same_trainee:
                        print("Updating repo table entry repo-trainee relationship with current trainee...\n")
                        
                        repo_table_dict["trainees"] = existing_trainees + [trainee]
                        

                        data = {"trainees": repo_table_dict["trainees"]}

                        q_query = """mutation updateRepo($id: ID!, $data: RepoInput!)
                        {
                            updateRepo(id: $id, data: $data)
                            {
                                data
                                {
                                    id
                                }   
                            }
                        }"""

                        q_variables = {"id": repo_id, "data": data}

                        r = send_graphql_query(client_url = client_url, query = q_query, variables= q_variables, token=strapi_token)


                        if "error" not in r and "errors" not in r:
                            print("Repo table entry trainee relationship updated successfully...\n")

                        else:
                            print("Error updating repo table entry trainee relationship...\n")

                            repo_table_error_dict["trainee_id"].append(trainee_id)
                            repo_table_error_dict["user"].append(user)
                            repo_table_error_dict["repo_name"].append(repo_name)
                            repo_table_error_dict["branch"].append(branch)
                            try:
                                repo_table_error_dict["error"].append(r["error"])
                            except:
                                repo_table_error_dict["error"].append((r["errors"]))

                    
                    #update assignments table
                    print("Updating assignments table...\n")

                    pluralapi = "assignments"

                    q_query = """mutation updateAssignment($id: ID!, $data: AssignmentInput!) 
                        {
                            updateAssignment(id: $id, data: $data) 
                                {
                                    data 
                                    {
                                        id
                                    }
                                }
                        }"""
                    
                    for a_id in assignments_ids:
                        q_variables = {"id": a_id, "data": {"repo": repo_id}}

                        r = send_graphql_query(client_url = client_url, query = q_query, variables= q_variables, token=strapi_token)

                        if "error" not in r and "errors" not in r:
                            print("Assignments table updated...\n")

                        else:
                            print("Error updating assignments table...\n")
                            assignment_table_error_dict["trainee_id"].append(trainee_id)
                            assignment_table_error_dict["user"].append(user)
                            assignment_table_error_dict["repo_name"].append(repo_name)
                            assignment_table_error_dict["branch"].append(branch)
                            assignment_table_error_dict["assignment_id"].append(a_id)
                            try:
                                assignment_table_error_dict["error"].append(r["error"])
                            except:
                                assignment_table_error_dict["error"].append((r["errors"]))
                            
                            


                    
                else:
                    print("Repo does not exist in repo table...\n")

                    #create a new entry in the repo table
                    print("Creating new entry in repo table...\n")

                    q_query = """mutation CreateRepoEntry($data: RepoInput!) 
                        {
                            createRepo(data: $data)
                                {
                                    data
                                    {
                                        id
                                    }
                                }
                        }"""

                    q_variables = {"data": repo_table_dict}

                    r = send_graphql_query(client_url = client_url, query = q_query, variables= q_variables, token=strapi_token)

                    #r = create_table_data_strapi(q_url, token=strapi_token, data=repo_table_dict)

                    if "error" not in r and "errors" not in r:
                        print("Repo table entry created successfully...\n")
                        
                        repo_id = int(r["data"]["createRepo"]["data"]["id"])

                        #update assignments table
                        print("Updating assignments table...\n")

                        pluralapi = "assignments"

                        q_query = """mutation updateAssignment($id: ID!, $data: AssignmentInput!) 
                            {
                                updateAssignment(id: $id, data: $data) 
                                    {
                                        data 
                                        {
                                            id
                                        }
                                    }
                            }"""
                        
                        for a_id in assignments_ids:
                            q_variables = {"id": a_id, "data": {"repo": repo_id}}

                            r = send_graphql_query(client_url = client_url, query = q_query, variables= q_variables, token=strapi_token)

                            if "error" not in r and "errors" not in r:
                                print("Assignments table updated...\n")

                            else:
                                print("Error updating assignments table...\n")
                                assignment_table_error_dict["trainee_id"].append(trainee_id)
                                assignment_table_error_dict["user"].append(user)
                                assignment_table_error_dict["repo_name"].append(repo_name)
                                assignment_table_error_dict["branch"].append(branch)
                                assignment_table_error_dict["assignment_id"].append(a_id)
                                try:
                                    assignment_table_error_dict["error"].append(r["error"])
                                except:
                                    assignment_table_error_dict["error"].append((r["errors"]))

                                

                    

                        
                    else:
                        print("Error creating new entry in repo table...\n")
                        
                        repo_table_error_dict["trainee_id"].append(trainee_id)
                        repo_table_error_dict["user"].append(user)
                        repo_table_error_dict["repo_name"].append(repo_name)
                        repo_table_error_dict["branch"].append(branch)
                        try:
                            repo_table_error_dict["error"].append(r["error"])
                        except:
                            repo_table_error_dict["error"].append((r["errors"]))
                        
                        


                    
                
            else:
                print("Error creating entry in repo table...\n")
                    
                repo_table_error_dict["trainee_id"].append(trainee_id)
                repo_table_error_dict["user"].append(user)
                repo_table_error_dict["repo_name"].append(repo_name)
                repo_table_error_dict["branch"].append(branch)
                try:
                    repo_table_error_dict["error"].append(r["error"])
                except:
                    repo_table_error_dict["error"].append((r["errors"]))
                




            ###############################################################################################
            #get repo meta dict
            
            if repo_id is not None:

                print("Repo meta data dict created\n")
                pluralapi = "github-repos-metas"
                week = week


                # this is commented out because of the decision to not update records in the db but it is left here for future reference and possible use
                ###############################################################################################
                # check for entry in strapi
                # q_url = "{}/api/{}?filters[trainee][id][$eq]={}".format(base_url, pluralapi, trainee)

                # r = get_table_data_strapi(q_url, token=strapi_token)
                

                # check if entry exists
                # r_filtered = [r_i for r_i in r if r_i["attributes"]["trainee_id"] == trainee_id and r_i["attributes"]["run_number"] == run_number and r_i["attributes"]["week"]== week]
                # if len(r_filtered) == 0:
                #     print("Creating repo meta data dict...\n")
                #     print("Entry does not exist in strapi...\n")
                #     print("Creating entry in strapi...\n\n")

                #     repo_meta_dict = {col:(_dict[trainee_id]["repo_meta"][col]
                #         if col in _dict[trainee_id]["repo_meta"].keys() else None)  for col in repo_meta_df_cols}


                #     # if starter_code_ref_basevalues:
                #     #     # normalize the repo data
                #     #     print("Normalizing repo_meta data...\n")
                #     #     repo_dict = normalize_repo_data(repo_meta_dict, starter_code_ref_basevalues)

                #     #fill in the default values where necessary
                #     repo_meta_dict = {col:(repo_meta_dict[col]
                #         if col in _dict[trainee_id]["repo_meta"].keys() and repo_meta_dict[col] != None
                #         else repo_meta_df_cols_default[col])  for col in repo_meta_df_cols}


                #     repo_meta_dict["trainee_id"] = trainee_id
                #     repo_meta_dict["trainee"] = trainee
                #     repo_meta_dict["run_number"] = run_number
                #     repo_meta_dict["repo"] = repo_id
                #     repo_meta_dict["week"] = week

                #     _r = insert_data_strapi(data=repo_meta_dict, pluralapi=pluralapi, token=strapi_token, url=base_url)

                #     if "error" in _r:
                #         print("Error creating entry in repo meta table...\n")
                #         repo_meta_error_dict["trainee_id"].append(trainee_id)
                #         repo_meta_error_dict["user"].append(user)
                #         repo_meta_error_dict["repo_name"].append(repo_name)
                #         repo_meta_error_dict["branch"].append(branch)
                #         repo_meta_error_dict["error"].append(_r["error"])
                        
                
                # else:
                #         print("Error creating entry in repo meta table...\n")
                #         print("Entry already exists in strapi...\n")
                #         repo_meta_error_dict["trainee_id"].append(trainee_id)
                #         repo_meta_error_dict["user"].append(user)
                #         repo_meta_error_dict["repo_name"].append(repo_name)
                #         repo_meta_error_dict["branch"].append(branch)
                #         repo_meta_error_dict["error"].append("Repo meta already exists in repo meta table")

                ###############################################################################################

                
                
                print("Creating repo meta data dict...\n")
                print("Entry does not exist in strapi...\n")
                print("Creating entry in strapi...\n\n")

                repo_meta_dict = {col:(_dict[trainee_id]["repo_meta"][col]
                    if col in _dict[trainee_id]["repo_meta"].keys() else None)  for col in repo_meta_df_cols}


                # if starter_code_ref_basevalues:
                #     # normalize the repo data
                #     print("Normalizing repo_meta data...\n")
                #     repo_dict = normalize_repo_data(repo_meta_dict, starter_code_ref_basevalues)

                #fill in the default values where necessary
                repo_meta_dict = {col:(repo_meta_dict[col]
                    if col in _dict[trainee_id]["repo_meta"].keys() and repo_meta_dict[col] != None
                    else repo_meta_df_cols_default[col])  for col in repo_meta_df_cols}


                repo_meta_dict["trainee_id"] = trainee_id
                repo_meta_dict["trainee"] = trainee
                repo_meta_dict["run_number"] = run_number
                repo_meta_dict["repo"] = repo_id
                repo_meta_dict["week"] = week

                if len(repo_meta_dict["description"]) > 255:
                    repo_meta_dict["description"] = repo_meta_dict["description"][:252] + "..."

                _r = insert_data_strapi(data=repo_meta_dict, pluralapi=pluralapi, token=strapi_token, url=base_url)

                if "error" in _r:
                    print(repo_meta_dict)
                    print("Error creating entry in repo meta table...\n")
                    repo_meta_error_dict["trainee_id"].append(trainee_id)
                    repo_meta_error_dict["user"].append(user)
                    repo_meta_error_dict["repo_name"].append(repo_name)
                    repo_meta_error_dict["branch"].append(branch)
                    repo_meta_error_dict["error"].append(_r["error"])



            else:
                print("Error creating entry in to repo table. Hence repo meta entry is skipped..\n")

        else:
            print("Error retrieving repo data for user: {} and repo: {}\n".format(user, repo_name))
            repo_meta_error_dict["trainee_id"].append(trainee_id)
            repo_meta_error_dict["repo_name"].append(repo_name)
            repo_meta_error_dict["user"].append(user)
            repo_meta_error_dict["branch"].append(branch)
            repo_meta_error_dict["error"].append(hld["repo_meta"])
        
        return repo_id


    def load_user_meta_to_strapi(self, hld, repo_id, user_error_dict, user, repo_name, branch, trainee_id, trainee, _dict) -> None:
        """
        Loads user meta data to strapi

        Args:
            hld (dict): Raw data retrieved from api
            repo_id (str): Repo id
            user_error_dict (dict): Holds user meta data errors
            user (str): User name
            repo_name (str): Repo name
            branch (str): Branch name
            trainee_id (str): trainee id of the user
            trainee (int): strapi trainee table index for trainee
            _dict (dict): dictionary of raw data with trainee_id as key

        Returns:
            None
        """

        base_url = self.base_url
        strapi_token = self.strapi_token
        week = self.week
        run_number = self.run_number

        print("Data for user: {} and repo: {} retrieved\n".format(user, repo_name))

        if "error" not in hld["user"]:
            # get the user data dict
            user_dict = hld["user"]
            pluralapi = "github-user-metas"

            # this is commented out because of a decision to not update records in db but it is left here for future reference and possible use
            ##############################################################################################################
            # check for entry in strapi
            # q_url = "{}/api/{}?filters[trainee][id][$eq]={}".format(base_url,pluralapi, trainee)

            # r = get_table_data_strapi(q_url, token=strapi_token)

            # # check if entry exists
            # r_filtered = [r_i for r_i in r if r_i["attributes"]["trainee_id"] == trainee_id and r_i["attributes"]["run_number"] == run_number and r_i["attributes"]["week"]== week]
            # if len(r_filtered) == 0:
            #     print("Creating user meta data dict...\n")
            #     print("Entry does not exist in strapi...\n")
            #     print("Creating entry in strapi...\n\n")

            #     user_dict = {col:(_dict[trainee_id]["user"][col]
            #         if col in _dict[trainee_id]["user"].keys() else None)  for col in user_df_cols}

            #     #fill in the default values where necessary
            #     user_dict = {col:(user_dict[col]
            #         if col in _dict[trainee_id]["user"].keys() and user_dict[col] != None
            #         else user_df_cols_default[col])  for col in user_df_cols}


            #     user_dict["trainee_id"] = trainee_id
            #     user_dict["trainee"] = trainee
            #     user_dict["run_number"] = run_number
            #     user_dict["week"] = week
            #     user_dict["repo"] = repo_id
                
            #     _r = insert_data_strapi(data=user_dict, pluralapi=pluralapi, token=strapi_token, url=base_url)
                
            #     if "error" in _r:
            #         print("Error creating entry in user meta table...\n")
            #         user_error_dict["trainee_id"].append(trainee_id)
            #         user_error_dict["user"].append(user)
            #         user_error_dict["repo_name"].append(repo_name)
            #         user_error_dict["branch"].append(branch)
            #         user_error_dict["error"].append(_r["error"])
                    

            # else:
            #     print("Error creating entry in user meta table...\n")
            #     print("Entry already exists in user meta table...\n")
            #     user_error_dict["trainee_id"].append(trainee_id)
            #     user_error_dict["user"].append(user)
            #     user_error_dict["repo_name"].append(repo_name)
            #     user_error_dict["branch"].append(branch)
            #     user_error_dict["error"].append("User meta already exists in user meta table")
            ##############################################################################################################
            
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
            
            _r = insert_data_strapi(data=user_dict, pluralapi=pluralapi, token=strapi_token, url=base_url)
            
            if "error" in _r:
                print("Error creating entry in user meta table...\n")
                user_error_dict["trainee_id"].append(trainee_id)
                user_error_dict["user"].append(user)
                user_error_dict["repo_name"].append(repo_name)
                user_error_dict["branch"].append(branch)
                user_error_dict["error"].append(_r["error"])



        else:
            print("Error retrieving user data for user: {} and repo: {}\n".format(user, repo_name))
            user_error_dict["trainee_id"].append(trainee_id)
            user_error_dict["user"].append(user)
            user_error_dict["repo_name"].append(repo_name)
            user_error_dict["branch"].append(branch)
            user_error_dict["error"].append(hld["user"])


    def load_commit_history_to_strapi(self, hld, trainee, trainee_id, _dict, repo_id, commit_history_error_dict, user, repo_name, branch) -> None:
        """
        Loads commit history data to strapi
        
        Args:
            hld (dict): Raw data retrieved from api
            trainee (int): strapi trainee table index for trainee
            trainee_id (str): trainee id of the user
            _dict (dict): dictionary of raw data with trainee_id as key
            repo_id (int): strapi repo table index for repo
            commit_history_error_dict (dict):
            user (str): username of the user
            repo_name (str): name of the repo
            branch (str): branch of the repo
            
        Returns:
            None
        """

        base_url = self.base_url
        strapi_token = self.strapi_token
        week = self.week
        run_number = self.run_number

        if "error" not in hld["commit_history"]:
            # get the repo commit history dict
            repo_commit_history_dict = hld["commit_history"]

            pluralapi = "github-branch-commit-histories"
            
            # this is commented out because of a decision to not update records in the db but it is left here for future reference and possible use
            ###############################################################################################################################
            # check for entry in strapi
            # q_url = "{}/api/{}?filters[trainee][id][$eq]={}".format(base_url, pluralapi, trainee)

            # r = get_table_data_strapi(q_url, token=strapi_token)

            # # check if entry exists
            # r_filtered = [r_i for r_i in r if r_i["attributes"]["trainee_id"] == trainee_id and r_i["attributes"]["run_number"] == run_number and r_i["attributes"]["week"]== week]
            # if len(r_filtered) == 0:
            #     print("Creating repo commit history dict...\n")
            #     print("Entry does not exist in strapi...\n")
            #     print("Creating entry in strapi...\n\n")

            #     commit_history_dict = {col:(_dict[trainee_id]["commit_history"][col]
            #         if col in _dict[trainee_id]["commit_history"].keys() else None)  for col in commit_history_df_cols}

            #     #fill in the default values where necessary
            #     commit_history_dict = {col:(commit_history_dict[col]
            #         if col in _dict[trainee_id]["commit_history"].keys() and commit_history_dict[col] != None
            #         else commit_history_df_cols_default[col])  for col in commit_history_df_cols}

            #     commit_history_dict["trainee_id"] = trainee_id
            #     commit_history_dict["trainee"] = trainee
            #     commit_history_dict["run_number"] = run_number
            #     commit_history_dict["week"] = week
            #     commit_history_dict["repo"] = repo_id

            #     _r = insert_data_strapi(data=commit_history_dict, pluralapi=pluralapi, token=strapi_token, url=base_url)

            #     if "error" in _r:
            #         print("Error creating entry in repo commit history table...\n")
            #         commit_history_error_dict["trainee_id"].append(trainee_id)
            #         commit_history_error_dict["user"].append(user)
            #         commit_history_error_dict["repo_name"].append(repo_name)
            #         commit_history_error_dict["branch"].append(branch)
            #         commit_history_error_dict["error"].append(_r["error"])
                    

            # else:
            #     print("Error creating entry in repo commit history table...\n")
            #     print("Entry already exists in repo commit history table...\n")
            #     commit_history_error_dict["trainee_id"].append(trainee_id)
            #     commit_history_error_dict["user"].append(user)
            #     commit_history_error_dict["repo_name"].append(repo_name)
            #     commit_history_error_dict["branch"].append(branch)
            #     commit_history_error_dict["error"].append("Repo commit history already exists in repo commit history table")
            ###############################################################################################################################


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

            _r = insert_data_strapi(data=commit_history_dict, pluralapi=pluralapi, token=strapi_token, url=base_url)

            if "error" in _r:
                print("Error creating entry in repo commit history table...\n")
                commit_history_error_dict["trainee_id"].append(trainee_id)
                commit_history_error_dict["user"].append(user)
                commit_history_error_dict["repo_name"].append(repo_name)
                commit_history_error_dict["branch"].append(branch)
                commit_history_error_dict["error"].append(_r["error"])   

        else:
            print("Error retrieving repo commit history data for user: {} and repo: {}\n".format(user, repo_name))
            commit_history_error_dict["trainee_id"].append(trainee_id)
            commit_history_error_dict["user"].append(user)
            commit_history_error_dict["repo_name"].append(repo_name)
            commit_history_error_dict["branch"].append(branch)
            commit_history_error_dict["error"].append(hld["commit_history"])


    def populate_lang_val_dict(self, hld, trainee, trainee_id, repo_id, error_dict) -> None:
        """
        Populate the language value dict with the data from the github api

        Args:
            hld (dict): Raw data retrieved from api
            trainee (int): strapi trainee table index for trainee
            trainee_id (str): trainee id of the user
            repo_id (int): strapi repo table index for repo
            error_dict (dict): the error dict

        Returns:
            None
        """
        
        lang_val_dict = self.lang_val_dict
        run_number = self.run_number
        week = self.week

        print("Populating lang val dict...\n")
        
        if "error" not in hld["repo_anlysis_metrics"]:

            for lang in hld["repo_anlysis_metrics"]:
                entry_made = False
                print("Language: {}\n".format(lang))

                if len(hld["repo_anlysis_metrics"][lang]) > 0:
                    lang_val_dict[lang]["status"].append("data_available")
                    
                    print("Data retrieved for language: {}\n".format(lang))

                    for metric in hld["repo_anlysis_metrics"][lang]["repo_summary"]:
                        if metric in self.metrics_detail_dict[lang]["metrics_descriptions"].keys():
                            lang_val_dict[lang][metric].append(hld["repo_anlysis_metrics"][lang]["repo_summary"][metric])
                            entry_made = True
                

                    if entry_made:
                        lang_val_dict[lang]["trainee"].append(trainee)
                        lang_val_dict[lang]["trainee_id"].append(trainee_id)
                        lang_val_dict[lang]["repo"].append(repo_id)
                
                else:
                    print("No data for lang: {}\n".format(lang))
                    lang_val_dict[lang]["status"].append("no_data")
                    lang_val_dict[lang]["trainee"].append(trainee)
                    lang_val_dict[lang]["trainee_id"].append(trainee_id)
                    lang_val_dict[lang]["repo"].append(repo_id)
                    for metric in self.metrics_detail_dict[lang]["metrics_descriptions"].keys():
                        lang_val_dict[lang][metric].append(None)

        
        else:
            print("Error retrieving repo analysis metrics data for user: {}, week: {} and run number: {}\n".format(trainee_id, week, run_number))
            error_dict["trainee_id"].append(trainee_id)
            error_dict["error"].append("Data retrival error:  " + hld["repo_anlysis_metrics"]["error"])

        
        print("Populating lang val dict completed!\n")

  
    def update_lang_val_dict(self) -> None:
        """
        Updates the language value dict with already existing data in the database

        Args:
            None

        Returns:
            None
        """
        strapi_token = self.strapi_token
        week = self.week
        run_number = self.run_number
        lang_val_dict = self.lang_val_dict
        client_url = self.client_url
        
        q_query = """query getAnalysisDetails($week: String!,$run_number:String!) 
                    {
                        githubAnalysisDetails
                            (
                                pagination: { start: 0, limit: 300 }
                                filters: 
                                {
                                    week:{ eq: $week }, 
                                    run_number:{ eq: $run_number }
                                }
                            ) 
                            {
                                data 
                                {
                                    id
                                    attributes
                                    {
                                        trainee 
                                            {
                                                data 
                                                    {
                                                        id
                                                    }
                                            },
                                        repo
                                            {
                                                data
                                                    {
                                                        id
                                                    }
                                            },
                                        trainee_id,
                                        analysis_details,
                                        createdAt,    
                                    }
                                }
                            }
                        
                    }"""

        q_variables = {"week": week, "run_number": run_number}

        r = send_graphql_query(client_url = client_url, query = q_query, variables= q_variables, token=strapi_token)
        
        utc=pytz.UTC
        
        if "error" not in r:
            if len(r["data"]["githubAnalysisDetails"]["data"]) > 0:
                print("Entry/entries found for {} and {} strapi...".format(week, run_number))
                print("Updating lang val dict...\n")

                retrieved_list = []
                for item in r["data"]["githubAnalysisDetails"]["data"]:
                    trainee = item["attributes"]["trainee"]["data"]["id"]
                    trainee_id = item["attributes"]["trainee_id"]
                    repo_id = item["attributes"]["repo"]["data"]["id"]
                    analysis_details = item["attributes"]["analysis_details"]
                    created_at = item["attributes"]["createdAt"]

                    retrieved_list.append({"trainee": trainee, "trainee_id": trainee_id, "repo_id": repo_id, "analysis_details": analysis_details, "created_at": created_at})

                retrieved_list_df = pd.DataFrame(retrieved_list)
                retrieved_list_df["created_at"] = retrieved_list_df["created_at"].apply(lambda date: parser.parse(date).replace(tzinfo=utc))


                retrieved_list_df.sort_values(by=["created_at"], ascending=False, ignore_index=True, inplace=True)
                retrieved_list_df.drop_duplicates(subset=["trainee_id"], keep="first", inplace=True)
                retrieved_list_df.drop(columns=["created_at"], inplace=True)
                retrieved_list_df.reset_index(drop=True, inplace=True)

                for index, row in retrieved_list_df.iterrows():
                    trainee = row["trainee"]
                    trainee_id = row["trainee_id"]
                    repo_id = row["repo_id"]
                    analysis_details = {detail["name"]:detail for detail in row["analysis_details"]}
                    
                    for lang in lang_val_dict:
                        if trainee_id in lang_val_dict[lang]["trainee_id"]:
                            pass
                        else:
                            lang_val_dict[lang]["trainee_id"].append(trainee_id)
                            lang_val_dict[lang]["trainee"].append(trainee)
                            lang_val_dict[lang]["repo"].append(repo_id)

                            if lang in analysis_details:
                                lang_val_dict[lang]["status"].append("data_available")
                                for _dict in analysis_details[lang]["repo_summary"]:
                                    if _dict["name"] in lang_val_dict[lang].keys():
                                        lang_val_dict[lang][_dict["name"]].append(_dict["value"])
                                    else:
                                        print("{} is not in the list of metrics".format(_dict["name"]))
                            else:
                                print("No data for lang: {} for user: {}\n".format(lang, trainee_id))
                                lang_val_dict[lang]["status"].append("no_data")
                                for metric in self.metrics_detail_dict[lang]["metrics_descriptions"].keys():
                                    lang_val_dict[lang][metric].append(None)
                
                print("Updating lang val dict completed!\n")
                
            else:
                print("Entries not found for {} and {} strapi...".format(week, run_number))
                print("No data to update lang val dict...\n")
        
        else:
            print("Error retrieving analysis details for {} and {} strapi...\n".format(week, run_number))
            print(r["error"])
            print("No data to update lang val dict...\n")


    def create_analysis_dict(self)-> None:
        """
        Creates the analysis dict with the data from the lang val dict

        Args:
            None

        Returns:
            None
        """
        week = self.week
        run_number = self.run_number
        batch = self.batch
        lang_val_dict = self.lang_val_dict
            

        # Compute the Analysis Metrics Summary
        print("Computing Analysis Metrics Ranks...\n")

        analysis_dict = {lang:dict() for lang in lang_val_dict.keys()}
        
        for lang in lang_val_dict.keys():
            #if lang_val_dict[lang]["status"][0] == "data_available":
            cat_df = pd.DataFrame(lang_val_dict[lang])
            
            cat_dict = {col:({"max":None, "min":None, "sum":None, "break_points":None}) for col in self.metrics_detail_dict[lang]["metrics_list"]}

            for col in cat_dict:
                if pd.api.types.is_numeric_dtype(cat_df[col]):

                    rev = False
                    series = cat_df[col]
                    series = series.dropna()
                    entry_counts = len(series)
                    cat_dict[col]["entry_counts"] = entry_counts


                    if col == "cc":
                        rev = True

                        # remove zeros from the series
                        # series = series[series != 0]

                    if col in self.metrics_detail_dict[lang]["sum_list"]:
                        cat_dict[col]["break_points"], cat_dict[col]["min"], cat_dict[col]["max"], cat_dict[col]["sum"] = get_break_points(series = series, cat_list=self.cat_list, reverse=rev, _add=True)
                    else:
                        del cat_dict[col]["sum"]
                        cat_dict[col]["break_points"], cat_dict[col]["min"], cat_dict[col]["max"] = get_break_points(series = series, cat_list=self.cat_list, reverse=rev, _add=False)
            
            ranks_list = []
            
            for i, row in cat_df.iterrows():
                rank_dict = {col:None for col in self.metrics_detail_dict[lang]["metrics_list"]}
                
                for col in rank_dict:
                    val = row[col]
                    break_points = cat_dict[col]["break_points"]
                    if val != None and not pd.isna(val) :
                        if col != "cc":
                            rank_dict[col] = get_metric_category(val=val, break_points=break_points, reverse=False)
                        else:
                            rank_dict[col] = get_metric_category(val=val, break_points=break_points, reverse=True)
                    else:
                        rank_dict[col] = get_metric_category(val=-999, break_points=break_points, reverse=False)
                ranks_list.append(rank_dict)
            
            for col in cat_dict:
                if cat_dict[col]["break_points"]:
                    cat_dict[col]["break_points"] = cat_dict[col]["break_points"][:-1]
                
            cat_df["rank"] = ranks_list
            cat_df["week"] = week
            cat_df["run_number"] = run_number
            cat_df["batch"] = batch
            
            
            ########################################################################################################################
        
            # get summary metrics dict

            ########################################################################################################################
            print("Computing Analysis Metrics Summary...\n")
            
            # create summary metrics df
            analysis_dict[lang]["analysis"] = cat_df
            analysis_dict[lang]["summary"] = cat_dict
        
        self.analysis_dict = analysis_dict


    def create_analysis_strapi_records(self) -> None:
        """
        Creates records form analysis dict to be uploaded into strapi

        Args:
            None

        Returns:
            None
        """
        week = self.week
        run_number = self.run_number
        batch = self.batch
        
        analysis_dict = self.analysis_dict
        languages = list(lang for lang in analysis_dict.keys())

        retrieve_summary = {lang:False for lang in languages}
        
        starter_lang = languages[0]

        analysis_summary_dict = {
                                    "week":week, 
                                    "run_number":run_number, 
                                    "batch":batch, 
                                    "summary_details":[]
                                }



        analysis_metrics_list = []
        print("Creating Analysis Detail records...\n")

        for i, row in analysis_dict[starter_lang]["analysis"].iterrows():
            
            analysis_metrics_dict = {
                                        "trainee_id":row["trainee_id"], 
                                        "trainee":int(row["trainee"]), 
                                        "repo":int(row["repo"]), 
                                        "week":row["week"], 
                                        "run_number":row["run_number"], 
                                        "batch":int(row["batch"]), 
                                        "analysis_details":[]
                                    }
            

            for lang in languages:
                
                analysis_hld_dict = dict()
                analysis_hld_list = list()

                if analysis_dict[lang]["analysis"].loc[i]["status"] == "data_available":
                    
                    retrieve_summary[lang] = True

                    for col in self.metrics_detail_dict[lang]["metrics_descriptions"]:
                        name = col
                        value = analysis_dict[lang]["analysis"].loc[i, col]
                        if value.__class__.__name__ == "int64":
                            value = int(value)
                        if value.__class__.__name__ == "float64":
                            value = float(value)
                        
                        desc = self.metrics_detail_dict[lang]["metrics_descriptions"][col]
                        
                        if col in analysis_dict[lang]["analysis"].loc[i, "rank"] and analysis_dict[lang]["analysis"].loc[i, "rank"][col]:
                            rank = analysis_dict[lang]["analysis"].loc[i, "rank"][col]
                            analysis_hld_list.append({"name":name, "value":value, "rank":rank, "desc":desc})
                        else:
                            analysis_hld_list.append({"name":name, "value":value, "desc":desc})
                    
                    analysis_hld_dict["name"] = lang
                    analysis_hld_dict["repo_summary"] = analysis_hld_list
                    analysis_metrics_dict["analysis_details"].append(analysis_hld_dict)
                    analysis_metrics_list.append(analysis_metrics_dict)
                    

        print("Creating Analysis Detail records completed!\n")

        print("Creating analysis summary records...\n")


        for lang in retrieve_summary:
            if retrieve_summary[lang]:
                summary_hld_dict = dict()
                summary_hld_list = list()
                

                for col, val in analysis_dict[lang]["summary"].items():
                    if col != "status":
                        name = col
                        val_list = []
                        for m, v in val.items():
                            val_list.append({"name":m, "value":v})
                        desc = self.metrics_detail_dict[lang]["metrics_descriptions"][col]
                        
                        summary_hld_list.append({"name":name, "value":val_list,"desc":desc})
                    
                summary_hld_dict["name"] = lang
                summary_hld_dict["summary_details"] = summary_hld_list
                analysis_summary_dict["summary_details"].append(summary_hld_dict)
        
        print("Creating analysis summary records completed!\n")

        # wipe out the analysis_dict in memomry and repopulate with retrieved records
        analysis_dict = {
                            "analysis":analysis_metrics_list,
                            "analysis_summary":[analysis_summary_dict]
                        }

        
        self.analysis_dict = analysis_dict  


    def save_errors(self, commit_history_error_dict, user_error_dict, repo_meta_error_dict, assignment_table_error_dict, analysis_retrival_error_dict, analysis_enrty_error_dict, analysis_summary_entry_error_dict) -> None:
        """
        Saves errors encountered during uploads

        Args:
            commit_history_error_dict: dictionary of errors encountered during commit history upload
            user_error_dict: dictionary of errors encountered during user upload
            repo_meta_error_dict: dictionary of errors encountered during repo meta upload 
            assignment_table_error_dict: dictionary of errors encountered during assignment table updates
            analysis_retrival_error_dict: dictionary of errors encountered during analysis retrieval
            analysis_enrty_error_dict: dictionary of errors encountered during analysis data uploads
            analysis_summary_entry_error_dict: dictionary of errors encountered during analysis summary data uploads

        Returns:
            None
        """
        
        week = self.week
        run_number = self.run_number
        platform = self.platform
        batch = self.batch
        run_type = self.run_type

        
        now = datetime.now()
        output_dir = "data/run_errors/batch{}/{}/{}/run{}/{}/".format(batch,platform,week,run_number,run_type) + now.strftime("%Y-%m-%d")

        
        # Save users with Github User analysis error
        if len(user_error_dict["user"]) > 0:

            print("Saving trainees with Github User analysis errors\n")
            user_error_df = pd.DataFrame(user_error_dict)

            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

            
            user_error_df.to_csv("{}/b{}_{}_trainees_with_github_user_analysis_error_{}.csv".format(output_dir, batch, week, now.strftime("%Y_%m_%d__%H_%M_%S")), index=False)
            

        
        
        # Save users with Github Repo analysis error
        if len(repo_meta_error_dict["user"]) > 0:

            print("Saving trainees with Github Repo meta analysis errors\n")
            repo_meta_error_df = pd.DataFrame(repo_meta_error_dict)

            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

            repo_meta_error_df.to_csv("{}/b{}_{}_trainees_with_github_repo_meta_analysis_error_{}.csv".format(output_dir, batch, week, now.strftime("%Y_%m_%d__%H_%M_%S")), index=False)



        # Save users with commit history error
        if len(commit_history_error_dict["user"]) > 0:
                
                print("Saving trainees with commit history errors\n")
                commit_history_error_df = pd.DataFrame(commit_history_error_dict)

                if not os.path.isdir(output_dir):
                    os.makedirs(output_dir)

                commit_history_error_df.to_csv("{}/b{}_{}_trainees_with_commit_history_error_{}.csv".format(output_dir, batch, week, now.strftime("%Y_%m_%d__%H_%M_%S")), index=False)
        
       
        # Save users with  Repo analysis retrieval error
        if len(analysis_retrival_error_dict["trainee_id"]) > 0:

            print("Saving trainees with Github Repo analysis retrieval errors\n")
            analysis_retrival_error_df = pd.DataFrame(analysis_retrival_error_dict)

            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

            analysis_retrival_error_df.to_csv("{}/b{}_{}_trainees_with_analysis_retrival_error_{}.csv".format(output_dir, batch, week, now.strftime("%Y_%m_%d__%H_%M_%S")), index=False)
            

        # Save users with  Repo analysis retrieval error
        if len(analysis_enrty_error_dict["trainee_id"]) > 0:

            print("Saving trainees with Github Repo analysis retrieval errors\n")
            analysis_enrty_error_df = pd.DataFrame(analysis_enrty_error_dict)

            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

            analysis_enrty_error_df.to_csv("{}/b{}_{}_trainees_with_analysis_entry_error_{}.csv".format(output_dir, batch, week, now.strftime("%Y_%m_%d__%H_%M_%S")), index=False)
            

        # Save analysis summary entry with error
        if len(analysis_summary_entry_error_dict["week"]) > 0:

            print("Saving trainees with Github Repo analysis records entry into strapi errors\n")
            analysis_summary_entry_error_df = pd.DataFrame(analysis_summary_entry_error_dict)

            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

            analysis_summary_entry_error_df.to_csv("{}/b{}_{}_analysis_summary_error_{}.csv".format(output_dir, batch, week, now.strftime("%Y_%m_%d__%H_%M_%S")), index=False)
            

        
        # save users with assignment data update error
        if len(assignment_table_error_dict["user"]) > 0:
            print("Saving trainees with assignment data update error\n")
            assignment_table_error_df = pd.DataFrame(assignment_table_error_dict)

            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

            assignment_table_error_df.to_csv("{}/b{}_{}_trainees_with_assignment_data_update_error_{}.csv".format(output_dir, batch, week, now.strftime("%Y_%m_%d__%H_%M_%S")), index=False)

        
        
        if len(user_error_dict["user"]) == 0 and len(repo_meta_error_dict["user"]) == 0 and len(analysis_retrival_error_dict["trainee_id"]) == 0 and len(analysis_enrty_error_dict["trainee_id"]) == 0 and len(analysis_summary_entry_error_dict["week"]) == 0 and len(commit_history_error_dict["user"]) == 0:
            print("No errors found\n\n")  


    def load_entries_to_strapi(self, error_dict, pluralapi, entry_list) -> None:
        """
        Loads entries to strapi

        Args:
            error_dict (dict): Dictionary to store errors
            pluralapi (str): Pluralapi for strapi table into which entries are to be loaded
            entry_list (list): List of records to be loaded to strapi

        Returns:
            None
        """
        base_url = self.base_url
        strapi_token = self.strapi_token
        week = self.week
        run_number = self.run_number

        print("Loading entries to {}...\n".format(pluralapi))


        for entry in entry_list:
            print("Loading data into strapi...\n")

            # this is commented out because of a decission to not update records in the db but it is left here for future reference or need

            ################################################################################################################
            # check if entry exists
            # print("Checking if entry exists...\n")
            
            # try:
            #     q_url = "{}/api/{}?filters[week][$eq]={}&filters[trainee_id][$eq]={}&filters[run_number][$eq]={}".format(base_url, pluralapi, week, entry["trainee_id"], run_number)
            # except:
            #     q_url = "{}/api/{}?filters[week][$eq]={}&filters[run_number][$eq]={}".format(base_url, pluralapi, week, run_number)
            
            # r_list = get_table_data_strapi(q_url, token=strapi_token)
                                                

            # if len(r_list) > 0: 
            #     if "error" not in r_list[0]:
            #         print("Entry already exists for user: {} for week: {}\n".format(entry["trainee_id"], week))
            #         print("Updating entry...\n")

            #         # update entry
            #         r = update_data_strapi(data=entry, pluralapi=pluralapi, token=strapi_token, entry_id=r_list[0]["id"], url=base_url)

            #         if "error" in r:
                        
            #             if "trainee_id" in entry:
            #                 print("Error updating entry for user: {} for week: {} and run_number: {} in {}\n".format(entry["trainee_id"], week, entry["run_number"], pluralapi))
            #                 error_dict["trainee_id"].append(r["trainee_id"])
            #             else:
            #                 print("Error updating entry for week: {} and run_number: {} in {}\n".format(week, entry["run_number"], pluralapi))

            #             if "week" in error_dict:
            #                 error_dict["week"].append(week)

            #             error_dict["entry_data"].append({"id": r_list[0]["id"], "data": entry})
            #             error_dict["error"].append("Update error: " + str(r["error"]))

            #     else:
            #         if "trainee_id" in entry:
            #             print("Error in checking if entry exists for user: {} for week: {} and run_number: {} in {}\n".format(entry["trainee_id"], week, entry["run_number"], pluralapi))
            #             error_dict["trainee_id"].append(entry["trainee_id"])
            #         else:
            #             print("Error in checking if entry exists for week: {} and run_number: {} in {}\n".format(week, run_number, pluralapi))
                    
            #         if "week" in error_dict:
            #             error_dict["week"].append(week)
                    
            #         error_dict["entry_data"].append({"data": entry})
            #         error_dict["error"].append("Entry existence check error: " + str(r_list["error"]))
            # else:
                # if "trainee_id" in entry:
                #     print("Entry does not exist for user: {}, week: {} and run_number: {} in {}\n".format(entry["trainee_id"], week, entry["run_number"], pluralapi))
                # else:
                #     print("Entry does not exist for week: {} and run_number: {} in {}\n".format(week, run_number, pluralapi))
            ################################################################################################################

            # create entry in strapi
            print("Creating entry in strapi...\n")
            r = insert_data_strapi(data=entry, pluralapi=pluralapi, token=strapi_token, url=base_url)
            
            if "error" in r:
                
                if "trainee_id" in entry:
                    print("Error creating entry for user: {} for week: {} and run_number: {} in {}\n".format(entry["trainee_id"], week, entry["run_number"], pluralapi))
                    error_dict["trainee_id"].append(entry["trainee_id"])
                else:
                    print("Error creating entry for week: {} and run_number: {} in {}\n".format(week, run_number, pluralapi))

                if "week" in error_dict:
                    error_dict["week"].append(week)

                error_dict["entry_data"].append({"data": entry})
                error_dict["error"].append("Insert error: " + str(r["error"]))

        print("Done loading entries to {}\n".format(pluralapi))


    def run_to_load(self) -> None:
        """
        Runs the load process

        Args:
            None

        Returns:
            None
        """
        counter = 0
        repo_table_error_dict = {"trainee_id":[], "user":[], "repo_name":[], "branch":[], "error":[]}
        assignment_table_error_dict = {"trainee_id":[], "user":[], "repo_name":[], "branch":[], "assignment_id":[], "error":[]}
        user_error_dict = {"trainee_id":[], "user":[], "repo_name":[], "branch":[], "error":[]}
        repo_meta_error_dict = {"trainee_id":[], "user":[], "repo_name":[], "branch":[], "error":[]}
        commit_history_error_dict = {"trainee_id":[], "user":[], "repo_name":[], "branch":[], "error":[]}
        analysis_retrival_error_dict = {"trainee_id":[], "error":[]}
        analysis_enrty_error_dict = {"trainee_id":[], "entry_data":[], "error":[]}
        analysis_summary_entry_error_dict = {"week":[], "entry_data":[], "error":[]}


        github_df  = self.github_df

        github_df["trainee"] = github_df.trainee.astype(int)

        for i, row in github_df.iterrows():
            counter += 1
            user = row["gh_username"]
            repo_name = row["repo_name"]
            trainee_id = row["trainee_id"]
            run_number = row["run_number"]
            branch = row["branch_name"]
            trainee = row["trainee"]
            assignments_ids = row["assignments_ids"]
            repo_id = None

            print("\n\n\nRetrieving data for user: {} and repo: {}...".format(user, repo_name))
            print("\n")
            hld = dict()
            if counter != 0 and counter%5 == 0:
                print(user)
                print("Sleeping for 20 seconds\n")
                time.sleep(20)
                print("Resumed...\n")

            # get repo meta data and analysis data
            hld = self.get_analysis_data(user, repo_name, branch)

            _dict = dict()
            _dict[trainee_id] =  hld
            
            counter += 1

            # load repo and repo meta data into strapi
            repo_id = self.load_repo_meta_and_repo_to_strapi(_dict, hld, repo_meta_error_dict, repo_table_error_dict, assignment_table_error_dict, trainee_id, repo_name, branch, user, trainee, assignments_ids)

            if repo_id is not None:
                # load repo_user_meta
                self.load_user_meta_to_strapi(hld, repo_id, user_error_dict, user, repo_name, branch, trainee_id, trainee, _dict)

                # load commit history
                self.load_commit_history_to_strapi(hld, trainee, trainee_id, _dict, repo_id, commit_history_error_dict, user, repo_name, branch)
                
                self.populate_lang_val_dict(hld, trainee, trainee_id, repo_id, error_dict=analysis_retrival_error_dict)

            else:
                print("Error creating entry in to repo table. Hence other entries are skipped..\n")
                continue
        
        self.update_lang_val_dict()
        self.create_analysis_dict()
        self.create_analysis_strapi_records()

        # load analysis data into strapi
        self.load_entries_to_strapi(error_dict=analysis_enrty_error_dict, pluralapi="github-analysis-details", entry_list=self.analysis_dict["analysis"])

        # load analysis summary data into strapi
        self.load_entries_to_strapi(error_dict=analysis_summary_entry_error_dict, pluralapi="github-analysis-summaries", entry_list=self.analysis_dict["analysis_summary"])

        # save errors
        self.save_errors(commit_history_error_dict, user_error_dict, repo_meta_error_dict, assignment_table_error_dict, analysis_retrival_error_dict, analysis_enrty_error_dict, analysis_summary_entry_error_dict)

