import pandas as pd


class PrepareGithubDf:
    def __init__(self, df, week):
        # read csv
        self.df = df
        self.week = week
        
        # rename userid column to trainee_id
        self.df.rename(columns={"userId":"trainee_id"}, inplace=True)
        
        
    def slice_week(self):
        slice_col = ["trainee_id"]
        slice_col.append(self.week)
        self.df = self.df[slice_col]
        
        # Drop null values
        self.df.dropna(inplace=True)
    
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
        self.slice_week()
        
        gh_usernames = []
        gh_repo_names = []
        gh_branch_names = []

        for index, row in self.df.iterrows():
            gh_usernames.append(self.get_username(row[self.week]))
            gh_repo_names.append(self.get_repo_name(row[self.week]))
            gh_branch_names.append(self.get_branch_name(row[self.week]))
        
        self.df["gh_username"] = gh_usernames
        self.df["repo_name"] = gh_repo_names
        self.df["branch_name"] = gh_branch_names

        self.df = self.df[self.df["gh_username"].notnull()]
        self.df = self.df[["trainee_id", "gh_username", "repo_name", "branch_name"]]
        if filename:
            self.df.to_csv(filename, index=False)
        return self.df