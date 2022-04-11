import json
import os
import sys
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from datetime import datetime, timedelta
import pandas as pd

curdir = os.path.dirname(os.path.realpath(__file__))
cpath = os.path.dirname(curdir)
if not cpath in sys.path:
    sys.path.append(cpath)

from modules.Category_Dict import Metrics_Summary_Dict
from modules.analyzer_utils import get_df, get_df_dict, get_github_analysis_dict, get_id_userid_df, get_metric_summary_dict, get_rank_dict, get_repo_df_dict, get_repo_names
from modules.strapi_methods import get_table_data_strapi, upload_to_strapi


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

def get_var_from_json(path_to_json:str, var_name:str):
    """
    Gets the variable from the json file

    Args:
        path_to_json (str): path to the json file
        var_name (str): variable name (key)
    """

    if os.path.exists(path_to_json):
        with open(path_to_json, "r") as f:
            try:
                j_dict = json.load(f)
                var_ = j_dict[var_name]
            except:
                print("Error: could not load json file")
                var_ = None
    else:
        print("Error: json file does not exist")
        var_ = None
    return var_

def get_github_token(path_to_json=".env/secret.json", var_name="github_token")->str:
    """
    Gets the github token from the json file

    Args:
        ti (TaskInstance): TaskInstance object
    
    Returns:
        str: github token
    """
    github_token = get_var_from_json(path_to_json=path_to_json, var_name=var_name)
    return github_token

def get_trainee_dict(ti)->dict:
    """
    Gets the trainee data from strapi and store it in a dictionary

    Args:
        ti (TaskInstance): TaskInstance object
    
    Returns:
        dict: trainee data dictionary
    """
    trainee_dict = get_table_data_strapi("trainees")
    return trainee_dict



def exit_with_error(error_message)->None:
    """
    Prints error message and exits the program
    
    Args:
        error_message (str): error message to print
        
    Returns:
        None
    """
    print(error_message)
    sys.exit(1)

def exit_with_error_trainee(error_message="Error: trainee data was not returned")->None:
    """
    Prints error message and exits the program
    
    Args:
        error_message (str): error message to print
        
    Returns:
        None
    """
    exit_with_error(error_message=error_message)

def exit_with_error_github_token(error_message="Error: github token was not returned")->None:
    """
    Prints error message and exits the program
    
    Args:
        error_message (str): error message to print
        
    Returns:
        None
    """
    exit_with_error(error_message=error_message)


def exit_with_error_token(error_message="Error: token was not returned")->None:
    """
    Prints error message and exits the program
    
    Args:
        error_message (str): error message to print
        
    Returns:
        None
    """
    print(error_message)
    sys.exit(1)


def choose_path_after_trainee_data(ti)->str:
    """
    Chooses the path to the next DAG depending on the trainee data
    
    Args:
        ti (TaskInstance): TaskInstance object
        
    Returns:
        str: path to the next DAG
    """
    # check if trainee_dict was returned
    trainee_dict = ti.xcom_pull(task_ids="get_trainee_dict_")
    if "error" not in trainee_dict:
        return "get_trainee_df_"
    else:
        return "exit_with_error_"

def choose_path_after_github_token(ti)->str:
    """
    Chooses the path to the next DAG depending on the github token
    
    Args:
        ti (TaskInstance): TaskInstance object
        
    Returns:
        str: path to the next DAG
    """
    # check if github_token was returned
    github_token = ti.xcom_pull(task_ids="get_github_token_")
    if github_token is not None:
        return "get_trainee_dict_"
    else:
        return "exit_with_error_token_"


def get_trainee_df(ti)->pd.DataFrame:
    """
    Gets the trainee data from the API and stores it in a dataframe

    Args:
        ti (TaskInstance): TaskInstance object
    
    Returns:
        pd.DataFrame: trainee dataframe
    """
    trainee_dict = ti.xcom_pull(task_ids="get_trainee_dict_")
    trainee_df_dict = get_id_userid_df(data_dict=trainee_dict).to_json()
    return json.loads(trainee_df_dict)


def read_data()->pd.DataFrame:
    """
    Reads in the trainee data data from csv files
    
    Args:
        None
        
    Returns:
        None
    """
    # read in the data
    dt_user = pd.read_csv("data/github_usernames.csv")
    dt_repo = pd.read_csv("data/github_repos_wk1.csv")
    github_df = dt_user.merge(dt_repo, on="userId")
    github_df_dict = github_df.to_json()
    return json.loads(github_df_dict)


