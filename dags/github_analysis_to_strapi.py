from datetime import datetime, timedelta
import os
import sys
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator

curdir = os.path.dirname(os.path.realpath(__file__))
cpath = os.path.dirname(curdir)
if not cpath in sys.path:
    sys.path.append(cpath)



from modules.air_flow_utls import check_assignment_data, check_state_vars, check_strapi_github_token, exit_with_error_all_none, exit_with_error_assignment_data, exit_with_error_github_token, exit_with_error_state_vars, exit_with_error_strapi_token, get_assignment_data, get_client_url, get_github_token, get_state_vars, get_strapi_token, get_training_week, retrieve_state, set_platform, set_run_number, update_state_dict, upload_analysis_to_strapi




DAG_CONFIG = {
    'depends_on_past': False,
    'start_date': datetime(2022, 7, 1),
    'email': ['michael@10acadey.org'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 5,
    'owner' : 'Tenx',
    'retry_delay': timedelta(minutes=1),
}


with DAG("github_analysis_to_strapi", # Dag id
         default_args=DAG_CONFIG,
         catchup=False,
         schedule_interval='0 0 * * 4,0'
        ) as dag:
        
        set_platform_ = PythonOperator(
            task_id="set_platform_",
            python_callable=set_platform
        )

        get_github_token_ = PythonOperator(
            task_id="get_github_token_",
            python_callable=get_github_token
        )

        get_strapi_token_ = PythonOperator(
            task_id="get_strapi_token_",
            python_callable=get_strapi_token
        )
        
        retrieve_state_ = PythonOperator(
            task_id="retrieve_state_",
            python_callable=retrieve_state
        )
        
        check_strapi_github_token_ = BranchPythonOperator(
            task_id="check_strapi_github_token_",
            python_callable=check_strapi_github_token
        )

        exit_with_error_all_none_ = PythonOperator(
            task_id="exit_with_error_all_none_",
            python_callable=exit_with_error_all_none
        )

        exit_with_error_strapi_token_ = PythonOperator(
            task_id = "exit_with_error_strapi_token_",
            python_callable=exit_with_error_strapi_token
        )

        exit_with_error_github_token_ = PythonOperator(
            task_id = "exit_with_error_github_token_",
            python_callable=exit_with_error_github_token
        )

        get_state_vars_ = PythonOperator(
            task_id="get_state_vars_",
            python_callable=get_state_vars
        )

        check_state_vars_ = BranchPythonOperator(
            task_id="check_state_vars_",
            python_callable=check_state_vars
        )

        exit_with_error_state_vars_ = PythonOperator(
            task_id="exit_with_error_state_vars_",
            python_callable=exit_with_error_state_vars
        )

        set_run_number_ = PythonOperator(
            task_id="set_run_number_",
            python_callable=set_run_number
        )

        get_training_week_ = PythonOperator(
            task_id="get_training_week_",
            python_callable=get_training_week
        )

        get_client_url_ = PythonOperator(
            task_id="get_client_url_",
            python_callable=get_client_url
        )

        get_assignment_data_ = PythonOperator(
            task_id="get_assignment_data_",
            python_callable=get_assignment_data
        )
        
        check_assignment_data_ = BranchPythonOperator(
            task_id="check_assignment_data_",
            python_callable=check_assignment_data
        )

        exit_with_error_assignment_data_ = PythonOperator(
            task_id="exit_with_error_assignment_data_",
            python_callable=exit_with_error_assignment_data
        )

        upload_analysis_to_strapi_ = PythonOperator(
            task_id="upload_analysis_to_strapi_",
            python_callable=upload_analysis_to_strapi
        )

        update_state_dict_ = PythonOperator(
            task_id="update_state_dict_",
            python_callable=update_state_dict
        )


        set_platform_ >> get_github_token_ >> get_strapi_token_ \
        >> check_strapi_github_token_ >> [exit_with_error_all_none_ , exit_with_error_strapi_token_, exit_with_error_github_token_]
        
        check_strapi_github_token_ >> retrieve_state_ >> get_state_vars_ >> check_state_vars_ >> exit_with_error_state_vars_
        
        check_state_vars_ >> set_run_number_ >> get_training_week_ >> get_client_url_ >> get_assignment_data_ >> check_assignment_data_ >> exit_with_error_assignment_data_ 
        check_assignment_data_  >> upload_analysis_to_strapi_ >> update_state_dict_
