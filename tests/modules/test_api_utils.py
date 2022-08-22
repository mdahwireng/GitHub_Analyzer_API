import json
import os
import sys
import pytest
import shutil
from modules.Retrieve_Commit_History import Retrieve_Commit_History

curdir = os.path.dirname(os.path.realpath("modules/api_utils.py"))
cpath = os.path.dirname(curdir)
if not cpath in sys.path:
    sys.path.append(cpath)

from modules.api_utils import retrieve_langs, check_lang_exit, create_repo_dir, clone_repo, get_git_branch, check_out_branch, get_file_checks, retriev_files, convert_nb_to_py, run_cmd_process, retrieve_init_last_commit_sha, get_additions_and_save_contents, run_to_get_adds_and_save_content


if os.path.exists(".env/secret.json"):
    with open(".env/secret.json", "r") as s:
        secret = json.load(s)
        try:
            github_token = secret["github_token"]
            #strapi_token = secret["strapi_token"][platform]
        except:
            github_token = None
            #strapi_token = None
else:
    github_token = None
    #strapi_token = None


headers = {"Authorization":"Bearer {}".format(github_token)}
repo = "js_code_metrics_api"
repo_name = repo
user = "mdahwireng"
lang_list = ["JavaScript"]
clone_url = "https://github.com/mdahwireng/js_code_metrics_api.git"
branch_name = "other"
default_branch = "main"
file_ext=[".py", ".ipynb", ".js"]


def get_into_repo():
    repo_dir = create_repo_dir(repo_name)
    clone_repo(clone_url, repo_dir)
    cwd = os.getcwd()
    os.chdir(repo_dir)
    return cwd, repo_dir



# def test_retrieve_langs():
#     langs =  retrieve_langs(user, repo, headers)
#     assert isinstance(langs, dict), "langs is not a dictionary"
#     assert len(langs) > 0, "langs is empty"

# def test_check_lang_exit():
#     assert check_lang_exit(user, repo, headers, lang_list) == True, "JavaScript is in repo but check_lang_exit returned False"
#     assert check_lang_exit(user, repo, headers, ["Python", "JavaScript"]) == True, "JavaScript is in lang_list but check_lang_exit returned False"
#     assert check_lang_exit(user, repo, headers, ["Python"]) == False, "Python is not in repo but check_lang_exit returned True"
#     assert check_lang_exit(user, repo, headers, []) == False, "lang_list is empty but check_lang_exit returned True"
#     assert check_lang_exit(user, repo, headers, ["Python", "JavaScript", "Jupyter Notebook"]) == True, "Jupyter Notebook is not in repo but check_lang_exit returned False"


# def test_create_repo_dir():
#     actual = "tmp/{}".format(repo_name)
#     repo_dir = create_repo_dir(repo_name)
#     print(repo_dir)
#     assert os.path.exists(repo_dir), "repo_dir does not exist"
#     assert os.path.isdir(repo_dir), "repo_dir is not a directory"
#     assert repo_dir == actual, "expected {} but got {}".format(actual, repo_dir)
#     shutil.rmtree(repo_dir)


# def test_clone_repo():
#     repo_dir = create_repo_dir(repo_name)
#     clone_repo(clone_url, repo_dir) 
#     assert os.listdir(repo_dir), "clone_repo did not clone repo, repo_dir is empty"
#     shutil.rmtree(repo_dir)


# def test_get_git_branch():
#     cwd,repo_dir = get_into_repo() 
#     branch = get_git_branch()
#     assert branch == "main", "expected main but got {}".format(branch)
#     os.chdir(cwd)
#     shutil.rmtree(repo_dir)


# def test_check_out_branch():
#     cwd,repo_dir = get_into_repo() 
#     check_out_branch(branch_name)
#     branch = get_git_branch()
#     assert branch == branch_name, "expected {} but got {}".format(branch_name, branch)
#     os.chdir(cwd)
#     shutil.rmtree(repo_dir)