def get_analysis_dict(ti)->dict:
    """
    Gets the analysis data from the API and store it in a dictionary

    Args:
        ti (TaskInstance): TaskInstance object
    
    Returns:
        dict: analysis data dictionary
    """
    github_df_dict = ti.xcom_pull(task_ids="read_data_")
    github_df = pd.DataFrame(github_df_dict)
    github_analysis_dict = get_github_analysis_dict(github_df=github_df)
    return github_analysis_dict


def get_userid_list(ti)->list:
    """
    Gets the list of userIds from the trainee data

    Args:
        ti (TaskInstance): TaskInstance object
    
    Returns:
        list: list of userIds
    """
    github_df_dict = ti.xcom_pull(task_ids="read_data_")
    github_df = pd.DataFrame(github_df_dict)
    userid_list = github_df["userId"].tolist()
    return userid_list


def get_repo_name_list(ti)->list:
    """
    Gets the list of repo names from the trainee data

    Args:
        ti (TaskInstance): TaskInstance object
    
    Returns:
        list: list of repo names
    """
    github_analysis_dict = ti.xcom_pull(task_ids="get_analysis_dict_")
    userid_list = ti.xcom_pull(task_ids="get_userid_list_")
    repo_name_list = get_repo_names(userid_list=userid_list, results_dict=github_analysis_dict, key="repo_meta")
    return  repo_name_list


def get_category_dict(ti)->dict:
    """
    Gets the category data from the API and store it in a dictionary

    Args:
        ti (TaskInstance): TaskInstance object
    
    Returns:
        dict: category data dictionary
    """
    github_analysis_dict = ti.xcom_pull(task_ids="get_analysis_dict_")
    cat_dict = Metrics_Summary_Dict(metrics_list=metrics_list, github_analysis_dict=github_analysis_dict).get_metrics_summary_dict()
    return cat_dict


def get_rank_dictn(ti)->dict:
    """
    Gets the rank data from the API and store it in a dictionary

    Args:
        ti (TaskInstance): TaskInstance object
    
    Returns:
        dict: rank data dictionary
    """
    github_analysis_dict = ti.xcom_pull(task_ids="get_analysis_dict_")
    cat_dict = ti.xcom_pull(task_ids="get_category_dict_")
    rank_dict = get_rank_dict( github_analysis_dict=github_analysis_dict, cat_dict=cat_dict)
    return rank_dict


def get_updated_get_analysis_dict(ti)->dict:
    """
    Gets the updated analysis data from the API and store it in a dictionary

    Args:
        ti (TaskInstance): TaskInstance object
    
    Returns:
        dict: updated analysis data dictionary
    """
    github_analysis_dict = ti.xcom_pull(task_ids="get_analysis_dict_")
    rank_dict = ti.xcom_pull(task_ids="get_rank_dict_")
    
    for _id,ranks in rank_dict.items():
        github_analysis_dict[_id]["metrics_rank"] = ranks
    return github_analysis_dict


def get_user_df(ti)->pd.DataFrame:
    """
    Gets the user data from the API and store it in a dataframe

    Args:
        ti (TaskInstance): TaskInstance object
    
    Returns:
        pd.DataFrame: user dataframe
    """
    github_analysis_dict = ti.xcom_pull(task_ids="get_updated_get_analysis_dict_")
    userid_list = ti.xcom_pull(task_ids="get_userid_list_")
    trainee_df_dict = ti.xcom_pull(task_ids="get_trainee_df_")
    trainee_df = pd.DataFrame(trainee_df_dict)

    # get the user dataframe
    user_dict = get_df_dict(user_df_cols, "user", userid_list, github_analysis_dict)
    user_df = get_df("week1", user_dict).merge(trainee_df, on="userId")
    # drop userid column
    user_df.drop(["userId"],axis=1, inplace=True)
    user_df_dict = user_df.to_json()
    return json.loads(user_df_dict)


def get_repo_meta_df(ti)->pd.DataFrame:
    """
    Gets the repo meta data from the API and store it in a dataframe

    Args:
        ti (TaskInstance): TaskInstance object
    
    Returns:
        pd.DataFrame: repo meta dataframe
    """
    github_analysis_dict = ti.xcom_pull(task_ids="get_updated_get_analysis_dict_")
    repo_name_list = ti.xcom_pull(task_ids="get_repo_name_list_")
    trainee_df_dict = ti.xcom_pull(task_ids="get_trainee_df_")
    trainee_df = pd.DataFrame(trainee_df_dict)
    userid_list = ti.xcom_pull(task_ids="get_userid_list_")

    # get the repo meta data dataframe
    repo_meta_dict = get_repo_df_dict(repo_df_cols, "repo_meta", userid_list, repo_name_list, github_analysis_dict)
    repo_meta_df = get_df("week1", repo_meta_dict).merge(trainee_df, on="userId")
    # drop userid column
    repo_meta_df.drop(["userId"],axis=1, inplace=True)
    repo_meta_df_dict = repo_meta_df.to_json()
    return json.loads(repo_meta_df_dict)


