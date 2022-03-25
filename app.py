import json
import os
import shutil
import sys
import requests
from radon.complexity import cc_rank
from radon.metrics import mi_rank
from flask import Flask, jsonify

curdir = os.path.dirname(os.path.realpath(__file__))
cpath = os.path.dirname(curdir)
if not cpath in sys.path:
    sys.path.append(cpath)

from modules.utils import check_lang_exit, get_cc_summary, retrieve_repo_meta, run_jsanalysis, run_pyanalysis, run_to_get_adds_and_save_content, send_get_req



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

                stderr, return_code, additions_dict, files = run_to_get_adds_and_save_content(repo_name, repo_dict=repo_details[0], file_ext=[".py"])

                # if there is no error
                if return_code == 0:

                    analysis_results = run_pyanalysis()
                    analysis_results["cyclomatic_complexity_summary"] = \
                        {
                            f:
                                (
                                    {
                                    "cc": get_cc_summary(analysis_results["cyclomatic_complexity"][f]),
                                    "rank": cc_rank(get_cc_summary(analysis_results["cyclomatic_complexity"][f]))
                                    }
                                    if isinstance(analysis_results["cyclomatic_complexity"][f], list) else None
                                ) 
                                for f in analysis_results["cyclomatic_complexity"] for i in f
                        }
                    
                    file_level = {f:dict() for f in analysis_results["raw_metrics"]}
                    for f in file_level.keys():
                        
                        # cyclomatic complexity 
                        if f in analysis_results["cyclomatic_complexity_summary"].keys() and analysis_results["cyclomatic_complexity_summary"][f] != None:
                            file_level[f]["cc"] = analysis_results["cyclomatic_complexity_summary"][f]["cc"]
                            file_level[f]["cc_rank"] = analysis_results["cyclomatic_complexity_summary"][f]["rank"]
                        else:
                            file_level[f]["cc"] = None
                            file_level[f]["cc_rank"] = "N/A"

                        # cyclomatic complexity 
                        if f in analysis_results["maintainability_index"].keys() and "error" not in analysis_results["maintainability_index"][f].keys():
                            file_level[f]["mi"] = analysis_results["maintainability_index"][f]["mi"]
                            file_level[f]["mi_rank"] = analysis_results["maintainability_index"][f]["rank"]
                        else:
                            file_level[f]["mi"] = None
                            file_level[f]["mi_rank"] = "N/A"

                        # additions
                        if "./"+f in additions_dict.keys():
                            file_level[f]["additions"] = additions_dict["./"+f]
                        else:
                            file_level[f]["additions"] = None

                        # raw metrics
                        file_level[f].update(analysis_results["raw_metrics"][f])


                    analysis_results["file_level"] = file_level

                    commulative_keys = ["blank","comments","lloc","loc","multi","single_comments","sloc","additions"]
                    
                    repo_summary = {k:[] for k in file_level[files[0][0][2:]].keys() if not k.endswith("_rank")}
                    
                    for k in repo_summary.keys():
                        for f in file_level:
                            if not f.__contains__("changed_"):
                                if file_level[f][k] != None:
                                    repo_summary[k].append(file_level[f][k])

                    repo_summary = {k:(sum(v) if k in commulative_keys else sum(v)/len(v)) for k,v in repo_summary.items()}

                    repo_summary["cc_rank"] = cc_rank(repo_summary["cc"])
                    repo_summary["mi_rank"] = mi_rank(repo_summary["mi"])

                    analysis_results["file_level"] = file_level

                    analysis_results["repo_summary"] = repo_summary





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
