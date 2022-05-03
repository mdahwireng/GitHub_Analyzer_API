import json
import pandas as pd
import requests
import time
import os
import sys

from app import get_user, single_repos_meta_single_repos_pyanalysis

github_token = None

if os.path.exists(".env/secret.json"):
    
    with open(".env/secret.json", "r") as s:
        secrets = json.load(s)
        github_token = secrets["github_token"]

if os.path.exists(".env/env_var.json"):
    with open(".env/env_var.json", "r") as e:
        env_var = json.load(e)
        host = env_var["host"]
        port = env_var["port"]
        api_root = "http://{}:{}/".format(host, port)


def get_id_userid_df(data_dict)->pd.DataFrame:
    """
    Gets the id and userid dataframe for the given data dict.
    Returns the id and trainee_id dataframe.

    Args:
        data_dict (dict): The data dict.
        
    Returns:
        pd.DataFrame: The id and trainee_id dataframe.
    """
    df_dict = {"trainee":[d["id"] for d in data_dict],
               "trainee_id": [d["attributes"]["trainee_id"] for d in data_dict],
               "email": [d["attributes"]["email"] for d in data_dict]}
    df = pd.DataFrame(df_dict)
    return df



def get_user_meta_url(api_root, username, token)->str:
    """
    Creates the url for the user endpoint taken the api root and the username.
    Returns the url.

    Args:
        api_root (str): The api root.
        username (str): The username.
        token (str): The token.

    Returns:
        str: The url. 
    """
    url = "{}/user/{}/{}".format(api_root, username, token)
    return url


def get_repo_meta_url(api_root, username, repo_name, token)->str:
    """
    Creates the url for the repo meta endpoint taken the api root and the username.
    Returns the url.

    Args:
        api_root (str): The api root.
        username (str): The username.
        repo_name (str): The repo name.
        token (str): The token.

    Returns:
        str: The url. 
    """
    url = "{}/single_repos_meta/{}/{}/{}".format(api_root, username, token, repo_name)
    return url

def get_repo_pymetrics_url(api_root, username, token, repo_name):
    """
    Creates the url for the repo_pymetrics endpoint taken the api root and the username.
    Returns the url.

    Args:
        api_root (str): The api root.
        username (str): The username.
        repo_name (str): The repo name.
        token (str): The token.

    Returns:
        str: The url. 
    """
    url = "{}/single_repos_pyanalysis/{}/{}/{}".format(api_root, username, token, repo_name)
    return url



def get_repo_meta_repo_pymetrics_url(api_root, username, token, repo_name):
    """
    Creates the url for the repo meta and repo_pymetrics endpoint taken the api root and the username.
    Returns the url.

    Args:
        api_root (str): The api root.
        username (str): The username.
        repo_name (str): The repo name.
        token (str): The token.

    Returns:
        str: The url. 
    """
    url = "{}/single_repos_meta_single_repos_pyanalysis/{}/{}/{}".format(api_root, username, token, repo_name)
    return url



def get_user_meta(username, token=github_token ,api_root=api_root)->dict:
    """
    Gets the user meta data for the given username taking the username, token and the api_root.
    Returns the user meta data.

    Args:
        username (str): The username.
        token (str): The token.
        api_root (str): The api root.

    Returns:
        dict: The user meta data.
    """
    user_url = get_user_meta_url(api_root, username, token)
    resp = requests.get(user_url).json()
    return resp


def get_repo_meta(username, repo_name, token=github_token ,api_root=api_root)->dict:
    """
    Gets the repo meta data for the given username taking the username, token and the api_root.
    Returns the repo meta data.
    
    Args:
        username (str): The username.
        repo_name (str): The repo name.
        token (str): The token.
        api_root (str): The api root.
    
    Returns:
        dict: The repo meta data.
    """
    repo_meta_url = get_repo_meta_url(api_root, username, token, repo_name)
    resp = requests.get(repo_meta_url).json()
    return resp

def get_repo_pymetrics(username, repo_name, token=github_token ,api_root=api_root)->dict:
    """
    Gets the repo pymetrics data for the given username taking the username, token and the api_root.
    Returns the repo pymetrics data.

    Args:
        username (str): The username.
        repo_name (str): The repo name.
        token (str): The token.
        api_root (str): The api root.

    Returns:
        dict: The repo pymetrics data.
    """
    repo_pymetrics_url = get_repo_pymetrics_url(api_root, username, token, repo_name)
    resp = requests.get(repo_pymetrics_url).json()
    return resp


