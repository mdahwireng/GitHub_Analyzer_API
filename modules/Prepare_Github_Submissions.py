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
    
    def create_username_col(self):
        self.df["gh_username"] = self.df[self.week].apply(lambda x:x.split("/")[-2] if not isinstance(x, float) and len(x) > 0 else None)
        
    def create_repo_name_col(self):
        self.df["repo_name"] = self.df[self.week].apply(lambda x:x.split("/")[-1] if not isinstance(x, float) and len(x) > 0 else None)
    
    def get_df(self,filename=None):
        self.slice_week()
        self.create_username_col()
        self.create_repo_name_col()
        self.df = self.df[self.df["gh_username"].notnull()]
        self.df = self.df[["trainee_id", "gh_username", "repo_name"]]
        if filename:
            self.df.to_csv(filename, index=False)
        return self.df