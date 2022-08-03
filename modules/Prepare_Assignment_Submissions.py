import pandas as pd


class PrepareAssignmentDf:
    """
    Prepares DataFrame created from assignment submissions for analysis
    
    methods:
        __init__: Initializes the class with the dataframe, the run number and the link column
        clean_link: Cleans a given link string and returns the cleaned link
        get_username: Retrives the username from a given link.
        get_repo_name: Retrives the repo name from a given link.
        get_branch_name: Retrives the branch name from a given link.
        get_df: Adds repo name, username, branch name, and run_number columns to the dataframe
                If a filename is given, the enhanced dataframe is saved to a csv file with the filename
    """
    def __init__(self, df, run_number, link_col) -> None:
        """
        Initialize the class with the dataframe, the run number and the link column

        Args:
            df (DataFrame): Dataframe to be prepared
            run_number (str): Run number of the analysis
            link_col (str): Link column of the dataframe

        Returns:
            None

        """
        self.df = df
        self.run_number = run_number
        self.link_col = link_col
        

    def clean_link(self, link) -> str:
        """
        Cleans a given link string and returns the cleaned link
        
        Args:
            link (str): Link to be cleaned

        Returns:
            str: Cleaned link
        """
        # remove trailing foward slash and .git
        if not isinstance(link, float) and len(link) > 0:
            if link.endswith(".git"):
                link = link[:-4]
            if "/commit/" in link:
                link = link.split("/commit/")[0]
            if link.endswith("/"):
                link = link[:-1]
            if link.__contains__("/blob/"):
                parts = link.split("/blob/")
                link = parts[0] + "/tree/" + parts[1]
            if link.__contains__("/tree/"):
                parts = link.split("/tree/")
                link = parts[0] + "/tree/" + parts[1].split("/")[0]

        return link

    
    def get_username(self, link) -> str or None:
        """
        Retrives the username from a given link.
        If the link is not a valid link, returns None

        Args:
            link (str): Link to be cleaned

        Returns:
            str: Username
        """
        if not isinstance(link, float) and len(link) > 0:
            if link.__contains__("/tree/"):
                return link.split("/")[3]
            return link.split("/")[-2]
        else:
            return None

        
    def get_repo_name(self,link) -> str or None:
        """
        Retrives the repo name from a given link.
        If the link is not a valid link, returns None
        
        Args:
            link (str): Link to be cleaned
            
        Returns:
            str: Repo name
        """
        if not isinstance(link, float) and len(link) > 0:
            if link.__contains__("/tree/"):
                return link.split("/")[4]
            return link.split("/")[-1]
        else:
            return None


    def get_branch_name(self, link)-> str or None:
        """
        Retrives the branch name from a given link.
        If the link is not a valid link, returns None

        Args:
            link (str): Link to be cleaned

        Returns:
            str: Branch name
        """
        if not isinstance(link, float) and len(link) > 0:
            if link.__contains__("/tree/"):
                return link.split("/")[-1]
            else:
                return None
        else:
            return None


    def get_df(self,filename=None) -> pd.DataFrame:
        """
        Adds repo name, username, branch name, and run_number columns to the dataframe
        If a filename is given, the enhanced dataframe is saved to a csv file with the filename
        Returns the enhanced dataframe

        Args:
            filename (str): Filename of the csv file to be saved, default None

        Returns:
            pd.DataFrame: Enhanced dataframe
        """
        
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