from ast import literal_eval
from datetime import datetime
import json
import os
import pickle
import sys
import numpy as np

import pandas as pd
from modules.Load_to_starpi import Load_To_Strapi
from modules.Prepare_Assignment_Submissions import PrepareAssignmentDf

from modules.Treat_Assignment_Response import Get_Assignment_Data


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



def set_week_submission_data_save_path(week, run_number, platform, batch):
    """
    Set week submission data save path
    
    Args:
        ti (TaskInstance): TaskInstance object
        
    Returns:
        None
    """
    week_submission_dir = "data/week_data/batch{}/{}/{}/run{}".format(batch, week, platform, run_number)
    week_submission_path = week_submission_dir + "/b{}_{}_{}_run{}.csv".format(batch, week, platform, run_number)
    
    if not os.path.isdir(week_submission_dir):
        os.makedirs(week_submission_dir)
    
    return week_submission_path


def save_week_submission_data(assignment_data_df, week_submission_path, run_number):
    prep_assn = PrepareAssignmentDf(assignment_data_df, run_number, "root_url")
    github_df = prep_assn.get_df(week_submission_path)


def check_assignment_data_internal(assignment_data_df, week, run_number, platform, batch):
    if isinstance(assignment_data_df, pd.DataFrame) and assignment_data_df.empty is False:
        week_submission_path = set_week_submission_data_save_path(week, run_number, platform, batch)
        save_week_submission_data(assignment_data_df, week_submission_path, run_number)
        return {"check": "pass", "save_path": week_submission_path}
   
    else:
        return {"check": "fail", "save_path": ""}
    





############################################################################################################################

# functions for the dags

############################################################################################################################

def retrieve_state(ti, state_path = "data/api_state/week/week_state.pk")->dict:
    """
    Retrieves the state from the pickle file

    Args:
        ti (TaskInstance): TaskInstance object
        state_path (str): path to the pickle file
    """
    try:
        if os.path.exists(state_path):
            with open(state_path, "rb") as s_d:
                state_dict = pickle.load(s_d)
        else:
            print("Error: state file does not exist")
            state_dict = None
            return state_dict
        platform = ti.xcom_pull(task_ids="set_platform_")
        analyzed_assgnmt = state_dict["previously_analyzed_assignments"]
        batch = state_dict["batch"]
        run_number = state_dict["run_number"]
        base_url = state_dict["base_url"][platform]
        return state_dict
    
    except Exception as e:
        print("Error: could not load state file")
        print(repr(e))
        state_dict = None
        return state_dict






def exit_with_error_all_none(error_message="Error: Github and Strapi tokens were not returned")->None:
    """
    Prints error message and exits the program
    
    Args:
        error_message (str): error message to print
        
    Returns:
        None
    """
    exit_with_error(error_message=error_message)
    



def exit_with_error_strapi_token(error_message="Error: strapi token was not returned")->None:
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




def set_platform(ti, platform="stage")->None:
    """
    Sets the platform
    
    Args:
        ti (TaskInstance): TaskInstance object
        platform (str): platform name (dev,stage, prod)
        
    Returns:
        None
    """
    return platform




def get_github_token(ti, path_to_json=".env/secret.json", var_name="github_token")->str:
    """
    Gets the github token from the json file

    Args:
        ti (TaskInstance): TaskInstance object
        path_to_json (str): path to the json file
        var_name (str): variable name (key)
    
    Returns:
        str: github token
    """
    github_token = get_var_from_json(path_to_json=path_to_json, var_name=var_name)
    return github_token



def get_strapi_token(ti, path_to_json=".env/secret.json", var_name="strapi_token")->str:
    """
    Gets the strapi token from the json file
    
    Args:
        ti (TaskInstance): TaskInstance object
        path_to_json (str): path to the json file
        var_name (str): variable name (key)
        
    Returns:
        str: strapi token
    """
    platform = ti.xcom_pull(task_ids="set_platform_")
    strapi_token = get_var_from_json(path_to_json=path_to_json, var_name=var_name)[platform]
    return strapi_token


def check_strapi_github_token(ti)->None:
    """
    Checks if the github token is set
    
    Args:
        ti (TaskInstance): TaskInstance object
        
    Returns:
        task id of the next task (str)
    """
    # check if github_token was returned
    github_token = ti.xcom_pull(task_ids="get_github_token_")
    strapi_token = ti.xcom_pull(task_ids="get_strapi_token_")

    if github_token is None or strapi_token is None:
    
        if github_token is None and strapi_token is None:
            return "exit_with_error_all_none_"
        elif github_token is None:
            return "exit_with_error_github_token_"
        else:
            return "exit_with_error_strapi_token_"

    else:
        return "retrieve_state_"


def get_state_vars(ti)->dict:
    """
    Gets the state variables
    
    Args:
        ti (TaskInstance): TaskInstance object
        
    Returns:
        Dictionary of error or empty dictionary
    """
    try:
        state_dict = ti.xcom_pull(task_ids="retrieve_state_")
        analyzed_assgnmt = state_dict["previously_analyzed_assignments"]
        batch = state_dict["batch"]
        run_number = state_dict["run_number"]
        return dict()
    except Exception as e:
        return {"error":repr(e)}

def check_state_vars(ti):
    """
    Checks if the state variables are set
    
    Args:
        ti (TaskInstance): TaskInstance object
        
    Returns:
        None
    """
    state_dict = ti.xcom_pull(task_ids="get_state_vars_")
    if "error" in state_dict:
        exit_with_error(error_message=state_dict["error"])
        return "exit_with_error_state_vars_"
    else:
        return "set_run_number_"