def get_repo_meta_repo_pymetrics(username, repo_name, token=github_token ,api_root=api_root)->dict:
    """
    Gets the repo meta and repo pymetrics data for the given username taking the username, token and the api_root.
    Returns the repo meta and repo pymetrics data.

    Args:
        username (str): The username.
        repo_name (str): The repo name.
        token (str): The token.
        api_root (str): The api root.

    Returns:
        dict: The repo meta and repo pymetrics data.
    """
    repo_pymetrics_url = get_repo_meta_repo_pymetrics_url(api_root, username, token, repo_name)
    resp = requests.get(repo_pymetrics_url).json()
    return resp



def get_github_analysis_dict(github_df, token=github_token)->dict:
    """
    Gets the github analysis dict for the given github dataframe and token.
    Returns the github analysis dict.

    Args:
        github_df (pandas.DataFrame): The github dataframe.
        token (str): github personal access token.

    Returns:
        dict: The github analysis dict.
    """    
    _dict = dict()
    counter = 0
    for _, userid, user, repo_name in github_df.itertuples():
        print("Retrieving data for user: {} and repo: {}...".format(user, repo_name))
        hld = dict()
        if counter != 0 and counter%5 == 0:
            print(user)
            print("Sleeping for 60 seconds\n")
            time.sleep(60)
            print("Resumed...\n")

        repo_meta_repo_pyanalysis = single_repos_meta_single_repos_pyanalysis(user, token, repo_name, api=False)

        hld["user"] = get_user(user, token, api=False)
        hld["repo_meta"] = repo_meta_repo_pyanalysis["repo_meta"]

        try:
            hld["repo_anlysis_metrics"] = repo_meta_repo_pyanalysis["analysis_results"]["repo_summary"]
        except:
            hld["repo_anlysis_metrics"] = repo_meta_repo_pyanalysis["analysis_results"]

        _dict[userid] =  hld
        counter += 1
        print("Data for user: {} and repo: {} retrieved\n".format(user, repo_name))
    return json.loads(json.dumps(_dict))

def get_metric_category(val, break_points, reverse=False)->str:
    """
    Gets the metric category for the given val and break points.
    Returns the metric category.

    Args:
        val (int): The val.
        break_points (list): The break points.
        reverse (bool): The reverse flag.

    Returns:
        str: The metric category.
    """
    if int(val) == -999 or float(val) == -999.0:
        return "N/A"
    if sum(break_points) == 0:
        return "top 25%"
    if reverse:
        if val < break_points[0]:
            return "top 25%"

        elif val < break_points[1]:
            return "top 50%"

        elif val < break_points[2]:
            return "top 75%"

        else:
            return "bottom 25%"
    else:
        if val < break_points[0]:
            return "bottom 25%"
    
        elif val < break_points[1]:
            return "top 75%"

        elif val < break_points[2]:
            return "top 50%"

        else:
            return "top 25%"



def get_rank_dict(github_analysis_dict, cat_dict)->dict:
    """
    Gets the rank dict for the given github analysis dict and category dict.
    Returns the rank dict.

    Args:
        github_analysis_dict (dict): The github analysis dict.
        cat_dict (dict): The category dict.

    Returns:
        dict: The rank dict.
    """
    ranks_dict = {_id:dict() for _id in list(github_analysis_dict.keys())}
    for userid in list(github_analysis_dict.keys())[:-1]:
        for k in cat_dict.keys():
            if k in github_analysis_dict[userid]["repo_anlysis_metrics"]:
                if k != "cc":
                    ranks_dict[userid][k] = get_metric_category(github_analysis_dict[userid]["repo_anlysis_metrics"][k], cat_dict[k]["break_points"], reverse=False)
                else:
                    ranks_dict[userid][k] = get_metric_category(github_analysis_dict[userid]["repo_anlysis_metrics"][k], cat_dict[k]["break_points"], reverse=True)
            else:
                ranks_dict[userid][k] = "N/A"
    return ranks_dict


def get_metric_summary_dict(cat_dict)->dict:
    """
    Gets the metric summary dict for the given category dict.
    Returns the metric summary dict.

    Args:
        cat_dict (dict): The category dict.

    Returns:
        dict: The metric summary dict.
    """
    metrics = list(cat_dict.keys())
    _dict = {
            "max":[cat_dict[m]["max"] for m in metrics],
            "min": [cat_dict[m]["min"] for m in metrics],
            "break_points": [cat_dict[m]["break_points"] for m in metrics],
            "sum": [cat_dict[m]["sum"] for m in metrics]
            }
    _dict["metrics"] = metrics
    return _dict

