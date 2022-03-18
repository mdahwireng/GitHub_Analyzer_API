import requests
import os
import subprocess




def send_get_req(_url, _header=None) -> tuple:
    """
    Sends a get request given a url and a header(optional) and returns a tuple of response and 
    the status code

    Args:
        _url(str): url to send the request to
        _header(dict): header to attach to the request (optional) default: None

    Returns:
        response, response status code
    """
    if _header:
        resp = requests.get(_url, headers=_header)
    else:
        resp = requests.get(_url)
    return resp, resp.status_code


def retrieve_topk_langs(user, repo, headers, topk=3) -> list:
    """
    Retrieves topk languages in a github repository. 
    Returns list of tuple of language and percentage of language in repository

    Args:
        user(str): github username
        repo(str): name of repo to retrieve meta data from
        headers(dict): header to attach to the request
        topk(int): the number of top languages to retrieve, default = 3

    Returns:
        list of tuple of language and percentage of language in repository
    """

    languages_url = "https://api.github.com/repos/{}/{}/languages".format(user,repo)
    languages = send_get_req(_url=languages_url, _header=headers)[0].json()
    
    #find the total contribution of all languages
    total_contribs = sum([languages[l] for l in languages]) 

    #calculate % of language contribution
    lang_list = [(l, float("{:.2f}".format(languages[l]/total_contribs * 100))) \
                        for l in languages]                 
    
    #sort languages by % of contribution
    lang_list.sort(key=lambda x:x[1], reverse=True)         
    
    #return topk languages
    return lang_list[:topk]



def retrieve_num_branches(user, repo, headers) -> int:
    """
    Retrieves the number of branches in a github repository. 
    Returns integer of the number of branches

    Args:
        user(str): github username
        repo(str): name of repo to retrieve meta data from
        headers(dict): header to attach to the request

    Returns:
        integer of the number of branches
    """

    branches_url = "https://api.github.com/repos/{}/{}/branches".format(user,repo)

    # retrieve number of branches and return the value
    return len(send_get_req(_url=branches_url, _header=headers)[0].json())
   


def retrieve_num_commits(user, repo, headers) -> int:
    """
    Retrieves the number of commits in a github repository. 
    Returns integer of the number of commits

    Args:
        user(str): github username
        repo(str): name of repo to retrieve meta data from
        headers(dict): header to attach to the request

    Returns:
        integer of the number of commits
    """

    commit_url = "https://api.github.com/repos/{}/{}/stats/commit_activity".format(user,repo)
    commits = send_get_req(_url=commit_url, _header=headers)[0].json()
    
    # retrieve and return the total number of commits
    return sum([c["total"] for c in commits])
    

def retrieve_contributors(user, repo, headers) -> list:
    """
    Retrieves the github usernames of all contributors to a github repository. 
    Returns list of contributors

    Args:
        user(str): github username
        repo(str): name of repo to retrieve meta data from
        headers(dict): header to attach to the request

    Returns:
        list of contributors
    """

    contributors_url = "https://api.github.com/repos/{}/{}/contributors".format(user,repo)
    contributors = send_get_req(_url=contributors_url, _header=headers)[0].json()
    
    # retrieve and return the list of contributors
    return [c["login"] for c in contributors]

    


def retrieve_clone_details(user, repo, headers) -> dict:
    """
    Retrieves the counts and unique counts of the clones of a github repository. 
    Returns dictionary of clone details

    Args:
        user(str): github username
        repo(str): name of repo to retrieve meta data from
        headers(dict): header to attach to the request

    Returns:
        dictionary of clone details
    """

    clone_url = "https://api.github.com/repos/{}/{}/traffic/clones".format(user,repo)
    clones = send_get_req(_url=clone_url, _header=headers)[0].json()
    
    # retrieve and return the dictionary of clone details
    return {"count": clones["count"], "uniques": clones["uniques"]}



def retrieve_views_details(user, repo, headers) -> dict:
    """
    Retrieves the counts and unique counts of the views of a github repository. 
    Returns dictionary of clone details

    Args:
        user(str): github username
        repo_name(str): name of repo to retrieve meta data from
        headers(dict): header to attach to the request

    Returns:
        dictionary of clone details
    """

    views_url =" https://api.github.com/repos/{}/{}/traffic/views".format(user,repo)
    views = send_get_req(_url=views_url, _header=headers)[0].json()
    
    # retrieve and return the dictionary of view details
    return {"uniques": views["uniques"], "count": views["count"]}




