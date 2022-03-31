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

from modules.utils import add_js_additions, check_lang_exit, get_cc_summary, get_file_level_summary, get_js_cc_summary, get_jsrepo_level_summary, get_repo_level_summary, retrieve_repo_meta, run_jsanalysis, run_pyanalysis, run_to_get_adds_and_save_content, send_get_req



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
        info_list = ["avatar_url", "public_repos",'name', 'email', 'bio','followers', 'following', "html_url"]
        dt = {k:d[k] for k in info_list}
        
        # issues
        resp, resp_status_code = send_get_req(_url='https://api.github.com/search/issues?q=author:{}'.format(user), _header=headers)
        if resp_status_code == 200:
            d = resp.json()
            dt["issues"] = d["total_count"]
        else:
            dt["issues"] = "N/A"

        # pull requests
        resp, resp_status_code = send_get_req(_url='https://api.github.com/search/issues?q=author:{}+is:pr'.format(user), _header=headers)
        if resp_status_code == 200:
            d = resp.json()
            dt["pull_requests"] = d["total_count"]
        else:
            dt["pull_requests"] = "N/A"

        resp, resp_status_code = send_get_req(_url='https://api.github.com/search/commits?q=author:{}'.format(user), _header=headers)
        if resp_status_code == 200:
            d = resp.json()
            dt["commits"] = d["total_count"]
        else:
            dt["commits"] = "N/A"


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
        info_list = ["forks", "languages_url", "contributors_url", "branches_url", "description", "html_url"]
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
    resp, resp_status_code = send_get_req(_url="https://api.github.com/search/repositories?q=repo:{}/{}".format(user,repo_name), _header=headers)
    if resp_status_code == 200:
        # retrive response body
        d = resp.json()
        info_list = ["forks", "languages_url", "contributors_url", "branches_url", "description", "html_url"]
        resp_dict = {repo["name"]:{k:repo[k] for k in info_list} for repo in d["items"]}
        if len(resp_dict) == 0:
            resp, resp_status_code = send_get_req(_url='https://api.github.com/users/{}/repos'.format(user), _header=headers)
            if resp_status_code == 200:
                # retrive response body
                d = resp.json()
                resp_dict = {repo["name"]:{k:repo[k] for k in info_list} for repo in d if repo["name"] == repo_name}
                if len(resp_dict) == 0:
                    return jsonify({"error":"Not Found"})
            else:
                return jsonify({"error":"Not Found"})
        dt = retrieve_repo_meta(resp_json=resp_dict, headers=headers, user=user)
        return jsonify(dt)
    else:
        return jsonify({"error":resp.json()["errors"][0]["message"]})


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
    resp, resp_status_code = send_get_req(_url="https://api.github.com/search/repositories?q=repo:{}/{}".format(user,repo_name), _header=headers)
    if resp_status_code == 200:
        # retrive response body
        d = resp.json()
        repo_details = [repo for repo in d["items"]]
        if len(repo_details) == 0:
            resp, resp_status_code = send_get_req(_url='https://api.github.com/users/{}/repos'.format(user), _header=headers)
            if resp_status_code == 200:
                # retrive response body
                d = resp.json()
                # retrieve named repo
                repo_details = [repo for repo in d if repo["name"]==repo_name]
                if len(repo_details) == 0:
                    return jsonify({"error":"Not Found"})
            else:
                return jsonify({"error":"Not Found"})   
        lang_list = ["Python"]
    
        # check if the repo contains python files
        if  check_lang_exit(user=user, repo=repo_name, headers=headers, lang_list=lang_list):

            stderr, return_code, additions_dict, files = run_to_get_adds_and_save_content(repo_name, repo_dict=repo_details[0], file_ext=[".py"])

            # if there is no error
            if return_code == 0:

                # run analysis for python codes
                analysis_results = run_pyanalysis()
                # get cyclomatic complexity values for each file
                analysis_results["cyclomatic_complexity_summary"] = get_cc_summary(analysis_results, "complexity")
                # get file level summary for code metrics
                analysis_results["file_level"] = get_file_level_summary(analysis_results, additions_dict)
                # get aggregate values of code metrics for repo
                analysis_results["repo_summary"] = get_repo_level_summary(files, analysis_results["file_level"])
                
                # delete repository directory after checking code metrics
                os.chdir("../")
                shutil.rmtree(repo_name)

                return jsonify({"analysis_results":analysis_results})  
            
            else:
                return jsonify({"error" : stderr})

        else:
            return jsonify({"error":"repository does not contain {} files".format(lang_list)})
    else:
        return jsonify({"error":resp.json()["errors"][0]["message"]})




@app.route('/single_repos_jsanalysis/<string:user>/<string:token>/<string:repo_name>',methods=["GET"])
def get_single_repo_jsanalysis(user, token, repo_name)->json:
    """
    Takes username, github generated token and name of repo and returns json of details of javascript code analysis in 
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
    resp, resp_status_code = send_get_req(_url="https://api.github.com/search/repositories?q=repo:{}/{}".format(user,repo_name), _header=headers)
    if resp_status_code == 200:
        # retrive response body
        d = resp.json()
        repo_details = [repo for repo in d["items"]]
        if len(repo_details) == 0:
            resp, resp_status_code = send_get_req(_url='https://api.github.com/users/{}/repos'.format(user), _header=headers)
            if resp_status_code == 200:
                # retrive response body
                d = resp.json()
                # retrieve named repo
                repo_details = [repo for repo in d if repo["name"]==repo_name]
                if len(repo_details) == 0:
                    return jsonify({"error":"Not Found"})
            else:
                return jsonify({"error":"Not Found"})

        lang_list = ["JavaScript"]
        
        # check if the repo contains python files
        if  check_lang_exit(user=user, repo=repo_name, headers=headers, lang_list=lang_list):

            stderr, return_code, additions_dict, files= run_to_get_adds_and_save_content(repo_name, repo_dict=repo_details[0], file_ext=[".js"])

            # if there is no error
            if return_code == 0:
                files = [f for tup in files for f in tup]
                analysis_results = run_jsanalysis(files)
                analysis_results["cyclomatic_complexity_summary"] = get_js_cc_summary(analysis_results, "cyclomatic_complexity")
                analysis_results = add_js_additions(analysis_results, additions_dict)
                analysis_results["repo_summary"] = get_jsrepo_level_summary(files, analysis_results["cyclomatic_complexity_summary"])

                # delete repository directory after checking code metrics
                os.chdir("../")
                shutil.rmtree(repo_name)

                return jsonify({"analysis_results":analysis_results, "commit_additions":additions_dict})  
            
            else:
                return jsonify({"error" : stderr})

        else:
            return jsonify({"error":"repository does not contain {} files".format(lang_list)})

    
    else:
        return jsonify({"error":resp.json()["errors"][0]["message"]})


if __name__ == "__main__":
    app.run(debug=True)