# def test_get_file_checks():
#     exclude_list = [".git", ".ipynb_checkpoints", "__pycache__", "node_modules",
#                         "lib", "bin", "etc", "include", "share", "var", "lib64", "venv"]
#     file_extensions = ["py", "js", "ipynb"]
#     files_to_check = [".gitignore", "README.md",
#                         "requirements.txt", "dockerfile", ".dvcignore"]
#     dirs_to_check = [".github", ".dvc"]
#     checks_results_expected = {
#                             "interested_files": [
#                                                 {"name": ".gitignore", "present": True}, 
#                                                 {"name": "readme.md", "present": True}, 
#                                                 {"name": "requirements.txt", "present": False}, 
#                                                 {"name": "dockerfile", "present": False}, 
#                                                 {"name": ".dvcignore", "present": False}, 
#                                                 {"name": ".github", "present": False}, 
#                                                 {"name": ".dvc", "present": False}
#                                                 ], 
#                             "num_dirs": 0, 
#                             "num_files": 6,
#                             "num_py": 0, 
#                             "num_js": 1, 
#                             "num_ipynb": 1
#                             }
#     cwd,repo_dir = get_into_repo()
#     checks_results_actual = get_file_checks(exclude_list, file_extensions, files_to_check, dirs_to_check)
#     assert checks_results_actual == checks_results_expected, "expected {} but got {}".format(checks_results_expected, checks_results_actual)
#     os.chdir(cwd)
#     shutil.rmtree(repo_dir)


# def test_retriev_files():
#     expected = {"py": [], "js": [("./server.js", "./changed_server.js")], "ipynb": [("./try.ipynb", "./changed_try.ipynb")]}
#     cwd,repo_dir = get_into_repo()
#     retriev_files_py_actual = retriev_files(path=".", file_ext=["py"])
#     retriev_files_js_actual = retriev_files(path=".", file_ext=["js"])
#     retriev_files_ipynb_actual = retriev_files(path=".", file_ext=["ipynb"])
    
#     assert retriev_files_py_actual == expected["py"], "expected {} but got {}".format(expected["py"], retriev_files_py_actual)
#     assert retriev_files_js_actual == expected["js"], "expected {} but got {}".format(expected["js"], retriev_files_js_actual)
#     assert retriev_files_ipynb_actual == expected["ipynb"], "expected {} but got {}".format(expected["ipynb"], retriev_files_ipynb_actual)

#     os.chdir(cwd)
#     shutil.rmtree(repo_dir)


# def test_convert_nb_to_py():
#     converted_nbs_expected =  {"success":["./try.ipynb"], "fail":[]}
#     py_files_expected = [("./try.py", "./changed_try.py")]
#     cwd,repo_dir = get_into_repo()
    
#     nb_paths_list = [tup[0] for tup in retriev_files(path=("."), file_ext=[".ipynb"])]
#     converted_nbs = convert_nb_to_py(nb_paths_list)

#     retriev_files_py_actual = retriev_files(path=".", file_ext=["py"])

#     assert nb_paths_list == converted_nbs_expected["success"], "expected {} but got {}".format(converted_nbs_expected["success"], nb_paths_list)
#     assert converted_nbs == converted_nbs_expected,  "expected {} but got {}".format(converted_nbs_expected, converted_nbs)
#     assert retriev_files_py_actual == py_files_expected,  "expected {} but got {}".format(py_files_expected, retriev_files_py_actual)

#     os.chdir(cwd)
#     shutil.rmtree(repo_dir)


# def test_retrieve_init_last_commit_sha():
#     commit_sha_expected = [("ae0a736580407aa1faea93af72d8d4ddc75ead19", "ae0a736580407aa1faea93af72d8d4ddc75ead19"), ("155b2412b013d196a34ec9da61f63cc2ed1a93d9", "11dbc4adeae8811243eb6f4b24731860ba26e929")]
#     cwd,repo_dir = get_into_repo()
    
#     files = retriev_files(file_ext=file_ext, path=".")
#     commit_sha = [retrieve_init_last_commit_sha(run_cmd_process(cmd_list=["git", "log", "--follow", tup[0]])[0])
#                       for tup in files]
    
#     assert commit_sha == commit_sha_expected, "expected {} but got {}".format(commit_sha_expected, commit_sha)

#     os.chdir(cwd)
#     shutil.rmtree(repo_dir)


# def test_get_additions_and_save_contents():
#     additions_expected = {"./server.js": 0, "./try.ipynb": 73}
#     cwd,repo_dir = get_into_repo()
    
#     files = retriev_files(file_ext=file_ext, path=".")
#     commit_sha = [retrieve_init_last_commit_sha(run_cmd_process(cmd_list=["git", "log", "--follow", tup[0]])[0])
#                       for tup in files]