def exit_with_error_state_vars(ti)->None:
    """
    Prints error message and exits the program
    
    Args:
        None
        
    Returns:
        None
    """
    state_dict = ti.xcom_pull(task_ids="get_state_vars_")
    exit_with_error(error_message=state_dict["error"])
     


def get_training_week(ti):
    """
    Gets the training week
    
    Args:
        ti (TaskInstance): TaskInstance object
        
    Returns:
        a dictionary of week name and week number with keys "week_name" and "week_number"
    """
    current_week = datetime.now().isocalendar()[1] - 1
    training_week = current_week - 18
    week= "week{}".format(training_week)
    return {"week": week, "week_number": training_week}


def get_client_url(ti):
    """
    Gets the client url
    
    Args:
        ti (TaskInstance): TaskInstance object
        
    Returns:
        client_url (str)
    """
    platform = ti.xcom_pull(task_ids="set_platform_")
    base_url = ti.xcom_pull(task_ids="retrieve_state_")["base_url"][platform]
    client_url = base_url + "/graphql"
    return client_url


def get_assignment_data(ti):
    """
    Gets the assignment data
    
    Args:
        ti (TaskInstance): TaskInstance object
        
    Returns:
        assignment data dictionary of filtered data and analyzed assignments (dict) with keys "filtered_data" and "analyzed_assignments"
    """
    week = ti.xcom_pull(task_ids="get_training_week_")["week"]
    platform = ti.xcom_pull(task_ids="set_platform_")
    base_url = ti.xcom_pull(task_ids="retrieve_state_")["base_url"][platform]
    strapi_token = ti.xcom_pull(task_ids="get_strapi_token_")
    batch = ti.xcom_pull(task_ids="retrieve_state_")["batch"]
    previous_analyzed_assignments = ti.xcom_pull(task_ids="retrieve_state_")["previously_analyzed_assignments"]
    run_number = ti.xcom_pull(task_ids="set_run_number_")

    assgn = Get_Assignment_Data(week, batch, base_url, strapi_token, previous_analyzed_assignments)

    assignment_data_df = assgn.filtered_data_df()
    analyzed_assignments = assgn.get_analyzed_assignments()
    assignment_data_check = check_assignment_data_internal(assignment_data_df, week, run_number, platform, batch)

    assignment_data = {"check": assignment_data_check["check"], "save_path": assignment_data_check["save_path"], "analyzed_assignments": analyzed_assignments}
    return assignment_data


def check_assignment_data(ti):
    """
    Checks if the assignment data has passed the checks

    Args:
        ti (TaskInstance): TaskInstance object

    Returns:
        task id of the next task (str)
    """
    check = ti.xcom_pull(task_ids="get_assignment_data_")["check"]
    if check:
        return "upload_analysis_to_strapi_"
    else:
        return "exit_with_error_assignment_data_"

def exit_with_error_assignment_data(ti):
    """
    Prints error message and exits the program
    
    Args:
        ti (TaskInstance): TaskInstance object
        
    Returns:
        None
    """
    exit_with_error(error_message="Assignment data is not a dataframe or is empty")


def set_run_number(ti):
    """
    Sets the run number
    
    Args:
        ti (TaskInstance): TaskInstance object
        
    Returns:
        run number (str)
    """
    batch = ti.xcom_pull(task_ids="retrieve_state_")["batch"]
    state_run_number = ti.xcom_pull(task_ids="retrieve_state_")["run_number"]
    run_number = "b{}_r{}".format(batch, state_run_number)
    return run_number   



def upload_analysis_to_strapi(ti):
    """
    Uploads the analysis to strapi
    
    Args:
        ti (TaskInstance): TaskInstance object
        
    Returns:
        None
    """
    week = ti.xcom_pull(task_ids="get_training_week_")["week"]
    platform = ti.xcom_pull(task_ids="set_platform_")
    batch = ti.xcom_pull(task_ids="retrieve_state_")["batch"]
    run_number = ti.xcom_pull(task_ids="set_run_number_")
    strapi_token = ti.xcom_pull(task_ids="get_strapi_token_")
   
    week_submission_path = ti.xcom_pull(task_ids="get_assignment_data_")["save_path"]
    github_df = pd.read_csv(week_submission_path)
    github_df = github_df.replace({np.nan: None})
    github_df["assignments_ids"] = github_df["assignments_ids"].apply(lambda x: literal_eval(x))
    github_df["trainee"] = github_df["trainee"].apply(lambda x: int(x))
    
    base_url = ti.xcom_pull(task_ids="retrieve_state_")["base_url"][platform]
    github_token = ti.xcom_pull(task_ids="get_github_token_")
    strapi_token = ti.xcom_pull(task_ids="get_strapi_token_")

    to_strapi = Load_To_Strapi(platform, week, batch, run_number, base_url, github_df, github_token, strapi_token)

    to_strapi.run_to_load()

def update_state_dict(ti):
    """
    Updates the state variables
    
    Args:
        ti (TaskInstance): TaskInstance object
        
    Returns:
        None
    """
    analyzed_assignments = ti.xcom_pull(task_ids="get_assignment_data_")["analyzed_assignments"]
    state_dict = ti.xcom_pull(task_ids="retrieve_state_")
    
    state_dict["previously_analyzed_assignments"] = analyzed_assignments
    present_week = datetime.now().isocalendar()[1]

    if present_week > state_dict["current_week"]:
        state_dict["run_number"] = 1
        state_dict["current_week"] = present_week
    else:
        state_dict["run_number"] += 1
    
    st_dir = "data/api_state/week"
    if not os.path.isdir(st_dir):
        os.makedirs(st_dir)


    with open(st_dir + "/week_state.pk", "wb") as f:
        pickle.dump(state_dict, f)





