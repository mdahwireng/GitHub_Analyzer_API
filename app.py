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

from modules.api_utils import add_js_additions, check_lang_exit, get_cc_summary, get_file_level_summary, get_js_cc_summary, get_jsrepo_level_summary, get_repo_level_summary, retrieve_repo_meta, run_jsanalysis, run_pyanalysis, run_to_get_adds_and_save_content, send_get_req


app = Flask(__name__)

@app.route('/user/<string:user>/<string:token>',methods=["GET"])
def get_user(user, token, api=True)->json:
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
            dt["issues"] = None

        # pull requests
        resp, resp_status_code = send_get_req(_url='https://api.github.com/search/issues?q=author:{}+is:pr'.format(user), _header=headers)
        if resp_status_code == 200:
            d = resp.json()
            dt["pull_requests"] = d["total_count"]
        else:
            dt["pull_requests"] = None

        resp, resp_status_code = send_get_req(_url='https://api.github.com/search/commits?q=author:{}'.format(user), _header=headers)
        if resp_status_code == 200:
            d = resp.json()
            dt["commits"] = d["total_count"]
        else:
            dt["commits"] = None

        if api:
            return jsonify(dt)
        return dt
    else:
        if api:
            return jsonify({"error":"Not Found"})
        return {"error":"Not Found"}

    
@app.route('/repos_meta/<string:user>/<string:token>',methods=["GET"])
def get_repo_meta(user, token, api=True)->json:
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
        if api:
            return jsonify(dt)
        return dt
    else:
        if api:
            return jsonify({"error":"Not Found"})
        return {"error":"Not Found"}


@app.route('/single_repos_meta/<string:user>/<string:token>/<string:repo_name>',methods=["GET"])
def get_single_repo_meta(user, token, repo_name, api=True)->json:
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
                    if api:
                        return jsonify({"error":"Not Found"})
                    return {"error":"Not Found"}
            else:
                if api:
                    return jsonify({"error":"Not Found"})
                return {"error":"Not Found"}
        dt = retrieve_repo_meta(resp_json=resp_dict, headers=headers, user=user)
        if api:
            return jsonify(dt)
        return dt
    else:
        if api:
            return jsonify({"error":"Not Found"})
        return {"error":"Not Found"}


@app.route('/single_repos_pyanalysis/<string:user>/<string:token>/<string:repo_name>',methods=["GET"])
def get_single_repo_pyanalysis(user, token, repo_name, api=True)->json:
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
                    if api:
                        return jsonify({"error":"Not Found"})
                    return {"error":"Not Found"}
            else:
                if api:
                    return jsonify({"error":"Not Found"}) 
                return {"error":"Not Found"} 
        lang_list = ["Python", "Jupyter Notebook"]
    
        # check if the repo contains python files
        if  check_lang_exit(user=user, repo=repo_name, headers=headers, lang_list=lang_list):

            stderr, return_code, additions_dict, files = run_to_get_adds_and_save_content(repo_name, repo_dict=repo_details[0], file_ext=[".py",".ipynb"])

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
                os.chdir("../../")
                shutil.rmtree("tmp/"+repo_name)
                
                if api:
                    return jsonify({"analysis_results":analysis_results})
                return {"analysis_results":analysis_results}  
            
            else:
                if api:
                    return jsonify({"error" : stderr})
                return {"error" : stderr}

        else:
            if api:
                return jsonify({"error":"repository does not contain {} files".format(lang_list)})
            return {"error":"repository does not contain {} files".format(lang_list)}
    else:
        if api:
            return jsonify({"error":resp.json()})
        return {"error":resp.json()}