#     additions_dict = get_additions_and_save_contents(files, commit_sha)

#     assert additions_dict == additions_expected, "expected {} but got {}".format(additions_expected, additions_dict)
    
#     os.chdir(cwd)
#     shutil.rmtree(repo_dir)




# class Test_Retrieve_Commit_History(object):
    
#     def test_retrieve_commit_history_no_branch_dict(self):
#         branch_dict = None
#         github_dict = {"owner": user, "repo": repo_name, "token": github_token}

#         expected_dict = {"log": "**11dbc4adeae8811243eb6f4b24731860ba26e929##1660327510##M. D. Ahwireng##Adds codes in notebook\n:100644 100644 e69de29 286f33c M\ttry.ipynb\n try.ipynb | 73 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n 1 file changed, 73 insertions(+)\n\n**6e95ed2c094f9c4896b23f9b1ccaa23c4747ccdf##1660327072##M. D. Ahwireng##Renames test .pynb file\n:100644 100644 e69de29 e69de29 R100\ttry.ipnyb\ttry.ipynb\n try.ipnyb => try.ipynb | 0\n 1 file changed, 0 insertions(+), 0 deletions(-)\n\n**155b2412b013d196a34ec9da61f63cc2ed1a93d9##1660326411##M. D. Ahwireng##Adds .ipynb file for testing\n:000000 100644 0000000 e69de29 A\ttry.ipnyb\n try.ipnyb | 0\n 1 file changed, 0 insertions(+), 0 deletions(-)\n\n**4760d51589be7f133980e97b14bbcd78898bb19b##1647421827##M. D. Ahwireng##Adds changes to package.jsons\n:100644 100644 e2e19f2 43c7654 M\tpackage-lock.json\n:100644 100644 3c1cb7d 771e219 M\tpackage.json\n package-lock.json | 1256 +++++++++++++++++++++++++++++++++++++++++++++++++++++\n package.json      |    8 +-\n 2 files changed, 1262 insertions(+), 2 deletions(-)\n\n**ae0a736580407aa1faea93af72d8d4ddc75ead19##1647421786##M. D. Ahwireng##Adds template for server.js\n:000000 100644 0000000 7b78207 A\tserver.js\n server.js | 18 ++++++++++++++++++\n 1 file changed, 18 insertions(+)\n\n**7824d9848e63cc5b86e8022c94a08f68410c6833##1647419759##M. D. Ahwireng##Adds package-lock.json\n:000000 100644 0000000 e2e19f2 A\tpackage-lock.json\n package-lock.json | 21 +++++++++++++++++++++\n 1 file changed, 21 insertions(+)\n\n**bdf3deeb7628e635963e0c827d34c9501a8c3438##1647419720##M. D. Ahwireng##Adds package.json\n:000000 100644 0000000 3c1cb7d A\tpackage.json\n package.json | 22 ++++++++++++++++++++++\n 1 file changed, 22 insertions(+)\n\n**c0b30f8f0140c35305d7121ca91cabfb34ab07ce##1647419610##M. D. Ahwireng##Adds gitignore\n:000000 100644 0000000 40b878d A\t.gitignore\n .gitignore | 1 +\n 1 file changed, 1 insertion(+)\n\n**1e9c00a7749b14853ef62169eb005cf6845c7ed7##1647417689##M. D. Ahwireng##Initial commit\n:000000 100644 0000000 dad40d2 A\tREADME.md\n README.md | 2 ++\n 1 file changed, 2 insertions(+)\n", "n_commit": 9}