def get_repo_analysis_df(ti)->pd.DataFrame:
    """
    Gets the repo analysis data from the API and store it in a dataframe

    Args:
        ti (TaskInstance): TaskInstance object
    
    Returns:
        pd.DataFrame: repo analysis dataframe
    """
    github_analysis_dict = ti.xcom_pull(task_ids="get_updated_get_analysis_dict_")
    trainee_df_dict = ti.xcom_pull(task_ids="get_trainee_df_")
    trainee_df = pd.DataFrame(trainee_df_dict)
    userid_list = ti.xcom_pull(task_ids="get_userid_list_")

   # get repo analysis dataframe
    repo_analysis_dict = get_df_dict(repo_analysis_df_cols, "repo_anlysis_metrics", userid_list, github_analysis_dict)
    repo_analysis_df = get_df("week1", repo_analysis_dict).merge(trainee_df, on="userId")
    # drop userid column
    repo_analysis_df.drop(["userId"],axis=1, inplace=True)
    repo_analysis_df_dict = repo_analysis_df.to_json()
    return json.loads(repo_analysis_df_dict)


def get_repo_metrics_df(ti)->pd.DataFrame:
    """
    Gets the repo metrics data from the API and store it in a dataframe

    Args:
        ti (TaskInstance): TaskInstance object
    
    Returns:
        pd.DataFrame: repo metrics dataframe
    """
    github_analysis_dict = ti.xcom_pull(task_ids="get_updated_get_analysis_dict_")
    trainee_df_dict = ti.xcom_pull(task_ids="get_trainee_df_")
    trainee_df = pd.DataFrame(trainee_df_dict)
    userid_list = ti.xcom_pull(task_ids="get_userid_list_")

    # get repo metrics dataframe
    repo_metrics_dict = get_df_dict(repo_metrics_cols, "metrics_rank", userid_list, github_analysis_dict)
    repo_metrics_df = get_df("week1", repo_metrics_dict).merge(trainee_df, on="userId")
    # drop userid column
    repo_metrics_df.drop(["userId"],axis=1, inplace=True)
    repo_metrics_df_dict = repo_metrics_df.to_json()
    return json.loads(repo_metrics_df_dict)


def get_metrics_summary_df(ti)->pd.DataFrame:
    """
    Gets the metrics summary data from the API and store it in a dataframe

    Args:
        ti (TaskInstance): TaskInstance object
    
    Returns:
        pd.DataFrame: metrics summary dataframe
    """
    cat_dict = ti.xcom_pull(task_ids="get_category_dict_")

    # metrics summary dataframe
    metrics_summary_dict = get_metric_summary_dict(cat_dict)
    metrics_summary_df = get_df("week1", metrics_summary_dict)
    metrics_summary_df_dict = metrics_summary_df.to_json()
    return json.loads(metrics_summary_df_dict)



def get_strapi_table_pairing(ti)->dict:
    """
    Gets the strapi table pairing from the API and store it in a dictionary

    Args:
        ti (TaskInstance): TaskInstance object
    
    Returns:
        dict: strapi table pairing dictionary
    """
    metrics_summary_df = ti.xcom_pull(task_ids="get_metrics_summary_df_")
    repo_meta_df = ti.xcom_pull(task_ids="get_repo_meta_df_")
    repo_analysis_df = ti.xcom_pull(task_ids="get_repo_analysis_df_")
    repo_metrics_df = ti.xcom_pull(task_ids="get_repo_metrics_df_")
    user_df = ti.xcom_pull(task_ids="get_user_df_")

    strapi_table_pairing = {
                            "github-metrics-summaries":metrics_summary_df, "github-repo-metas":repo_meta_df, 
                            "github-repo-metrics":repo_analysis_df, "github-repo-metric-ranks":repo_metrics_df,
                            "github-user-metas":user_df
                            }
    return strapi_table_pairing

