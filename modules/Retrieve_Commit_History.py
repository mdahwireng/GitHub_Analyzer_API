from modules.api_utils import run_cmd_process

class Retrieve_Commit_History:
    """
        Retrieve commit history for a given branch
        
        Methods:
            treat_details(): Treats the details of the commit history
            treat_raw(): Treats the raw data of the commit history
            treat_stat(): Treats the stats of the commit history
            get_commit_history(): Returns a list of commit history
        """
            
    def __init__(self, branch_dict=None) -> None:
        """
        Initialize the class.
        Returns None.

        Args:
            branch_dict (dict): The branch dictionary containing the default branch and the branch to be analyzed. Default is None
        """

        self.branch_dict = branch_dict       
        if branch_dict:
            self.default_branch = self.branch_dict['default']
            self.branch = self.branch_dict['branch']
            if self.branch == self.default_branch:
                self.log = run_cmd_process(cmd_list=["git", "log", '--pretty=format:**%H##%ct##%aN##%s', "--raw", "--stat"])[0]
            else:
                self.log = run_cmd_process(cmd_list=["git", "log", "{}..{}".format(self.default_branch, self.branch), '--pretty=format:**%H##%ct##%aN##%s', "--raw", "--stat"])[0]
        
        else:
            self.log = run_cmd_process(cmd_list=["git", "log", '--pretty=format:**%H##%ct##%aN##%s', "--raw", "--stat"])[0]
        self.lines = self.log.split("**")


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

    def get_commit_history(self) -> list:
        """
        Returns a list of commit history
        Returns:
            A list of commit history
        """

        commit_history = []
        commit_history = []
        for line in self.lines[1:]:
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

                commit_sha, commit_ts, author, message = self.treat_details(details)
                raw_dict = self.treat_raw(raw)
                stats_dict = self.treat_stat(stats)

                for f,s in stats_dict.items():
                    if f in raw_dict.keys():
                        raw_dict[f].update(s)

                commit_dict = {"commit_sha":commit_sha,"commit_ts":commit_ts, "author":author, "message":message, "files":raw_dict}
                commit_history.append(commit_dict)
        return commit_history