def retrieve_repo_meta(resp_json, headers, user) -> dict:
    """
    Retrieves repo meta data from response json and returns a dictionary of the details

    Args:
        resp_json(json): url to send the request to
        headers(dict): header to attach to the request
        user(str): github username

    Returns:
        dictionary of the details
    """
    dt = resp_json
    for repo in dt.keys():

        # Retrieve language details
        dt[repo]["languages"] = retrieve_topk_langs(user, repo, headers, topk=3)

        # Retrieve branches details
        dt[repo]["branches"] = retrieve_num_branches(user, repo, headers)

        # Retrieve commit activity details
        dt[repo]["total_commits"] = retrieve_num_commits(user, repo, headers)

        # Retrieve contributors details
        dt[repo]["contributors"] = retrieve_contributors(user, repo, headers)

        # Retrieve clones details
        dt[repo]["clones"] = retrieve_clone_details(user, repo, headers)
        
        # Retrieve views(visitors) details
        dt[repo]["visitors"] = retrieve_views_details(user, repo, headers)

    return dt



def check_lang_exit(repo_dict, language) -> bool:
    """
    Takes a dictionary of repository details and name of language files.
    Returns a boolean to indicate if language file is present in repository.

    Args:
        repo_dict(dict): dictionary or reponse with repository details
        language(str): name of language

    Returns:
        A boolean to indicate if language file is present in repository
    """
    
    return language in repo_dict["language"]




def run_cmd_process(cmd_list) -> tuple:
    """
    Takes a list of elements of a shell command and executes the command
    Returns a tuple of the output, error and return code of the process.

    Args:
        cmd_list(list): list of elements of the shell command

    Returns:
        A tuple of the output, error and return code of the process
    """

    process = subprocess.Popen(cmd_list,
                     stdout=subprocess.PIPE, 
                     stderr=subprocess.PIPE,
                     universal_newlines=True)
    
    # retrieve the output and error
    stdout, stderr = process.communicate()

    return stdout, stderr, process.returncode



def retriev_files(path, file_ext) -> list:
    """
    Takes the path to the directory where search is to be done recursively and 
    the file extention of files to look for
    Returns a list of tuples of the relative path of language files , relative path of 
    language files with filenames prefixed with changed

    Args:
        path(str): path to the directory where search is to be done recursively
        file_ext(str): file extention of files to look for with the "." included
                        example ".py"

    Returns:
        A list of tuples of the relative path of language files , relative path of language files 
        with filenames prefixed with changed
    """
    return [(os.path.join(root, fn), os.path.join(root, "changed_"+fn)) 
            for root, _, files in os.walk(path, topdown=False) 
            for fn in files if fn.endswith(file_ext)]



def retrieve_init_last_commit_sha(stdout) -> tuple:
    """
    Takes the out put from a git diff cmd process and retrieves the additions 
    and the content of the changed files

    Args:
        stdout: out put from a git diff cmd process

    Returns:
        A tuples the first and the most current commit shas
    """

    # split the output into lines
    lines = stdout.split("\n")

    # retrieve all the commit shas
    sha_lines = [i.split(" ")[1] for i in lines if i.startswith("commit")]
    if len(sha_lines) > 2:
        # return the first and the most current
        return (sha_lines[-1], sha_lines[0])
    else:
        # return the only sha in both index 0 and 1
        return (sha_lines[0], sha_lines[0])

    



def retrieve_diff_details(stdout) -> tuple:
    """
    Takes the out put from a git log cmd process and retrieves the first and the most current commit shas

    Args:
        stdout: out put from a git log cmd process

    Returns:
        A tuples the additions and the contents that has been added
    """

    # split the output into lines
    lines = stdout.split("\n")

    # retireve additions from line with addition details                    
    additions = lines[4].split(" ")[2][1:].replace("+","")
    
    # replace commas in additions quantity
    if "," in additions:
        additions = additions.replace(",","")

    return int(additions), [i[1:] for i in lines[4:] if i.startswith("+")]



 