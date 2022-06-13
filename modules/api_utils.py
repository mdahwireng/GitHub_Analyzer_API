import json
import shutil
import requests
import os
import subprocess
import lizard
from radon.complexity import cc_rank
from radon.metrics import mi_rank

from modules.Retrieve_Commit_History import Retrieve_Commit_History



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


def retrieve_langs(user, repo, headers) -> dict:
    """
    Retrieves languages in a github repository. 
    Returns dictionary of language with language name as keys their 
    raw values of contribution as values in repository

    Args:
        user(str): github username
        repo(str): name of repo to retrieve meta data from
        headers(dict): header to attach to the request

    Returns:
        dictionary of language with language name as keys their 
        raw values of contribution as values in repository
    """
    languages_url = "https://api.github.com/repos/{}/{}/languages".format(user,repo)
    return send_get_req(_url=languages_url, _header=headers)[0].json()


def get_langs_contribs(langs_dict) -> list:
    """
    Creates percentage of contribution for languages in a github repository. 
    Returns dictionary of language (keys) and percentage of language (values) in repository

    Args:
        langs_dict(dict): dictionary of language with language name as keys their 
                            raw values of contribution as values in repository
    Returns:
        list of tuple of language and percentage of language in repository
    """
    #find the total contribution of all languages
    total_contribs = sum(list(langs_dict.values())) 

    #calculate  and return % of language contribution
    return [(l[0], float("{:.2f}".format(l[1]/total_contribs * 100))) \
                        for l in langs_dict.items()]


def retrieve_topk_langs(lang_list, topk=3) -> list:
    """
    Retrieves topk languages in a github repository. 
    Returns list of tuple of language and percentage of language in repository

    Args:
        lang_list(list): list of tuple of language and percentage of language in repository
        topk(int): the number of top languages to retrieve, default = 3

    Returns:
        list of tuple of language and percentage of language in repository
    """                
    #sort languages by % of contribution
    lang_list.sort(key=lambda x:x[1], reverse=True)         
    
    #return topk languages
    return lang_list[:topk]



def get_topk_langs(user, repo, headers, topk=3) -> list:
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
    #get lang details
    langs_dict = retrieve_langs(user, repo, headers)
    langs_list = get_langs_contribs(langs_dict)

    #sort languages by % of contribution
    langs_list = retrieve_topk_langs(langs_list, topk=3)        
    
    #return topk languages
    return langs_list[:topk]




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


def retrieve_branch_sha(user, repo, headers, branch) -> str:
    """
    Retrieves the sha of a branch in a github repository. 
    Returns string of the sha of the branch

    Args:
        user(str): github username
        repo(str): name of repo to retrieve meta data from
        headers(dict): header to attach to the request
        branch(str): name of branch to retrieve sha of

    Returns:
        string of the sha of the branch
    """
    branch_url = "https://api.github.com/repos/{}/{}/branches/{}".format(user,repo,branch)
    return send_get_req(_url=branch_url, _header=headers)[0].json()["commit"]["sha"]

   


def retrieve_num_commits(user, repo, headers, sha=None) -> int:
    """
    Retrieves the number of commits in a github repository. 
    Returns integer of the number of commits

    Args:
        user(str): github username
        repo(str): name of repo to retrieve meta data from
        headers(dict): header to attach to the request
        sha(str): sha of branch to retrieve number of commits of

    Returns:
        integer of the number of commits
    """

    _url = "https://api.github.com/repos/{}/{}/commits?per_page=1&page=1"
    commit_url = _url.format(user,repo)
    if sha:
        _url = _url + "&sha={}"
        commit_url = _url.format(user,repo,sha)
    try:
        resp = send_get_req(_url=commit_url, _header=headers)[0]
        commits = resp.headers["link"].split(',')[1].split("=")[2][:-6]

        if sha:
            commits = resp.headers["link"].split(',')[1].split("=")[2][:-4]
    
        # retrieve and return the total number of commits
        return int(commits)
    except:
        return None
    

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
    try:
        contributors = send_get_req(_url=contributors_url, _header=headers)[0].json()
    
        # retrieve and return the list of contributors
        return [c["login"] for c in contributors]
    except:
        return None

    


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
    try:
        clones = send_get_req(_url=clone_url, _header=headers)[0].json()
    
        # retrieve and return the dictionary of clone details
        return {"count": clones["count"], "uniques": clones["uniques"]}
    except:
        return None


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
    try:
        views = send_get_req(_url=views_url, _header=headers)[0].json()
    
        # retrieve and return the dictionary of view details
        return {"uniques": views["uniques"], "count": views["count"]}
    except:
        return None



