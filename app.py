import json
import os
import shutil
import sys

import requests
from flask import Flask, jsonify

curdir = os.path.dirname(os.path.realpath(__file__))
cpath = os.path.dirname(curdir)
if not cpath in sys.path:
    sys.path.append(cpath)

from modules.utils import check_lang_exit, clone_repo, create_repo_dir, get_additions_and_save_contents, retriev_files, retrieve_diff_details, retrieve_init_last_commit_sha, retrieve_repo_meta, run_cmd_process, run_jsanalysis, run_pyanalysis, run_to_get_adds_and_save_content, save_file, send_get_req



app = Flask(__name__)

@app.route('/user/<string:user>/<string:token>',methods=["GET"])
def get_user(user, token)->json:
    """
    Takes username and github generated token and returns json on user acount details

    Args:
        user(str): github account username
        token(str): github account token

    Returns:
        json of accounts details
    """
    # create authourization headers for get request
    headers = {"Authorization":"Bearer {}".format(token)}
    # send get request to github api
    resp, resp_status_code = send_get_req(_url='https://api.github.com/users/{}'.format(user), _header=headers)
    if resp_status_code == 200:
        # retrive response body
        d = resp.json()
        info_list = ['name', 'email', 'bio','followers', 'following']
        dt = {k:d[k] for k in info_list}
        dt["repos"] = {"public_repos": d["public_repos"], "total_private_repos":d["total_private_repos"], \
             "owned_private_repos":d["owned_private_repos"]}
        return jsonify(dt)
    else:
        return jsonify({"error":"Not Found"})

    
@app.route('/repos_meta/<string:user>/<string:token>',methods=["GET"])
def get_repo_meta(user, token)->json:
    """
    Takes username and github generated token and returns json of details on each repository

    Args:
        user(str): github account username
        token(str): github account token

    Returns:
        json of details of each repository 
    """
    # create authourization headers for get request
    headers = {"Authorization":"Bearer {}".format(token)}
    # send get request to github api
    resp, resp_status_code = send_get_req(_url='https://api.github.com/users/{}/repos'.format(user), _header=headers)
    if resp_status_code == 200:
        # retrive response body
        d = resp.json()
        info_list = ["forks", "languages_url", "contributors_url", "branches_url"]
        resp_dict = {repo["name"]:{k:repo[k] for k in info_list} for repo in d}
        dt = retrieve_repo_meta(resp_json=resp_dict, headers=headers, user=user)
        return jsonify(dt)
    else:
        return jsonify({"error":"Not Found"})


@app.route('/single_repos_meta/<string:user>/<string:token>/<string:repo_name>',methods=["GET"])
def get_single_repo_meta(user, token, repo_name)->json:
    """
    Takes username, github generated token and name of repo and returns json of details of repository

    Args:
        user(str): github account username
        token(str): github account token
        repo_name(str): github repository name

    Returns:
        json of details of repository 
        metrics :
            cyclomatic complxity
            raw metrics
            maintinability Index
    """
    # create authourization headers for get request
    headers = {"Authorization":"Bearer {}".format(token)}
    # send get request to github api
    resp, resp_status_code = send_get_req(_url='https://api.github.com/users/{}/repos'.format(user), _header=headers)
    if resp_status_code == 200:
        # retrive response body
        d = resp.json()
        info_list = ["forks", "languages_url", "contributors_url", "branches_url"]
        resp_dict = {repo["name"]:{k:repo[k] for k in info_list} for repo in d if repo["name"]==repo_name}
        dt = retrieve_repo_meta(resp_json=resp_dict, headers=headers, user=user)
        return jsonify(dt)
    else:
        return jsonify({"error":"Not Found"})


@app.route('/single_repos_pyanalysis/<string:user>/<string:token>/<string:repo_name>',methods=["GET"])
def get_single_repo_pyanalysis(user, token, repo_name)->json:
    """
    Takes username, github generated token and name of repo and returns json of details of python code analis in 
    repository

    Args:
        user(str): github account username
        token(str): github account token
        repo_name(str): github repository name

    Returns:
        json of details of python code analysis in repository 
    """
    # create authourization headers for get request
    headers = {"Authorization":"Bearer {}".format(token)}
    # send get request to github api
    resp = requests.get('https://api.github.com/users/{}/repos'.format(user), headers=headers)
    if resp.status_code == 200:
        # retrive response body
        d = resp.json()

        # retrieve named repo
        repo_details = [repo for repo in d if repo["name"]==repo_name]
        
        if repo_details:
            lang_list = ["Python"]
            
            # check if the repo contains python files
            if  check_lang_exit(user=user, repo=repo_name, headers=headers, lang_list=lang_list):

                stderr, return_code, additions_dict, _ = run_to_get_adds_and_save_content(repo_name, repo_dict=repo_details[0], file_ext=[".py"])

                # if there is no error
                if return_code == 0:

                    analysis_results = run_pyanalysis()
                    
                    # delete repository directory after checking code metrics
                    os.chdir("../")
                    shutil.rmtree(repo_name)

                    return jsonify({"analysis_results":analysis_results, "commit_additions":additions_dict})  
                
                else:
                    return jsonify({"error" : stderr})

            else:
                return jsonify({"error":"repository does not contain {} files".format(lang_list)})

        else:
            return jsonify({"error":"repository not found"})
    
    else:
        return jsonify({"error":"Not Found"})



@app.route('/single_repos_jsanalysis/<string:user>/<string:token>/<string:repo_name>',methods=["GET"])
def get_single_repo_jsanalysis(user, token, repo_name)->json:
    """
    Takes username, github generated token and name of repo and returns json of details of javascript code analis in 
    repository

    Args:
        user(str): github account username
        token(str): github account token
        repo_name(str): github repository name

    Returns:
        json of details of python code analysis in repository 
    """
    # create authourization headers for get request
    headers = {"Authorization":"Bearer {}".format(token)}
    # send get request to github api
    resp = requests.get('https://api.github.com/users/{}/repos'.format(user), headers=headers)
    if resp.status_code == 200:
        # retrive response body
        d = resp.json()

        # retrieve named repo
        repo_details = [repo for repo in d if repo["name"]==repo_name]
        
        if repo_details:

            lang_list = ["JavaScript"]
            
            # check if the repo contains python files
            if  check_lang_exit(user=user, repo=repo_name, headers=headers, lang_list=lang_list):

                stderr, return_code, additions_dict, files= run_to_get_adds_and_save_content(repo_name, repo_dict=repo_details[0], file_ext=[".js"])

                # if there is no error
                if return_code == 0:
                    files = [f for tup in files for f in tup]
                    analysis_results = run_jsanalysis(files)
                    
                    # delete repository directory after checking code metrics
                    os.chdir("../")
                    shutil.rmtree(repo_name)

                    return jsonify({"analysis_results":analysis_results, "commit_additions":additions_dict})  
                
                else:
                    return jsonify({"error" : stderr})

            else:
                return jsonify({"error":"repository does not contain {} files".format(lang_list)})

        else:
            return jsonify({"error":"repository not found"})
    
    else:
        return jsonify({"error":"Not Found"})


if __name__ == "__main__":
    app.run(debug=True)
