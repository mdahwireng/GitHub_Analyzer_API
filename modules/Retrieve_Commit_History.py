from collections import Counter
import subprocess
import requests


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




    


class Retrieve_Commit_History:
    """
        Retrieve commit history for a given branch
        
        Methods:
            treat_details(): Treats the details of the commit history
            treat_raw(): Treats the raw data of the commit history
            treat_stat(): Treats the stats of the commit history
            get_commit_history_and_contributors(): A dictionary containing the commit history, contributors, number of commits and number of contributors
        """
            
    def __init__(self, branch_dict=None, github_dict=None) -> None:
        """
        Initialize the class.
        Returns None.

        Args:
            branch_dict (dict): The branch dictionary containing the default branch and the branch to be analyzed. Default is None
            github_dict (dict): The github details dictionary containing the username and the repository name. Default is None
        """

        self.branch_dict = branch_dict
        self.n_commit_default_to_branch = None
        self.merged = False 
        self.html_link = None      
        if branch_dict:
            self.default_branch = self.branch_dict['default']
            self.branch = self.branch_dict['branch']
            if self.branch == self.default_branch:
                self.log = run_cmd_process(cmd_list=["git", "log", '--pretty=format:**%H##%ct##%aN##%s', "--raw", "--stat"])[0]
                self.n_commit_default_to_branch = len(self.log.split("**"))-1
            else:
                log = run_cmd_process(cmd_list=["git", "log", "{}..{}".format(self.default_branch, self.branch), '--pretty=format:**%H##%ct##%aN##%s', "--raw", "--stat"])[0]
                if log == "":
                    self.merged = True
                    print("\nNo unique commits found for the branch {}. The branch may have been merged with {} (default branch)\n".format(self.branch, self.default_branch))
                    self.log = run_cmd_process(cmd_list=["git", "log", '--pretty=format:**%H##%ct##%aN##%s', "--raw", "--stat"])[0]
                    self.n_commit_default_to_branch = len(self.log.split("**"))-1
                else:
                    self.log = log
        
        else:
            self.log = run_cmd_process(cmd_list=["git", "log", '--pretty=format:**%H##%ct##%aN##%s', "--raw", "--stat"])[0]
            self.n_commit_default_to_branch = len(self.log.split("**"))-1

        self.lines = self.log.split("**")
        self.headers = None

        if not self.n_commit_default_to_branch:
            log = run_cmd_process(cmd_list=["git", "log", '--pretty=format:**%H##%ct##%aN##%s', "--raw", "--stat"])[0]
            self.n_commit_default_to_branch = len(log.split("**"))-1
            

        if github_dict:
            self.owner = github_dict['owner']
            self.repo = github_dict['repo']

            if self.branch:
                self.html_link = "https://github.com/{}/{}/tree/{}".format(self.owner, self.repo, self.branch)

            if "token" in github_dict:
                self.headers = {"Authorization":"Bearer {}".format(github_dict['token'])}



    def treat_details(self, d_list) -> tuple:
        """
        Treats the details of the commit history
        Returns the commit sha, commit timestamp, author and message
        
        Args:
            d_list (list): The list of details

        Returns:
            A tuple containing the commit sha, commit timestamp, author and message
        """
        details = d_list[0].split("##")
        d_ = details[0],details[1],details[2],details[3]
        return d_

    
    
    def treat_raw(self, r_list) -> dict:
        """
        Treats the raw data of the commit history
        Returns the files and the type of modification made to them

        Args:
            r_list (list): The list of raw data

        Returns:
            A dictionary containing the files and the type of modification made to them
        """

        change_status_d = {"M":"Modified", "A":"Created", "D":"Deleted", "R100":"Renamed"}
        files__ = {}
        for r in r_list:
            r_ll = r.split("\t")
            change_status = change_status_d[r_ll[0].split(" ")[-1]]
            if change_status == "Renamed":
                file_n = r_ll[-2].strip()
                files__[file_n] = {"change_status": change_status, "renamed_to":r_ll[-1].strip()}
            else:
                file_n = r_ll[-1]
                files__[file_n] = {"change_status": change_status}
        return files__

    def treat_stat(self, s_list) -> dict:
        """
        Treats the stats of the commit history
        Returns the files and the lines added and deleted

        Args:
            s_list (list): The list of stats

        Returns:
            A dictionary containing the files and the lines added and deleted as well as modification details
        """

        files__ = {}
        for s in s_list:
            s_ll = s.split("|")
            file_n = s_ll[0].strip()
            changes = s_ll[-1].split(" ")[-1]
            additions = changes.count("+")
            deletions = changes.count("-")
            files__[file_n] = {"additions":additions, "deletions":deletions}
        return files__

    def get_commit_history_and_contributors(self) -> list:
        """
        Returns a list of commit history
        Returns:
            A dictionary containing the commit history, contributors, number of commits and number of contributors
        """

        if self.owner and self.repo:
            author_git_user_dict = {}

        if self.merged:
            unique_commits = []
            for l in run_cmd_process(cmd_list=["git", "log", self.branch, "--decorate", "--oneline"])[0].split("\n"):
                if "origin" in l and self.branch not in l:
                    break
                if l not in unique_commits:
                    unique_commits.append(l)
            if "Merge" in unique_commits[-1]:
                unique_commits.pop(-1)
            unique_commits = [l.split(" ")[0] for l in unique_commits]
            unique_commits_lines = []

            for commit in unique_commits:
                for line in self.lines:
                    if commit in line:
                        unique_commits_lines.append(line)
                        break
            self.lines = unique_commits_lines
        
        else:
            self.lines = self.lines[1:]
        


        commit_history = []
        for line in self.lines:
            l_split = line.split("\n")
            if len(l_split) > 0:
                details = []
                raw = []
                stats = []
                for l in l_split:
                    if l.__contains__("##"):
                        details.append(l)
                    if l.__contains__(":") and not l.__contains__("##"):
                        raw.append(l)
                    if l.__contains__("|"):
                        stats.append(l)
                if len(details) > 0:
                    commit_sha, commit_ts, author, message = self.treat_details(details)
                    raw_dict = self.treat_raw(raw)
                    stats_dict = self.treat_stat(stats)

                    for f,s in stats_dict.items():
                        if f in raw_dict.keys():
                            raw_dict[f].update(s)

                    raw_dict = [{"file":k, "details":v} for k,v in raw_dict.items()]

                    if self.owner and self.repo:
                        if author not in author_git_user_dict.keys():

                            ref_url = "https://api.github.com/repos/{}/{}/commits/{}".format(self.owner, self.repo, commit_sha)
                            ref_r, ref_sc = send_get_req(ref_url, _header=self.headers)
                            
                            if ref_sc == 200:
                                ref_json = ref_r.json()
                                author_git_user_dict[author] = ref_json["author"]["login"]
                            else:
                                author_git_user_dict[author] = None
                            
                            github_username = author_git_user_dict[author]

                        else:
                            github_username = author_git_user_dict[author]
                    
                    else:
                        github_username = None

                    commit_dict = {"commit_sha":commit_sha,"commit_ts":commit_ts, "author":author, "author_git_user":github_username, "message":message, "files":raw_dict}
                    
                    commit_history.append(commit_dict)

        
            contributor_list = [c["author"] for c in commit_history]
            contribution_count = dict(Counter(contributor_list))

            addition_deletion_dict = {author:{"additions":0, "deletions":0} for author in contribution_count.keys()}
            for c in commit_history:
                for f in c["files"]:
                    if "additions" in f["details"].keys():
                        addition_deletion_dict[c["author"]]["additions"] += f["details"]["additions"]
                    if "deletions" in f["details"].keys():
                        addition_deletion_dict[c["author"]]["deletions"] += f["details"]["deletions"]

            if self.owner and self.repo:
                contribution_count = [ {"author":a, "author_git_user":author_git_user_dict[a], "total_commits":c, "total_additions":addition_deletion_dict[a]["additions"], "total_deletions":addition_deletion_dict[a]["deletions"]} for a,c in contribution_count.items()]
            else:
                contribution_count = [ {"author":a, "total_commits":c, "total_additions":addition_deletion_dict[a]["additions"], "total_deletions":addition_deletion_dict[a]["deletions"]} for a,c in contribution_count.items()]
            
        return {"commit_history": commit_history, "contribution_count": contribution_count, "num_commits_on _branch":len(commit_history), "num_commits_on_default_to_branch":self.n_commit_default_to_branch, "num_contributors":len(contribution_count), "branch":self.branch, "default_branch":self.default_branch, "repo_name":self.repo, "html_link":self.html_link}