def retrieve_repo_meta(resp_json, headers, user, branch) -> dict:
    """
    Retrieves repo meta data from response json and returns a dictionary of the details

    Args:
        resp_json(json): url to send the request to
        headers(dict): header to attach to the request
        user(str): github username
        branch(str): name of branch to retrieve sha of

    Returns:
        dictionary of the details
    """
    dt = resp_json
    for repo in dt.keys():

        # Retrieve language details
        dt[repo]["languages"] = get_topk_langs(user, repo, headers, topk=3)

        # Retrieve branches details
        dt[repo]["branches"] = retrieve_num_branches(user, repo, headers)

        # Retrieve branch sha
        if branch:
            branch_sha = retrieve_branch_sha(user, repo, headers, branch)

            # Retrieve commit activity details
            dt[repo]["total_commits"] = retrieve_num_commits(user, repo, headers, sha=branch_sha)

        else:
            # Retrieve commit activity details
            dt[repo]["total_commits"] = retrieve_num_commits(user, repo, headers)

        # Retrieve contributors details
        dt[repo]["contributors"] = retrieve_contributors(user, repo, headers)

        """# Retrieve clones details
        try:
            dt[repo]["clones"] = retrieve_clone_details(user, repo, headers)
        except:
            dt[repo]["clones"] = "Cannot get Acess"
        try:
            # Retrieve views(visitors) details
            dt[repo]["visitors"] = retrieve_views_details(user, repo, headers)
        except:
             dt[repo]["visitors"] = "Cannot get Acess" """
    return dt



