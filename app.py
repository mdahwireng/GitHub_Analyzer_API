import json
from flask import Flask, jsonify
import requests
import os
import subprocess
import shutil

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
    resp = requests.get('https://api.github.com/users/{}'.format(user), headers=headers)
    if resp.status_code == 200:
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
    resp = requests.get('https://api.github.com/users/{}/repos'.format(user), headers=headers)
    if resp.status_code == 200:
        # retrive response body
        d = resp.json()
        info_list = ["forks", "languages_url", "contributors_url", "branches_url"]
        dt = {repo["name"]:{k:repo[k] for k in info_list} for repo in d}
        for repo in dt.keys():
            # Retrieve language details
            languages_url = "https://api.github.com/repos/{}/{}/languages".format(user,repo)
            languages = requests.get(languages_url, headers=headers).json()
            total_contribs = sum([languages[l] for l in languages])
            lang_list = [(l, float("{:.2f}".format(languages[l]/total_contribs * 100))) \
                                for l in languages]
            lang_list.sort(key=lambda x:x[1], reverse=True)
            dt[repo]["languages"] = lang_list[:3]

            # Retrieve branches details
            branches_url = "https://api.github.com/repos/{}/{}/branches".format(user,repo)
            branches = len(requests.get(branches_url, headers=headers).json())
            dt[repo]["branches"] = branches

            # Retrieve commit activity details
            commit_url = "https://api.github.com/repos/{}/{}/stats/commit_activity".format(user,repo)
            commits = requests.get(commit_url, headers=headers).json()
            dt[repo]["total_commits"] = sum([c["total"] for c in commits])

            # Retrieve contributors details
            contributors_url = "https://api.github.com/repos/{}/{}/contributors".format(user,repo)
            contributors = requests.get(contributors_url, headers=headers).json()
            dt[repo]["contributors"] = [c["login"] for c in contributors]

            # Retrieve clones details
            clone_url = "https://api.github.com/repos/{}/{}/traffic/clones".format(user,repo)
            clones = requests.get(clone_url, headers=headers).json()
            dt[repo]["clones"] = {"count": clones["count"], "uniques": clones["uniques"]}
            
            # Retrieve views(visitors) details
            views_url =" https://api.github.com/repos/{}/{}/traffic/views".format(user,repo)
            views = requests.get(views_url, headers=headers).json()
            dt[repo]["visitors"] = {"uniques": views["uniques"], "count": views["count"]}
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
    resp = requests.get('https://api.github.com/users/{}/repos'.format(user), headers=headers)
    if resp.status_code == 200:
        # retrive response body
        d = resp.json()
        info_list = ["forks", "languages_url", "contributors_url", "branches_url"]
        dt = {repo["name"]:{k:repo[k] for k in info_list} for repo in d if repo["name"]==repo_name}
        for repo in dt.keys():
            # Retrieve language details
            languages_url = "https://api.github.com/repos/{}/{}/languages".format(user,repo)
            languages = requests.get(languages_url, headers=headers).json()
            total_contribs = sum([languages[l] for l in languages])
            lang_list = [(l, float("{:.2f}".format(languages[l]/total_contribs * 100))) \
                                for l in languages]
            lang_list.sort(key=lambda x:x[1], reverse=True)
            dt[repo]["languages"] = lang_list[:3]

            # Retrieve branches details
            branches_url = "https://api.github.com/repos/{}/{}/branches".format(user,repo)
            branches = len(requests.get(branches_url, headers=headers).json())
            dt[repo]["branches"] = branches

            # Retrieve commit activity details
            commit_url = "https://api.github.com/repos/{}/{}/stats/commit_activity".format(user,repo)
            commits = requests.get(commit_url, headers=headers).json()
            dt[repo]["commits"] = {"total_commits" : sum([c["total"] for c in commits])}
            dt[repo]["commits"]["previous_week"] = commits[-2]["total"]
            dt[repo]["commits"]["current_week"] = commits[-1]["total"]

            # Retrieve contributors details
            contributors_url = "https://api.github.com/repos/{}/{}/contributors".format(user,repo)
            contributors = requests.get(contributors_url, headers=headers).json()
            dt[repo]["contributors"] = [c["login"] for c in contributors]

            # Retrieve clones details
            clone_url = "https://api.github.com/repos/{}/{}/traffic/clones".format(user,repo)
            clones = requests.get(clone_url, headers=headers).json()
            dt[repo]["clones"] = {"count": clones["count"], "uniques": clones["uniques"]}
            
            # Retrieve views(visitors) details
            views_url =" https://api.github.com/repos/{}/{}/traffic/views".format(user,repo)
            views = requests.get(views_url, headers=headers).json()
            dt[repo]["visitors"] = {"uniques": views["uniques"], "count": views["count"]}
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
            
            # check if the repo contains python files
            if "Python" in repo_details[0]["language"]:

                # retrieve clone url
                clone_url = repo_details[0]["clone_url"]

                # dir for cloned repos
                tmp_dir = "tmp"

                # dir for named repo
                repo_path = "{}/{}".format(tmp_dir, repo_name)
                
                if not os.path.exists(tmp_dir):
                    os.mkdir(tmp_dir)

                if os.path.exists(repo_path):
                    shutil.rmtree(repo_path)

                os.mkdir(repo_path)

                # run cmd process to clone repo
                process = subprocess.Popen(["git", "clone", clone_url, repo_path],
                     stdout=subprocess.PIPE, 
                     stderr=subprocess.PIPE,
                     universal_newlines=True)
                stdout, stderr = process.communicate()

                # if there is no error
                if process.returncode == 0:

                   
                    # find the diffs and save them 
                    os.chdir("tmp/GitHub_Analyzer_API")

                    # function here
                    py_files = [(os.path.join(root, fn), os.path.join(root, "changed_"+fn)) for root, _, files in os.walk(".", topdown=False) 
                                for fn in files if fn.endswith(".py")]

                    commit_sha = []

                    for tup in py_files:

                        # function here
                        process = subprocess.Popen(["git", "log", "--follow", tup[0]],
                                                    stdout=subprocess.PIPE, 
                                                    stderr=subprocess.PIPE,
                                                    universal_newlines=True)

                        stdout, stderr = process.communicate()

                        # function here
                        lines = stdout.split("\n")
                        stdout = [i.split(" ")[1] for i in lines if i.startswith("commit")]
                        
                        if len(stdout) > 2:
                            commit_sha.append((stdout[-1], stdout[0]))
                        else:
                            commit_sha.append((stdout[0], stdout[0]))
                    
                    additions_dict = dict()
                    for tup in zip(py_files, commit_sha):
                        # function here
                        process = subprocess.Popen(["git", "diff", tup[1][0], 
                                                    tup[1][1], "--", tup[0][0]],
                                                    stdout=subprocess.PIPE, 
                                                    stderr=subprocess.PIPE,
                                                    universal_newlines=True)

                        stdout, stderr = process.communicate()


                        # function here
                        lines = stdout.split("\n")
                        
                        additions = lines[4].split(" ")[2][1:].replace("+","")
                        if "," in additions:
                            additions = additions.replace(",","")
                        
                        additions_dict[tup[0][0]] = int(additions)
                        stdout = [i[1:] for i in lines[4:] if i.startswith("+")]

                        # function here 
                        with open(tup[0][1], "w") as f:
                            f.write("\n".join(stdout))
                    


                    analysis_dict = {"cyclomatic_complexity":"cc", "raw_metrics":"raw", "maintainability_index":"mi"}
                    analysis_results = {}
                    for k,v in analysis_dict.items():

                        process = subprocess.Popen(["radon", v, "./", "-s", "-j"],
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE,
                            universal_newlines=True)
                        stdout, stderr = process.communicate()
                        
                        # if there is no error
                        if process.returncode == 0:
                            analysis_results[k] = json.loads(stdout.strip())
                        else:
                             analysis_results[k] = json.loads(stderr.strip())
                    
                    # delete tmp_dir after checking code metrics
                    os.chdir("../")
                    shutil.rmtree(repo_path.split("/")[1])

                    return jsonify({"analysis_results":analysis_results, "commit_additions":additions_dict})

                    
                else:
                    return jsonify({"error" : stderr})

            else:
                jsonify({"error":"repository does not contain python files"})

        else:
            jsonify({"error":"repository not found"})
    
    else:
        return jsonify({"error":"Not Found"})



if __name__ == "__main__":
    app.run(debug=True)