#         commit_history_dict_expected = {
#             "commit_history": [
#                 {
#                     "commit_sha": "11dbc4adeae8811243eb6f4b24731860ba26e929",
#                     "commit_ts": "1660327510",
#                     "author": "M. D. Ahwireng",
#                     "author_git_user": "mdahwireng",
#                     "message": "Adds codes in notebook",
#                     "files": [
#                         {
#                             "file": "try.ipynb",
#                             "details": [
#                                 {
#                                     "name": "change_status",
#                                     "value": "Modified"
#                                 },
#                                 {
#                                     "name": "file_type",
#                                     "value": "non-binary"
#                                 },
#                                 {
#                                     "name": "additions",
#                                     "value": 73
#                                 },
#                                 {
#                                     "name": "deletions",
#                                     "value": 0
#                                 }
#                             ]
#                         }
#                     ],
#                     "num_files": 1
#                 },
#                 {
#                     "commit_sha": "6e95ed2c094f9c4896b23f9b1ccaa23c4747ccdf",
#                     "commit_ts": "1660327072",
#                     "author": "M. D. Ahwireng",
#                     "author_git_user": "mdahwireng",
#                     "message": "Renames test .pynb file",
#                     "files": [
#                         {
#                             "file": "try.ipnyb",
#                             "details": [
#                                 {
#                                     "name": "change_status",
#                                     "value": "Renamed"
#                                 },
#                                 {
#                                     "name": "renamed_to",
#                                     "value": "try.ipynb"
#                                 },
#                                 {
#                                     "name": "similarity_index",
#                                     "value": "100"
#                                 },
#                                 {
#                                     "name": "file_type",
#                                     "value": "non-binary"
#                                 },
#                                 {
#                                     "name": "additions",
#                                     "value": 0
#                                 },
#                                 {
#                                     "name": "deletions",
#                                     "value": 0
#                                 }
#                             ]
#                         }
#                     ],
#                     "num_files": 1
#                 },
#                 {
#                     "commit_sha": "155b2412b013d196a34ec9da61f63cc2ed1a93d9",
#                     "commit_ts": "1660326411",
#                     "author": "M. D. Ahwireng",
#                     "author_git_user": "mdahwireng",
#                     "message": "Adds .ipynb file for testing",
#                     "files": [
#                         {
#                             "file": "try.ipnyb",
#                             "details": [
#                                 {
#                                     "name": "change_status",
#                                     "value": "Created"
#                                 },
#                                 {
#                                     "name": "file_type",
#                                     "value": "non-binary"
#                                 },
#                                 {
#                                     "name": "additions",
#                                     "value": 0
#                                 },
#                                 {
#                                     "name": "deletions",
#                                     "value": 0
#                                 }
#                             ]
#                         }
#                     ],
#                     "num_files": 1
#                 }
#             ],
#             "contribution_counts": [
#                 {
#                     "author_git_user": "mdahwireng",
#                     "author": [
#                         "M. D. Ahwireng"
#                     ],
#                     "total_commits": 9,
#                     "total_additions": 1397,
#                     "total_deletions": 4
#                 }
#             ],
#             "commits_on_branch": 9,
#             "commits_on_default_to_branch": 9,
#             "num_contributors": 1,
#             "branch": "main",
#             "default_branch": "main",
#             "repo_name": "js_code_metrics_api",
#             "html_link": "https://github.com/mdahwireng/js_code_metrics_api/tree/main"
#         }
#         cwd,repo_dir = get_into_repo()

#         ret_commit = Retrieve_Commit_History(github_dict=github_dict, branch_dict=branch_dict)
#         n_commit = ret_commit.n_commit_default_to_branch
#         log = ret_commit.log

#         assert n_commit ==  expected_dict["n_commit"], "expected {} but got {}".format(expected_dict["n_commit"], n_commit)
#         assert log == expected_dict["log"], "expected {} but got {}".format(expected_dict["log"], log)
        
#         commit_history_dict = ret_commit.get_commit_history_and_contributors()
#         commit_history_dict["commit_history"] = commit_history_dict["commit_history"][:3]

#         assert commit_history_dict == commit_history_dict_expected, "expected {} but got {}".format(commit_history_dict_expected, commit_history_dict) 
        
#         os.chdir(cwd)
#         shutil.rmtree(repo_dir)

    
#     def test_get_commit_history_and_contributors_with_branch(self):
#         branch_dict = {"default": default_branch, "branch": branch_name}
#         github_dict = {"owner": user, "repo": repo_name, "token": github_token}

#         expected_dict = {
#                     "n_commit": 7,
#                     "log": "**5889763543830369b07db4c6d2fba286e23bb95d##1660323170##M. D. Ahwireng##Adds test python file\n:000000 100644 0000000 b645cf0 A\tother.py\n other.py | 1 +\n 1 file changed, 1 insertion(+)\n",
#                 }