def check_lang_exit(user, repo, headers, lang_list) -> bool:
    """
    Takes a dictionary of repository details and name of language files.
    Returns a boolean to indicate if language file is present in repository.

    Args:
        repo_dict(dict): dictionary or reponse with repository details
        language(list): list of name(s) of language

    Returns:
        A boolean to indicate if language file is present in repository
    """
    to_lower = lambda x:[i.lower() for i in x]
    repo_lang_list = to_lower(retrieve_langs(user, repo, headers).keys())

    return True in [l_c.lower() == l_r for l_c in lang_list for l_r in repo_lang_list]




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
        file_ext(lst): file extention of files to look for with the "." included
                        example ".py"

    Returns:
        A list of tuples of the relative path of language files , relative path of language files 
        with filenames prefixed with changed
    """
    r_list = [(os.path.join(root, fn), os.path.join(root, "changed_"+fn)) 
            for root, _, files in os.walk(path, topdown=False) 
            if not root.startswith("__") and not root.startswith("..") 
            for fn in files for ext in file_ext if fn.endswith(ext)]

    filter_list = ["lib","bin","etc", "include", "share", "var", "lib64", "venv"]
    take_out = []
    for root in filter_list:
        for tup in r_list:
            path_split_l = tup[0].lower().split("/")

            if root in path_split_l:

                path_split = tup[0].split("/")
                dir_path = "/".join(path_split[ : path_split_l.index(root)+1])
                take_out.append(tup)
                try:
                    shutil.rmtree(dir_path)
                except:
                    pass
                #r_list.remove(tup)

    r_list = [tup for tup in r_list if tup not in take_out]

    return r_list




def retrieve_init_last_commit_sha(stdout) -> tuple:
    """
    Takes the out put from a git diff cmd process and retrieves the additions 
    and the content of the changed files

    Args:
        stdout: out put from a git diff cmd process

    Returns:
        A tuples of the first and the most current commit shas
    """

    # split the output into lines
    lines = stdout.split("\n")

    # retrieve all the commit shas
    sha_lines = [i.split(" ")[1] for i in lines if i.startswith("commit")]
    if len(sha_lines) > 2:
        # return the first and the most current
        return (sha_lines[-1], sha_lines[0])
    else:
        try:
            # return the only sha in index 0
            return (sha_lines[0], sha_lines[0])
        except:
            # return empty None
            return (None, None)

    



def retrieve_diff_details(stdout) -> tuple:
    """
    Takes the out put from a git log cmd process and retrieves the first and the most current commit shas

    Args:
        stdout: out put from a git log cmd process

    Returns:
        A tuples of the additions and the contents that has been added
    """
    # split the output into lines
    lines = stdout.split("\n")
    
    if len(lines)>5:
        # retireve additions from line with addition details                    
        try:
            additions = lines[4].split(" ")[2][1:].replace("+","")
        except:
            additions = "0"
        
        # replace commas in additions quantity
        if "," in additions:
            additions = additions.replace(",","")

        try:
            return int(additions), [i[1:] for i in lines[4:] if i.startswith("+")]
        except:
            return 0, [""]
    else:
        return 0, [""]


def save_file(file_name, content) -> None:
    """
    Takes a filename and content. Then writes the content to an opened file and save it 
    with the filename given

    Args:
        file_name(str): file name to save the content with
        content(list): list of content with each line as an element

    Returns:
        None
    """
    with open(file_name, "w") as f:
        f.write("\n".join(content))


def create_repo_dir(repo_name, tmp_dir="tmp") -> str:
    """
    Takes a temporary directory and repo_name and then creates a directory named as the name of the repository.
    Returns the relative path to the created directory

    Args:
        tmp_dir(str): the name of the temporary directory. Default = "tmp"
        repo_name(str): the name of the repository to be used for naming the directory

    Returns:
        A string of the relative path to the created directory
    """
    # dir for named repo
    repo_path = "{}/{}".format(tmp_dir, repo_name)
    
    # create temporary folder if it does not exist
    if not os.path.exists(tmp_dir):
        os.mkdir(tmp_dir)
    
    # delete directory named just as repository name if it exists
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)

    # create directory named just as repository name
    os.mkdir(repo_path)

    return repo_path



def clone_repo(clone_url, repo_path) -> tuple:
    """
    Runs a sub process to clone reposiories given the clone url and the path to the directory to clone into.
    Returns the stderr and return code of the sub process.

    Args:
        clone_url(str): the git clone url of the repository to be cloned
        repo_path(str): the path to the directory to clone into

    Returns:
        the stderr and return code of the sub process.
    """
    # run cmd process to clone repo
    stdout, stderr, return_code = run_cmd_process(cmd_list = ["git", "clone", clone_url, repo_path])

    return stderr, return_code


def check_out_branch(branch_name) -> tuple:
    """
    Runs a sub process to checkout a branch given the branch name.
    Returns the stderr and return code of the sub process.

    Args:
        branch_name(str): the name of the branch to checkout

    Returns:
        the stderr and return code of the sub process.
    """
    # run cmd process to clone repo
    stdout, stderr, return_code = run_cmd_process(cmd_list = ["git", "checkout", branch_name])

    return stderr, return_code


def get_additions_and_save_contents(files, commit_sha):
    """
    Retrieves the additions added in a file between two given commits and saves the content of the changes made.
    Returns a dictionary of filenames as keys and the additions added as values.

    Args:
        files(str): A list of tuples of the relative path of language files , relative path of language files 
                    with filenames prefixed with changed
        commit_sha(str): tuples of the initial and the latter commit shas

    Returns:
        A dictionary of filenames as keys and the additions added as values.
    """

    additions_dict = dict()
    for tup in zip(files, commit_sha):
        if tup[1][0] is not None:
            # run git diff command
            stdout, stderr, _ = run_cmd_process(cmd_list=["git", "diff", tup[1][0], tup[1][1], "--", tup[0][0]])
            
            # retrieve the additions and the content of the changed files
            additions, content = retrieve_diff_details(stdout)
            
            # save the content of the changed files
            save_file(file_name=tup[0][1], content=content)

            # add the additions to the dictionary
            additions_dict[tup[0][0]] = additions
        
        else:
            # if the initial commit sha is None, then the file has not been changed
            additions_dict[tup[0][0]] = 0

    return additions_dict

def get_hal_summary(hal_result_dict)->dict:
    """
    Takes a dictionary of filenames as keys and the halstead complexity metrics as values.
    Returns a dictionary of filenames as keys and the hal summary as values.
    
    Args:
        hal_result_dict(dict): A dictionary of filenames as keys and the additions added as values.
        
    Returns: 
        A dictionary of filenames as keys and the hal summary as values.
    """
    # keys for hal summary
    keys = ["difficulty", "effort", "time"]

    # create a dictionary of hal summary
    hal_summary_dict = dict()

    # loop through all the files
    for f in hal_result_dict.keys():
        if "error" in hal_result_dict[f].keys():
            hal_summary_dict[f] = {keys[i]:0 for i in range(len(keys))}
        else:
            hld = hal_result_dict[f]["total"][-4:-1]
            hal_summary_dict[f] = {keys[i]:hld[i] for i in range(len(keys))}
    
    return hal_summary_dict


def get_file_checks(exclude_list, file_extensions, files_to_check, dirs_to_check, path="./"):
    """
    Get the file checks for a given path.
    

    Args:
        path (str): The path to check.
        exclude_list (list): A list of directories to exclude.
        file_extensions (list): A list of file extensions to check.
        files_to_check (list): A list of files to check.
        dirs_to_check (list): A list of directories to check.

    Returns:
        dict: A dictionary of the file checks and number of files
    """
    exclude = exclude_list
    exclude_roots = ["./"+i.lower() for i in exclude]
    count_dict = {"num_dirs":0, "num_files":0}
    extension_checks = {"num_"+ ext.lower():0 for ext in file_extensions}
    file_checks = {f.lower():False for f in files_to_check}
    dir_checks = {dir.lower():False for dir in dirs_to_check}


    for i in os.walk(path):
        if True in [False if i[0].lower().startswith(e.lower() + "/") 
                    or i[0].lower() == e.lower() 
                    or i[0].__contains__("/" + e.lower() + "/")
                    else True for e in exclude_roots ] or len(exclude_roots) == 0:
            
            dirs = i[1]
            _files = i[2]

            # check for the existence of interested files and file extentions
            for f in _files:
                if f.lower() in file_checks:
                    file_checks[f.lower()] = True

            for ig in exclude:
                # remove files from the directories to exclude
                for f in _files:
                     if f.lower().startswith(ig.lower() + "/") or f.lower() == ig.lower() or f.__contains__("/" + ig.lower() + "/"):
                         _files.remove(f)
                # remove the directories to exclude
                try:
                    dirs.remove(ig)
                except:
                    pass
            
            # count directories
            count_dict["num_dirs"] += len(dirs)

            # count files
            count_dict["num_files"] += len(_files)
            
            # check for the existence of interesting dirs
            for dir in dirs:
                if dir.lower() in dir_checks:
                    dir_checks[dir.lower()] = True
            
            
            for f in _files:
                # check for the existence of interested file extentions
                for ext in file_extensions:
                    if f.endswith(ext):
                        extension_checks["num_"+ext] += 1

        else:
            print ("{} is excluded\n".format(i[0]))


    checks_results_dict = dict()
    checks_results_dict["interested_files"] = file_checks
    checks_results_dict["interested_files"].update(dir_checks)
    checks_results_dict["interested_files"] = [{"name":k, "present":v} for k,v in checks_results_dict["interested_files"].items()]
    checks_results_dict.update(count_dict)
    checks_results_dict.update(extension_checks)

    return checks_results_dict



def run_pyanalysis(path="./") -> dict:
    """
    Runs a subprocess to under take python code analysis recursively given the path to a directory on which 
    to run the analysis.
    Returns 

    Args:
        path(str): path to the directory on which code analysis is carried out on. Default = "./"

    Returns:
        A dictionary of filenames as keys and the dictionary of code metrics as values.
    """
    analysis_dict = {"halstead_complexity":"hal","cyclomatic_complexity":"cc", "raw_metrics":"raw", "maintainability_index":"mi"}
    analysis_results = {}
    for k,v in analysis_dict.items():
        if k == "halstead_complexity":
            print(k,"\n")
            stdout, stderr, return_code = run_cmd_process(cmd_list=["radon", v, path , "-j"])

            if return_code == 0:
                analysis_results[k] = get_hal_summary(json.loads(stdout.strip()))
                print("Success\n")
                
            else:
                analysis_results[k] = json.loads(stderr.strip())
                print("Error\n")
        
        else:
            # run radon code analysis
            print(k, "\n")
            stdout, stderr, return_code = run_cmd_process(cmd_list=["radon", v, path, "-s", "-j"])
            
            # if there is no error
            if return_code == 0:
                analysis_results[k] = json.loads(stdout.strip())
                print("Success\n")
            else:
                analysis_results[k] = json.loads(stderr.strip())
                print("Error\n")
    return analysis_results

def convert_nb_to_py(path_list):
    """
    Converts a notebook to a python file.

    Args:
        path_list(list): A list of paths to the notebooks to be converted.

    Returns:
        A list of paths to the converted python files.
    """
    conversion_success = []
    for path in path_list:
        stdout, stderr, return_code = run_cmd_process(cmd_list=["jupyter", "nbconvert", path, "--to", "python"])
        if return_code == 0:
            conversion_success.append(True)
        else:
            conversion_success.append(False)

    out_dict = {"success":[], "fail":[]}
    for i in range(len(conversion_success)):
        if conversion_success[i]:
            out_dict["success"].append(path_list[i])
        else:
            out_dict["fail"].append(path_list[i])
    return out_dict


def run_to_get_adds_and_save_content(user, repo_name, repo_dict, file_ext, branch, path="./") -> tuple:
    """
    Abstract a processes involved from cloning and retrieving of commit shas to comparing changes that has occured between
    the first and current commits as well as retrieval of commit history on a given branch.
    Returns a tuple of stderr, return_code of the cloning process, additions_dict, files, commit_history_dict.

    Args:
        user(str): The user name of the github repository.
        repo_name(str): the name of the repository to be used for naming the directory
        repo_dict(dict): dictionary of metadata returned as a response to a request to get metadata on repositoy
        path(str): path to the directory where search is to be done recursively, default = "./"
        file_ext(lst): file extention of files to look for with the "." included
                        example ".py"
        branch(str): the branch to be used for the analysis

    Returns:
        A tuple of stderr, return_code of the cloning process, additions_dict and files
    """
    # dir for named repo
    repo_path = create_repo_dir(repo_name)

    # clone repo
    stderr, return_code = clone_repo(repo_path=repo_path, clone_url=repo_dict["clone_url"])
   
    # if there is no error
    if return_code == 0:

        # change working directory to cloned reository
        os.chdir(repo_path)

        default_branch = None

        github_dict = {"owner":user, "repo":repo_name}

        # checkout to branch
        if branch:
            default_branch = get_git_branch()
            stderr, return_code =  check_out_branch(branch_name=branch)

            # retrive commit history
            branch_dict = {"default":default_branch, "branch":branch}
            ret_commit = Retrieve_Commit_History(github_dict=github_dict, branch_dict=branch_dict)
        else:
            # retrieve commit history
            ret_commit = Retrieve_Commit_History(github_dict=github_dict)
        
        commit_history_dict = ret_commit.get_commit_history_and_contributors()

        # check for the existence of files with the given file extension
        exclude_list=[".git", ".ipynb_checkpoints", "__pycache__", "node_modules"]
        file_extensions=["py","js","ipynb"]
        files_to_check=[".gitignore", "README.md", "requirements.txt", "dockerfile", ".dvcignore"]
        dirs_to_check=[".github", ".dvc"]

        file_check_results =  get_file_checks(path=path, exclude_list=exclude_list, file_extensions=file_extensions, files_to_check=files_to_check , dirs_to_check=dirs_to_check)
        
        # retrieve jupyter notebook paths
        nb_paths_list = [tup[0] for tup in retriev_files(path=path, file_ext=[".ipynb"])]

        # convert jupyter notebook to python scripts
        if file_check_results["num_ipynb"] > 0:
            print("Converting notebooks to python scripts...")
            _cnvt = convert_nb_to_py(path_list=nb_paths_list)
        
        #run_cmd_process(cmd_list=["git", "add", "*"])
        #run_cmd_process(cmd_list=["git", "commit", "-m", "converted jupyter notebooks to python scripts"])

        # rerieve language files
        files = retriev_files(file_ext=file_ext, path=path)

        if branch and default_branch != branch:
            commit_sha = [retrieve_init_last_commit_sha(run_cmd_process(cmd_list=["git", "log", "{}..{}".format(default_branch,branch), "--follow", tup[0]])[0])
                        for tup in files]
        else:
            commit_sha = [retrieve_init_last_commit_sha(run_cmd_process(cmd_list=["git", "log", "--follow", tup[0]])[0])
                        for tup in files]

        additions_dict = get_additions_and_save_contents(files, commit_sha)

        return stderr, return_code, additions_dict, files, file_check_results, commit_history_dict

    else:
        return stderr, return_code, dict(), list(), dict(), dict()



def run_jsanalysis(files):
    """
    Runs JavaScript code analysis on given JavaScript files in a list of files paths.
    Returns a dictionary of filenames as keys and the dictionary of code metrics as values

    Args:
        files(list): list of files paths
    Returns:
        A dictionary of filenames as keys and the dictionary of code metrics as values.
    """
    # retrieve JavaScript files
    files = [f for f in files if f.endswith(".js")]

    # run analysis
    analysis_results = {f:[i.__dict__ for i in lizard.analyze_file(f).function_list] for f in files}
    
    return analysis_results


def get_cc_avg(cc_list, cc_key):
    return sum([r[cc_key] for r  in cc_list])/len(cc_list)

def get_cc_summary(analysis_results, cc_key):
    return  {
                f:
                    (
                        {
                        "cc": get_cc_avg(analysis_results["cyclomatic_complexity"][f], cc_key),
                        "rank": cc_rank(get_cc_avg(analysis_results["cyclomatic_complexity"][f], cc_key))
                        }
                        if isinstance(analysis_results["cyclomatic_complexity"][f], list) else None
                    ) 
                    for f in analysis_results["cyclomatic_complexity"]
            }


def get_type_details(_type, v_list)->dict:
    """
    Retrieves the details of a type from the results of cc_analysis dictionary

    Args:
        _type (str): The type of the details to be retrieved
        v_dict (dict): The list of dictionaries containing the results of cc_analysis
    Returns:
        A dictionary of the number of the type and the average number of lines of code
    """
    return {
        "num_" + _type :  [len([1 for i in v_list if i["type"]==_type])][0],
        "avg_lines_per_" + _type : [
            round(sum([i["endline"] - i["lineno"] for i in v_list if i["type"]==_type])/len([1 for i in v_list if i["type"]==_type]))
            if len([1 for i in v_list if i["type"]==_type]) > 0 else 0                     
                            ][0]
       } 



def get_file_level_summary(analysis_results, additions_dict):

    raw_metrics = {"blank": None, "comments": None, "lloc": None, "loc": None, 
                   "multi": None, "single_comments": None, "sloc": None}

    halstead = {"difficulty": None,"effort": None, "time": None}
    
    file_level = {f:dict() for f in analysis_results["raw_metrics"]}
    for f in file_level.keys():
        # get type details
        if f in analysis_results["cyclomatic_complexity"].keys() and isinstance(analysis_results["cyclomatic_complexity"][f], list):
            # functions
            hld = get_type_details("function", analysis_results["cyclomatic_complexity"][f])
            file_level[f]["num_functions"] = hld["num_function"]
            file_level[f]["avg_lines_per_function"] = hld["avg_lines_per_function"]
            # classes
            hld = get_type_details("class", analysis_results["cyclomatic_complexity"][f])
            file_level[f]["num_classes"] = hld["num_class"]
            file_level[f]["avg_lines_per_class"] = hld["avg_lines_per_class"]
            # methods
            hld = get_type_details("method", analysis_results["cyclomatic_complexity"][f])
            file_level[f]["num_methods"] = hld["num_method"]
            file_level[f]["avg_lines_per_method"] = hld["avg_lines_per_method"]
        else:
            # functions
            file_level[f]["num_functions"] = None
            file_level[f]["avg_lines_per_function"] = None
            # classes
            file_level[f]["num_classes"] = None
            file_level[f]["avg_lines_per_class"] = None
            # methods
            file_level[f]["num_methods"] = None
            file_level[f]["avg_lines_per_method"] = None

        # cyclomatic complexity 
        if f in analysis_results["cyclomatic_complexity_summary"].keys() and analysis_results["cyclomatic_complexity_summary"][f] != None:
            file_level[f]["cc"] = analysis_results["cyclomatic_complexity_summary"][f]["cc"]
            file_level[f]["cc_rank"] = analysis_results["cyclomatic_complexity_summary"][f]["rank"]
        else:
            file_level[f]["cc"] = None
            file_level[f]["cc_rank"] = None

        # maintainability index
        if f in analysis_results["maintainability_index"].keys() and "error" not in analysis_results["maintainability_index"][f].keys():
            file_level[f]["mi"] = analysis_results["maintainability_index"][f]["mi"]
            file_level[f]["mi_rank"] = analysis_results["maintainability_index"][f]["rank"]
        else:
            file_level[f]["mi"] = None
            file_level[f]["mi_rank"] = None

        # additions
        if "./"+f in additions_dict.keys():
            file_level[f]["additions"] = additions_dict["./"+f]
        else:
            file_level[f]["additions"] = None

        # raw metrics
        file_level[f].update(analysis_results["raw_metrics"][f]) 
        file_level[f].update(analysis_results["halstead_complexity"][f])
    
    
    for f in additions_dict:
        if f not in file_level.keys():
            file_level[f] = dict()
            file_level[f]["additions"] = additions_dict[f]
            file_level[f]["cc"] = None
            file_level[f]["cc_rank"] = None
            file_level[f]["mi"] = None
            file_level[f]["mi_rank"] = None
            file_level[f]["num_functions"] = None
            file_level[f]["avg_lines_per_function"] = None
            file_level[f]["num_classes"] = None
            file_level[f]["avg_lines_per_class"] = None
            file_level[f]["num_methods"] = None
            file_level[f]["avg_lines_per_method"] = None
            file_level[f].update(raw_metrics) 
            file_level[f].update(halstead)
    
    return file_level



def get_js_cc_summary(analysis_results, cc_key):
    return  {
                f:
                    (
                        {
                        "cc": get_cc_avg(analysis_results[f], cc_key),
                        "rank": cc_rank(get_cc_avg(analysis_results[f], cc_key)),
                        "nloc":  sum([i["nloc"] for i in analysis_results[f]]),
                        "length":  sum([i["length"] for i in analysis_results[f]]),
                        "token_count": sum([i["token_count"] for i in analysis_results[f]])
                        }
                        if len(analysis_results[f]) != 0 else {"cc": None, "rank": None, "nloc" : None, "length" : None,"token_count" : None}
                    ) 
                    for f in analysis_results
            }


def get_repo_level_summary(files, file_level):
    commulative_keys = ["blank","comments","lloc","loc","multi","single_comments","sloc","additions","num_functions","num_classes","num_methods","difficulty", "effort", "time"]
                
    repo_summary = {k:[] for k in file_level[list(file_level.keys())[0]].keys() if not k.endswith("_rank")}
    for k in repo_summary.keys():
        for f in file_level:
            if not f.__contains__("changed_") and k in file_level[f].keys():
                if not isinstance(file_level[f][k], str) and file_level[f][k] != None:
                    repo_summary[k].append(file_level[f][k])

    repo_summary = {k:(sum(v) if k in commulative_keys else sum(v)/len(v)) if len(v) > 0 else 0 for k,v in repo_summary.items()}
    
    try:
        repo_summary["cc_rank"] = cc_rank(repo_summary["cc"])
    except:
        repo_summary["cc_rank"] = None
    
    try:
        repo_summary["mi_rank"] = mi_rank(repo_summary["mi"])
    except:
        repo_summary["mi_rank"] = None
    
    return repo_summary


def add_js_additions(analysis_results, addition_dict):
    for f in addition_dict.keys():
        analysis_results["cyclomatic_complexity_summary"][f]["additions"] = addition_dict[f]
    return analysis_results


def get_jsrepo_level_summary(files, file_level):

    repo_summary = {k:[] for k in file_level[files[0]].keys() if k != "rank"}
    
    for k in repo_summary.keys():
        for f in file_level:
            if not f.__contains__("changed_"):
                if file_level[f][k] != None:
                    repo_summary[k].append(file_level[f][k])

    repo_summary = {k:(sum(v) if k != "cc" else sum(v)/len(v)) for k,v in repo_summary.items()}
    
    repo_summary["cc_rank"] = cc_rank(repo_summary["cc"])

    return repo_summary


def get_git_branch():
    """
    Returns the current git branch
    """
    #get branch name
    stdout, stderr, return_code = run_cmd_process(cmd_list=['git', 'branch'])
    if return_code == 0:
        branch = [a for a in stdout.split('\n') if a.find('*') >= 0][0]
        branch = branch.replace('*', '').strip()
    else:
        branch = None
    return branch


def get_recent_commit_stamp() -> dict:
    """
    Returns a dictionary of the most recent commit shas and the timestamp of the most recent commit

    Args:
        None

    Returns:
        A dictionary of the most recent commit shas and the timestamp of the most recent commit
    """
    stdout, stderr, return_code = run_cmd_process(cmd_list = ['git', 'log', '-n', '1', '--pretty=format:%H/%ct/%aN/%s'])
    if return_code == 0:
        lines = stdout.split("\n")
        if len(lines) == 1:
            details = lines[0].split("/")

            #get branch name
            branch = get_git_branch()
            return {"branch": branch, "commit_sha": details[0], "commit_ts": details[1], "author": details[2], "message": details[3]}
        else:
            return  {"branch": "", "commit_sha": "", "commit_stamp": "", "author": "", "message": ""}
    else:
        return {"error": stderr}