def get_repo_names(userid_list, results_dict, key='repo_meta')->list:
    """
    Gets the repo names for the given userid list and results dict.
    Returns the repo names.

    Args:
        userid_list (list): The userid list.
        results_dict (dict): The results dict.
        key (str): The key.

    Returns:
        list: The repo names.
    """
    return [list(results_dict[user_id][key].keys())[0]
                  if results_dict[user_id] and "error" not in results_dict[user_id][key] 
                  else None
                  for user_id in userid_list]


def get_repo_df_dict(df_cols,  key, userid_list, repo_name_list, results_dict)->dict:
    """
    Gets the repo df dict for the given df cols, key, userid list, repo name list and results dict.
    Returns the repo df dict.

    Args:
        df_cols (list): The df cols.
        key (str): The key.
        userid_list (list): The userid list.
        repo_name_list (list): The repo name list.
        results_dict (dict): The results dict.
        
    Returns:
        dict: The repo df dict.
    """
    _dict = {col:[results_dict[user_id][key][rn][col]
                  if "error" not in results_dict[user_id][key] and rn != None and col in results_dict[user_id][key][rn]
                  else "N/A"
                  for user_id,rn in zip(userid_list,repo_name_list)]
             for col in df_cols}
    _dict["userId"] = userid_list
    _dict["repo_name"] = repo_name_list
    
    return _dict


def get_df_dict(df_cols, key, userid_list, results_dict)->dict:
    """
    Gets the df dict for the given df cols, key, userid list and results dict.
    Returns the df dict.

    Args:
        df_cols (list): The df cols.
        key (str): The key.
        userid_list (list): The userid list.
        results_dict (dict): The results dict.

    Returns:
        dict: The df dict.
    """
    _dict = {col:[results_dict[user_id][key][col]
                  if col in results_dict[user_id][key] 
                  else "N/A"
                  for user_id in userid_list]
             for col in df_cols
                  }
    _dict["userId"] = userid_list
    
    return _dict


def get_df(week, _dict)-> pd.DataFrame:
    """
    Gets the df for the given week and dict.
    Returns the df.

    Args:
        week (int): The week.
        _dict (dict): The dict.

    Returns:
        pd.DataFrame: The df.
    """
    _df = pd.DataFrame(_dict)
    _df["week"] = week
    
    return _df



def get_break_points(_min,_max, num_cat=4)->list:
    """
    Gets the break points for the given min and max values.
    Returns the break points.

        Args:
            _min (int): The min value.
            _max (int): The max value.
            num_cat (int): The number of categories.

        Returns:
            list: The break points.
    """
    div = (_max  - _min)/num_cat
    if div == 0:
        return [0 for i in range(num_cat)]
    return [_min + (i*div) for i in range(1,num_cat)]

# get repo meta data and analysis data
            

def get_repo_meta_pyanalysis(user, github_token, repo_name)->dict:
    """
    Gets the repo meta data and analysis data.
    Returns the repo meta data and analysis data.

    Args:
        user (str): The user.
        github_token (str): The github token.
        repo_name (str): The repo name.

    Returns:
        dict: The repo meta data and analysis data.
    """
    repo_meta_repo_pyanalysis = single_repos_meta_single_repos_pyanalysis(user, github_token, repo_name, api=False)

    hld = dict()
    try:
        hld["repo_meta"] = repo_meta_repo_pyanalysis["repo_meta"][repo_name]

    except:
        hld["repo_meta"] = repo_meta_repo_pyanalysis["repo_meta"]

    try:
        hld["repo_anlysis_metrics"] = repo_meta_repo_pyanalysis["analysis_results"]["repo_summary"]
    except:
        hld["repo_anlysis_metrics"] = repo_meta_repo_pyanalysis["analysis_results"]

    return hld


def normalize_repo_data(data_dict, starter_code_ref_basevalues)->dict:
    """
    Normalizes the repo data.
    Returns the normalized repo data.

    Args:
        data_dict (dict): The repo data dict.
        starter_code_ref_basevalues (dict): The starter code reference basevalues dict.

    Returns:
        dict: The normalized repo data.
    """
    _dict = {
             k:(data_dict[k] - starter_code_ref_basevalues[k] 
             if k in starter_code_ref_basevalues.keys() and data_dict[k] != None else data_dict[k]) 
             for k in data_dict
             }
    return _dict