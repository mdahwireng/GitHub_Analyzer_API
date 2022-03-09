import json
from flask import Flask, jsonify
import requests

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
            branches_url = "https://api.github.com/repos/{}/{}/branches"
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



@app.route('/repos_python/<string:user>/<string:token>',methods=["GET"])
def get_repo_python(user, token)->json:
    """
    Takes username and github generated token and returns json of details on the python codes in each repository

    Args:
        user(str): github account username
        token(str): github account token

    Returns:
        json of details on the python codes in each repository 
    """
    # create authourization headers for get request
    headers = {"Authorization":"Bearer {}".format(token)}
    # send get request to github api
    resp = requests.get('https://api.github.com/users/{}/repos'.format(user), headers=headers)
    if resp.status_code == 200:
        # retrive response body
        repo_file_dict = {}
        d = resp.json()

        # create function for separting python files from directories
        def separate_files_and_dir(resp):
            ext_list = ["py", "ipynb"]
            file_list = []
            dir_list = []
            # loop through response to separate files and folders
            for content in resp:
                if content["type"] == "file":
                    file_name = content["name"].lower()
                    ext = ""
                    for i in range(file_name.count('.')):
                        if i == 0:
                            ext = file_name.split('.')[-1]
                        else:
                            ext = ext.split('.')[-1]
                        
                        if i + 1 == file_name.count('.'):
                            if ext in ext_list:
                                file_list.append(content)
            
            if content["type"] == "dir":
                dir_list.append(content)

            return file_list, dir_list

    for repo in d:
        repo_resp = requests.get("https://api.github.com/repos/mdahwireng/{}/contents".format(repo["name"]), headers=headers)
        json_repo_resp = repo_resp.json()
        
        if repo_resp.status_code == 200:
            file_list, dir_list = separate_files_and_dir(json_repo_resp)

            while len(dir_list) != 0:
                loop_list = dir_list.copy()
                
                for dir in loop_list:
                    resp_ = requests.get(dir["url"], headers=headers)
                    if resp_.status_code == 200:
                        # retrive response body
                        d = resp_.json()
                        sep_tup = separate_files_and_dir(d)
                        file_list.extend(sep_tup[0])
                        dir_list.extend(sep_tup[1])
                        dir_list.remove(dir)
        
            repo_file_dict[repo["name"]] = {"files":file_list, "dir":dir_list}
            return jsonify(repo_file_dict)
        else:
            return jsonify({"error":"Not Found"}) 
         
        
    

if __name__ == "__main__":
    app.run(debug=True)