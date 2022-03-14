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
            branches_url = "https://api.github.com/repos/{}/{}/branches"
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


if __name__ == "__main__":
    app.run(debug=True)