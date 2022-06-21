import pandas as pd


class PrepareAssignmentDf:
    def __init__(self, df, run_number, link_col):
        # read csv
        self.df = df
        self.run_number = run_number
        self.link_col = link_col
        

    
    def get_username(self, link):
        if not isinstance(link, float) and len(link) > 0:
            if link.endswith(".git"):
                link = link.replace(".git", "")
            if link.__contains__("/tree/"):
                return link.split("/")[3]
            return link.split("/")[-2]
        else:
            return None

        
    def get_repo_name(self,link):
        if not isinstance(link, float) and len(link) > 0:
            if link.endswith(".git"):
                link = link.replace(".git", "")
            if link.endswith("/"):
                link = link.replace("/", "")
            if link.__contains__("/tree/"):
                return link.split("/")[4]
            return link.split("/")[-1]
        else:
            return None


    def get_branch_name(self, link):
        if not isinstance(link, float) and len(link) > 0:
            if link.__contains__("/tree/"):
                return link.split("/")[-1]
            else:
                return None
        else:
            return None


    def get_df(self,filename=None):
        
        gh_usernames = []
        gh_repo_names = []
        gh_branch_names = []

        for index, row in self.df.iterrows():
            gh_usernames.append(self.get_username(row[self.link_col]))
            gh_repo_names.append(self.get_repo_name(row[self.link_col]))
            gh_branch_names.append(self.get_branch_name(row[self.link_col]))
        
        self.df["gh_username"] = gh_usernames
        self.df["repo_name"] = gh_repo_names
        self.df["branch_name"] = gh_branch_names
        self.df["run_number"] = self.run_number

        """self.df = self.df[self.df["gh_username"].notnull()]
        self.df = self.df[["trainee_id", "gh_username", "repo_name", "branch_name"]]"""
        if filename:
            self.df.to_csv(filename, index=False)
        return self.df