@app.route('/single_repos_meta_single_repos_pyanalysis/<string:user>/<string:token>/<string:repo_name>',methods=["GET"])
def single_repos_meta_single_repos_pyanalysis(user, token, repo_name, api=True)->json:
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
        
        info_list = ["name","forks", "languages_url", "contributors_url", "branches_url", "description", "html_url"]
        resp_dict = {repo["name"]:{k:repo[k] for k in info_list} for repo in d["items"]}

        if len(resp_dict) > 0:
            resp_dict[repo_name]["repo_name"] = repo_name

        repo_details = [repo for repo in d["items"]]
        if len(repo_details) == 0:
            print("Using alternate method to retrieve rpository details...\n")
            resp, resp_status_code = send_get_req(_url='https://api.github.com/repos/{}/{}'.format(user,repo_name), _header=headers)
            if resp_status_code == 200:
                # retrive response body
                d = resp.json()
                # retrieve named repo
                #print(d)
                # repo_details = [repo for repo in d if repo["name"]==repo_name]
                if  d["name"]==repo_name:
                    repo_details = [d]
                else:
                    repo_details = []

                resp_dict = {d["name"]:{k:d[k] for k in info_list} for i in range(len(d)) if d["name"] == repo_name}
                if len(resp_dict) > 0:
                    resp_dict[repo_name]["repo_name"] = repo_name

                
                if len(repo_details) == 0:
                    if api:
                        return jsonify({"repo_meta":{"error":"Not Found"}, "analysis_results":{"error":"Not Found"}})
                    return {"repo_meta":{"error":"Not Found"}, "analysis_results":{"error":"Not Found"}}
            else:
                if api:
                    return jsonify({"repo_meta":{"error":"Not Found"}, "analysis_results":{"error":"Not Found"}}) 
                return {"repo_meta":{"error":"Not Found"}, "analysis_results":{"error":"Not Found"}}
                
        dt = retrieve_repo_meta(resp_json=resp_dict, headers=headers, user=user)

        lang_list = ["Python", "Jupyter Notebook"]
    
        # check if the repo contains python files
        if  check_lang_exit(user=user, repo=repo_name, headers=headers, lang_list=lang_list):

            stderr, return_code, additions_dict, files, file_check_results = run_to_get_adds_and_save_content(repo_name, repo_dict=repo_details[0], file_ext=[".py", ".ipynb"])

            # Make languages dynamic with number of files of the language
            lang_files_pairing = {"Jupyter Notebook":"num_ipynb", "Python":"num_py", "JavaScript":"num_js"}

            tmp_list = []
            for k,v in lang_files_pairing.items():
                for tup in dt[repo_name]["languages"]:
                    if tup[0] == k:
                        hld_dict = dict()
                        hld_dict["name"] = k
                        hld_dict["percentage"] = tup[1]
                        hld_dict["file_count"] = file_check_results[v]
                        tmp_list.append(hld_dict)
            
            # replace languages with updated values
            dt[repo_name]["languages"] = tmp_list
            
            # Add file check results to repo meta
            dt[repo_name].update(file_check_results)
            dt[repo_name]["repo_name"] = repo_name

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
                os.chdir("../../")
                shutil.rmtree("tmp/"+repo_name)

                if api:
                    return jsonify({"repo_meta":dt, "analysis_results":analysis_results})  
                return {"repo_meta":dt, "analysis_results":analysis_results}

            else:
                if api:
                    return jsonify({"repo_meta":dt, "analysis_results":{"error" : stderr}})
                return {"repo_meta":dt, "analysis_results":{"error" : stderr}}

        else:
            if api:
                return jsonify({"repo_meta":dt, "analysis_results":{"error":"repository does not contain {} files".format(lang_list)}})
            return {"repo_meta":dt, "analysis_results":{"error":"repository does not contain {} files".format(lang_list)}}

    else:
        if api:
            return jsonify({"repo_meta":{"error":resp.json()}, "analysis_results":{"error":"Not Found"}})
        return {"repo_meta":{"error":resp.json()}, "analysis_results":{"error":"Not Found"}}
        



@app.route('/single_repos_jsanalysis/<string:user>/<string:token>/<string:repo_name>',methods=["GET"])
def get_single_repo_jsanalysis(user, token, repo_name, api=True)->json:
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
                    if api:
                        return jsonify({"error":"Not Found"})
                    return {"error":"Not Found"}
            else:
                if api:
                    return jsonify({"error":"Not Found"})
                return {"error":"Not Found"}

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
                os.chdir("../../")
                shutil.rmtree("tmp/"+repo_name)

                if api:
                    return jsonify({"analysis_results":analysis_results, "commit_additions":additions_dict})
                return {"analysis_results":analysis_results, "commit_additions":additions_dict}  
            
            else:
                if api:
                    return jsonify({"error" : stderr})
                return {"error" : stderr}

        else:
            if api:
                return jsonify({"error":"repository does not contain {} files".format(lang_list)})
            return {"error":"repository does not contain {} files".format(lang_list)}

    
    else:
        if api:
            return jsonify({"error":resp.json()})
        return {"error":resp.json()}

# run the app


if __name__ == "__main__":
    if os.path.exists(".env/env_var.json"):
        with open(".env/env_var.json", "r") as e:
            env_var = json.load(e)
            host = env_var["host"]
            port = env_var["port"]
        app.run(host=host, port=port, debug=False)
    
    else:
        app.run(debug=True)