#         commit_history_dict_expected = {
#                 "commit_history": [
#                     {
#                         "commit_sha": "5889763543830369b07db4c6d2fba286e23bb95d",
#                         "commit_ts": "1660323170",
#                         "author": "M. D. Ahwireng",
#                         "author_git_user": "mdahwireng",
#                         "message": "Adds test python file",
#                         "files": [
#                             {
#                                 "file": "other.py",
#                                 "details": [
#                                     {
#                                         "name": "change_status",
#                                         "value": "Created"
#                                     },
#                                     {
#                                         "name": "file_type",
#                                         "value": "non-binary"
#                                     },
#                                     {
#                                         "name": "additions",
#                                         "value": 1
#                                     },
#                                     {
#                                         "name": "deletions",
#                                         "value": 0
#                                     }
#                                 ]
#                             }
#                         ],
#                         "num_files": 1
#                     }
#                 ],
#                 "contribution_counts": [
#                     {
#                         "author_git_user": "mdahwireng",
#                         "author": [
#                             "M. D. Ahwireng"
#                         ],
#                         "total_commits": 1,
#                         "total_additions": 1,
#                         "total_deletions": 0
#                     }
#                 ],
#                 "commits_on_branch": 1,
#                 "commits_on_default_to_branch": 7,
#                 "num_contributors": 1,
#                 "branch": "other",
#                 "default_branch": "main",
#                 "repo_name": "js_code_metrics_api",
#                 "html_link": "https://github.com/mdahwireng/js_code_metrics_api/tree/other"
#             }

#         cwd,repo_dir = get_into_repo()

#         ret_commit = Retrieve_Commit_History(github_dict=github_dict, branch_dict=branch_dict)
#         n_commit = ret_commit.n_commit_default_to_branch
#         log = ret_commit.log

#         assert n_commit ==  expected_dict["n_commit"], "expected {} but got {}".format(expected_dict["n_commit"], n_commit)
#         assert log == expected_dict["log"], "expected {} but got {}".format(expected_dict["log"], log)


#         commit_history_dict = ret_commit.get_commit_history_and_contributors()
#         commit_history_dict["commit_history"] = commit_history_dict["commit_history"]

#         assert commit_history_dict == commit_history_dict_expected, "expected {} but got {}".format(commit_history_dict_expected, commit_history_dict)

#         os.chdir(cwd)
#         shutil.rmtree(repo_dir)

#     def test_get_commit_history_and_contributors_with_not_found_specified_branch(self):
#         branch_dict = {"default": default_branch, "branch": "wrong"}
#         github_dict = {"owner": user, "repo": repo_name, "token": github_token}
#         commit_history_dict_expected = {"error": "Specified branch: {} \nDoes not exist".format(branch_dict["branch"])}

#         cwd,repo_dir = get_into_repo()

#         ret_commit = Retrieve_Commit_History(github_dict=github_dict, branch_dict=branch_dict)
#         commit_history_dict = ret_commit.get_commit_history_and_contributors()

#         assert commit_history_dict == commit_history_dict_expected, "expected {} but got {}".format(commit_history_dict_expected, commit_history_dict)

#         os.chdir(cwd)
#         shutil.rmtree(repo_dir)


#     def test_get_commit_history_and_contributors_with_not_found_default_branch(self):
#         branch_dict = {"default": "wrong", "branch": branch_name}
#         github_dict = {"owner": user, "repo": repo_name, "token": github_token}
#         commit_history_dict_expected = {"error": "Default branch: {} \nDoes not exist".format(branch_dict["default"])}

#         cwd,repo_dir = get_into_repo()

#         ret_commit = Retrieve_Commit_History(github_dict=github_dict, branch_dict=branch_dict)
#         commit_history_dict = ret_commit.get_commit_history_and_contributors()

#         assert commit_history_dict == commit_history_dict_expected, "expected {} but got {}".format(commit_history_dict_expected, commit_history_dict)

#         os.chdir(cwd)
#         shutil.rmtree(repo_dir)

    
#     def test_get_commit_history_and_contributors_with_not_found_branches(self):
#         branch_dict = {"default": "wrong", "branch": "another_wrong"}
#         github_dict = {"owner": user, "repo": repo_name, "token": github_token}
#         commit_history_dict_expected = {"error": "Default branch: {}\nSpecified branch: {} \nBoth do not exist".format(branch_dict["default"], branch_dict["branch"])}

#         cwd,repo_dir = get_into_repo()

#         ret_commit = Retrieve_Commit_History(github_dict=github_dict, branch_dict=branch_dict)
#         commit_history_dict = ret_commit.get_commit_history_and_contributors()

