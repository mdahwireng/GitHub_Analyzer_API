import pandas as pd


class PrepareAssignmentDf:
    def __init__(self, df, run_number, link_col):
        # read csv
        self.df = df
        self.run_number = run_number
        self.link_col = link_col
        

    def clean_link(self, link):
        # remove trailing foward slash and .git
        if not isinstance(link, float) and len(link) > 0:
            if link.endswith(".git"):
                link = link[:-4]
            if link.endswith("/"):
                link = link[:-1]
            if link.__contains__("/blob/"):
                parts = link.split("/blob/")
                link = parts[0] + "/tree/" + parts[1]
            if link.__contains__("/tree/"):
                parts = link.split("/tree/")
                link = parts[0] + "/tree/" + parts[1].split("/")[0]

        return link

    
    def get_username(self, link):
        if not isinstance(link, float) and len(link) > 0:
            if link.__contains__("/tree/"):
                return link.split("/")[3]
            return link.split("/")[-2]
        else:
            return None

        
    def get_repo_name(self,link):
        if not isinstance(link, float) and len(link) > 0:
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
            link = self.clean_link(row[self.link_col])
            gh_usernames.append(self.get_username(link))
            gh_repo_names.append(self.get_repo_name(link))
            gh_branch_names.append(self.get_branch_name(link))
        
        self.df["gh_username"] = gh_usernames
        self.df["repo_name"] = gh_repo_names
        self.df["branch_name"] = gh_branch_names
        self.df["run_number"] = self.run_number

        """self.df = self.df[self.df["gh_username"].notnull()]
        self.df = self.df[["trainee_id", "gh_username", "repo_name", "branch_name"]]"""
        if filename:
            self.df.to_csv(filename, index=False)
        return self.df