def upload_into_strapi_tables(ti)->None:
    """
    Uploads the data into strapi tables

    Args:
        ti (TaskInstance): TaskInstance object
    
    Returns:
        None
    """
    strapi_table_pairing = ti.xcom_pull(task_ids="get_strapi_table_pairing_dict_")
    strapi_table_pairing = {k:pd.DataFrame(v) for k,v in strapi_table_pairing.items()}
    upload_to_strapi(strapi_table_pairing, token=False)



DAG_CONFIG = {
    'depends_on_past': False,
    'start_date': datetime(2021, 3, 1),
    'email': ['michael@10acadey.org'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 5,
    'owner' : 'Tenx',
    'retry_delay': timedelta(minutes=1),
}

with DAG("github_analyzer", # Dag id
         default_args=DAG_CONFIG,
         catchup=False,
         schedule_interval='*/15 * * * * '
        ) as dag: # DAG object
    get_trainee_dict_ = PythonOperator(
            task_id="get_trainee_dict_",
            python_callable= get_trainee_dict
        )
    get_github_token_ = PythonOperator(
            task_id="get_github_token_",
            python_callable= get_github_token
        )
    choose_path_after_trainee_data_ = BranchPythonOperator( 
            task_id="choose_path_after_trainee_data_",
            python_callable= choose_path_after_trainee_data
        )
    choose_path_after_github_token_ = BranchPythonOperator( 
            task_id="choose_path_after_github_token_",
            python_callable= choose_path_after_github_token
        )
    exit_with_error_trainee_ = PythonOperator(
            task_id="exit_with_error_trainee_",
            python_callable= exit_with_error_trainee
        )
    exit_with_error_token_ = PythonOperator(
            task_id="exit_with_error_token_",
            python_callable= exit_with_error_github_token
        )
    get_trainee_df_ = PythonOperator(
            task_id="get_trainee_df_",
            python_callable= get_trainee_df
        )
    read_data_ = PythonOperator(
            task_id="read_data_",
            python_callable= read_data
        )
    get_analysis_dict_ = PythonOperator(
            task_id="get_analysis_dict_",
            python_callable= get_analysis_dict
        )
    get_userid_list_ = PythonOperator(
            task_id="get_userid_list_",
            python_callable= get_userid_list
        )
    get_repo_name_list_ = PythonOperator(
            task_id="get_repo_name_list_",
            python_callable= get_repo_name_list
        )
    get_category_dict_ = PythonOperator(
            task_id="get_category_dict_",
            python_callable= get_category_dict
        )
    get_rank_dict_ = PythonOperator(
            task_id="get_rank_dict_",
            python_callable= get_rank_dictn
        )
    get_updated_get_analysis_dict_ = PythonOperator(
            task_id="get_updated_get_analysis_dict_",
            python_callable= get_updated_get_analysis_dict
        )
    get_user_df_ = PythonOperator(
            task_id="get_user_df_",
            python_callable= get_user_df
        )
    get_repo_meta_df_ = PythonOperator(
            task_id="get_repo_meta_df_",
            python_callable= get_repo_meta_df
        )
    get_repo_analysis_df_ = PythonOperator(
            task_id="get_repo_analysis_df_",
            python_callable= get_repo_analysis_df
        )
    get_repo_metrics_df_ = PythonOperator(
            task_id="get_repo_metrics_df_",
            python_callable= get_repo_metrics_df
        )
    get_metrics_summary_df_ = PythonOperator(
            task_id="get_metrics_summary_df_",
            python_callable= get_metrics_summary_df
        )
    get_strapi_table_pairing_dict_ = PythonOperator(
            task_id="get_strapi_table_pairing_dict_",
            python_callable= get_strapi_table_pairing
        )
    upload_into_strapi_tables_ = PythonOperator(
            task_id="upload_into_strapi_tables_",
            python_callable= upload_into_strapi_tables
        )

    get_github_token_ >> choose_path_after_github_token_ >> exit_with_error_token_
    
    choose_path_after_github_token_ >> get_trainee_dict_ >> choose_path_after_trainee_data_ >> exit_with_error_trainee_
    
    choose_path_after_trainee_data_ >> get_trainee_df_ >> read_data_ >> get_userid_list_ >> get_analysis_dict_ \
    >> get_repo_name_list_ >> get_category_dict_ >> get_rank_dict_ >> get_updated_get_analysis_dict_ \
    >> [get_user_df_, get_repo_meta_df_, get_repo_analysis_df_, get_repo_metrics_df_, get_metrics_summary_df_] \
    >> get_strapi_table_pairing_dict_ >> upload_into_strapi_tables_ 
    
    