#         assert commit_history_dict == commit_history_dict_expected, "expected {} but got {}".format(commit_history_dict_expected, commit_history_dict)

#         os.chdir(cwd)
#         shutil.rmtree(repo_dir)




class Test_run_to_get_adds_and_save_content(object):
    
    global repo_dict
    repo_dict = {"clone_url": clone_url}

    
    def test_run_to_get_adds_and_save_content_no_branch(self):
        expected = (
                    "Cloning into 'tmp/js_code_metrics_api'...\n",
                    0,
                    {
                        "./server.js": 0,
                        "./try.ipynb": 73,
                        "./try.py": 0
                    },
                    [
                        (
                            "./server.js",
                            "./changed_server.js"
                        ),
                        (
                            "./try.ipynb",
                            "./changed_try.ipynb"
                        ),
                        (
                            "./try.py",
                            "./changed_try.py"
                        )
                    ],
                    {
                        "interested_files": [
                            {
                                "name": ".gitignore",
                                "present": True
                            },
                            {
                                "name": "readme.md",
                                "present": True
                            },
                            {
                                "name": "requirements.txt",
                                "present": False
                            },
                            {
                                "name": "dockerfile",
                                "present": False
                            },
                            {
                                "name": ".dvcignore",
                                "present": False
                            },
                            {
                                "name": ".github",
                                "present": False
                            },
                            {
                                "name": ".dvc",
                                "present": False
                            }
                        ],
                        "num_dirs": 0,
                        "num_files": 6,
                        "num_py": 0,
                        "num_js": 1,
                        "num_ipynb": 1
                    },
                    {
                        "commit_history": [
                            {
                                "commit_sha": "11dbc4adeae8811243eb6f4b24731860ba26e929",
                                "commit_ts": "1660327510",
                                "author": "M. D. Ahwireng",
                                "author_git_user": "mdahwireng",
                                "message": "Adds codes in notebook",
                                "files": [
                                    {
                                        "file": "try.ipynb",
                                        "details": [
                                            {
                                                "name": "change_status",
                                                "value": "Modified"
                                            },
                                            {
                                                "name": "file_type",
                                                "value": "non-binary"
                                            },
                                            {
                                                "name": "additions",
                                                "value": 73
                                            },
                                            {
                                                "name": "deletions",
                                                "value": 0
                                            }
                                        ]
                                    }
                                ],
                                "num_files": 1
                            },
                            {
                                "commit_sha": "6e95ed2c094f9c4896b23f9b1ccaa23c4747ccdf",
                                "commit_ts": "1660327072",
                                "author": "M. D. Ahwireng",
                                "author_git_user": "mdahwireng",
                                "message": "Renames test .pynb file",
                                "files": [
                                    {
                                        "file": "try.ipnyb",
                                        "details": [
                                            {
                                                "name": "change_status",
                                                "value": "Renamed"
                                            },
                                            {
                                                "name": "renamed_to",
                                                "value": "try.ipynb"
                                            },
                                            {
                                                "name": "similarity_index",
                                                "value": "100"
                                            },
                                            {
                                                "name": "file_type",
                                                "value": "non-binary"
                                            },
                                            {
                                                "name": "additions",
                                                "value": 0
                                            },
                                            {
                                                "name": "deletions",
                                                "value": 0
                                            }
                                        ]
                                    }
                                ],
                                "num_files": 1
                            },
                            {
                                "commit_sha": "155b2412b013d196a34ec9da61f63cc2ed1a93d9",
                                "commit_ts": "1660326411",
                                "author": "M. D. Ahwireng",
                                "author_git_user": "mdahwireng",
                                "message": "Adds .ipynb file for testing",
                                "files": [
                                    {
                                        "file": "try.ipnyb",
                                        "details": [
                                            {
                                                "name": "change_status",
                                                "value": "Created"
                                            },
                                            {
                                                "name": "file_type",
                                                "value": "non-binary"
                                            },
                                            {
                                                "name": "additions",
                                                "value": 0
                                            },
                                            {
                                                "name": "deletions",
                                                "value": 0
                                            }
                                        ]
                                    }
                                ],
                                "num_files": 1
                            },
                            {
                                "commit_sha": "4760d51589be7f133980e97b14bbcd78898bb19b",
                                "commit_ts": "1647421827",
                                "author": "M. D. Ahwireng",
                                "author_git_user": "mdahwireng",
                                "message": "Adds changes to package.jsons",
                                "files": [
                                    {
                                        "file": "package-lock.json",
                                        "details": [
                                            {
                                                "name": "change_status",
                                                "value": "Modified"
                                            },
                                            {
                                                "name": "file_type",
                                                "value": "non-binary"
                                            },
                                            {
                                                "name": "additions",
                                                "value": 1256
                                            },
                                            {
                                                "name": "deletions",
                                                "value": 0
                                            }
                                        ]
                                    },
                                    {
                                        "file": "package.json",
                                        "details": [
                                            {
                                                "name": "change_status",
                                                "value": "Modified"
                                            },
                                            {
                                                "name": "file_type",
                                                "value": "non-binary"
                                            },
                                            {
                                                "name": "additions",
                                                "value": 4
                                            },
                                            {
                                                "name": "deletions",
                                                "value": 4
                                            }
                                        ]
                                    }
                                ],
                                "num_files": 2
                            },
                            {
                                "commit_sha": "ae0a736580407aa1faea93af72d8d4ddc75ead19",
                                "commit_ts": "1647421786",
                                "author": "M. D. Ahwireng",
                                "author_git_user": "mdahwireng",
                                "message": "Adds template for server.js",
                                "files": [
                                    {
                                        "file": "server.js",
                                        "details": [
                                            {
                                                "name": "change_status",
                                                "value": "Created"
                                            },
                                            {
                                                "name": "file_type",
                                                "value": "non-binary"
                                            },
                                            {
                                                "name": "additions",
                                                "value": 18
                                            },
                                            {
                                                "name": "deletions",
                                                "value": 0
                                            }
                                        ]
                                    }
                                ],
                                "num_files": 1
                            },
                            {
                                "commit_sha": "7824d9848e63cc5b86e8022c94a08f68410c6833",
                                "commit_ts": "1647419759",
                                "author": "M. D. Ahwireng",
                                "author_git_user": "mdahwireng",
                                "message": "Adds package-lock.json",
                                "files": [
                                    {
                                        "file": "package-lock.json",
                                        "details": [
                                            {
                                                "name": "change_status",
                                                "value": "Created"
                                            },
                                            {
                                                "name": "file_type",
                                                "value": "non-binary"
                                            },
                                            {
                                                "name": "additions",
                                                "value": 21
                                            },
                                            {
                                                "name": "deletions",
                                                "value": 0
                                            }
                                        ]
                                    }
                                ],
                                "num_files": 1
                            },
                            {
                                "commit_sha": "bdf3deeb7628e635963e0c827d34c9501a8c3438",
                                "commit_ts": "1647419720",
                                "author": "M. D. Ahwireng",
                                "author_git_user": "mdahwireng",
                                "message": "Adds package.json",
                                "files": [
                                    {
                                        "file": "package.json",
                                        "details": [
                                            {
                                                "name": "change_status",
                                                "value": "Created"
                                            },
                                            {
                                                "name": "file_type",
                                                "value": "non-binary"
                                            },
                                            {
                                                "name": "additions",
                                                "value": 22
                                            },
                                            {
                                                "name": "deletions",
                                                "value": 0
                                            }
                                        ]
                                    }
                                ],
                                "num_files": 1
                            },
                            {
                                "commit_sha": "c0b30f8f0140c35305d7121ca91cabfb34ab07ce",
                                "commit_ts": "1647419610",
                                "author": "M. D. Ahwireng",
                                "author_git_user": "mdahwireng",
                                "message": "Adds gitignore",
                                "files": [
                                    {
                                        "file": ".gitignore",
                                        "details": [
                                            {
                                                "name": "change_status",
                                                "value": "Created"
                                            },
                                            {
                                                "name": "file_type",
                                                "value": "non-binary"
                                            },
                                            {
                                                "name": "additions",
                                                "value": 1
                                            },
                                            {
                                                "name": "deletions",
                                                "value": 0
                                            }
                                        ]
                                    }
                                ],
                                "num_files": 1
                            },
                            {
                                "commit_sha": "1e9c00a7749b14853ef62169eb005cf6845c7ed7",
                                "commit_ts": "1647417689",
                                "author": "M. D. Ahwireng",
                                "author_git_user": "mdahwireng",
                                "message": "Initial commit",
                                "files": [
                                    {
                                        "file": "README.md",
                                        "details": [
                                            {
                                                "name": "change_status",
                                                "value": "Created"
                                            },
                                            {
                                                "name": "file_type",
                                                "value": "non-binary"
                                            },
                                            {
                                                "name": "additions",
                                                "value": 2
                                            },
                                            {
                                                "name": "deletions",
                                                "value": 0
                                            }
                                        ]
                                    }
                                ],
                                "num_files": 1
                            }
                        ],
                        "contribution_counts": [
                            {
                                "author_git_user": "mdahwireng",
                                "author": [
                                    "M. D. Ahwireng"
                                ],
                                "total_commits": 9,
                                "total_additions": 1397,
                                "total_deletions": 4
                            }
                        ],
                        "commits_on_branch": 9,
                        "commits_on_default_to_branch": 9,
                        "num_contributors": 1,
                        "branch": "main",
                        "default_branch": "main",
                        "repo_name": "js_code_metrics_api",
                        "html_link": "https://github.com/mdahwireng/js_code_metrics_api/tree/main"
                    },
                    [
                        "./try.ipynb"
                    ]
                )   
        cwd_start = os.getcwd()
        output = run_to_get_adds_and_save_content(user, repo_name, repo_dict, file_ext, github_token,  branch=None, path='.')

        assert output == expected, "Expected output to be {} but got {}".format(expected, output)

        cwd_end = os.getcwd()

        os.chdir(cwd_start)
        shutil.rmtree(cwd_end)


    def test_run_to_get_adds_and_save_content_branch_specified(self):
        expected = (
                "Switched to a new branch 'other'\n",
                0,
                {
                    "./server.js": 0,
                    "./other.py": 0
                },
                [
                    
                    (    "./server.js",
                        "./changed_server.js"
                    ),
                   ( 
                        "./other.py",
                        "./changed_other.py"
                    )
                ],
                {
                    "interested_files": [
                        {
                            "name": ".gitignore",
                            "present": True
                        },
                        {
                            "name": "readme.md",
                            "present": True
                        },
                        {
                            "name": "requirements.txt",
                            "present": False
                        },
                        {
                            "name": "dockerfile",
                            "present": False
                        },
                        {
                            "name": ".dvcignore",
                            "present": False
                        },
                        {
                            "name": ".github",
                            "present": False
                        },
                        {
                            "name": ".dvc",
                            "present": False
                        }
                    ],
                    "num_dirs": 0,
                    "num_files": 6,
                    "num_py": 1,
                    "num_js": 1,
                    "num_ipynb": 0
                },
                {
                    "commit_history": [
                        {
                            "commit_sha": "5889763543830369b07db4c6d2fba286e23bb95d",
                            "commit_ts": "1660323170",
                            "author": "M. D. Ahwireng",
                            "author_git_user": "mdahwireng",
                            "message": "Adds test python file",
                            "files": [
                                {
                                    "file": "other.py",
                                    "details": [
                                        {
                                            "name": "change_status",
                                            "value": "Created"
                                        },
                                        {
                                            "name": "file_type",
                                            "value": "non-binary"
                                        },
                                        {
                                            "name": "additions",
                                            "value": 1
                                        },
                                        {
                                            "name": "deletions",
                                            "value": 0
                                        }
                                    ]
                                }
                            ],
                            "num_files": 1
                        }
                    ],
                    "contribution_counts": [
                        {
                            "author_git_user": "mdahwireng",
                            "author": [
                                "M. D. Ahwireng"
                            ],
                            "total_commits": 1,
                            "total_additions": 1,
                            "total_deletions": 0
                        }
                    ],
                    "commits_on_branch": 1,
                    "commits_on_default_to_branch": 7,
                    "num_contributors": 1,
                    "branch": "other",
                    "default_branch": "main",
                    "repo_name": "js_code_metrics_api",
                    "html_link": "https://github.com/mdahwireng/js_code_metrics_api/tree/other"
                },
                []
            )                
        cwd_start = os.getcwd()
        output = run_to_get_adds_and_save_content(user, repo_name, repo_dict, file_ext, github_token,  branch=branch_name, path='.')

        assert output == expected, "Expected output to be {} but got {}".format(expected, output)

        cwd_end = os.getcwd()

        os.chdir(cwd_start)
        shutil.rmtree(cwd_end)
