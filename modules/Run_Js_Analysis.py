from typing import List
import lizard
from radon.complexity import cc_rank


class Run_Js_Analysis:
    """
    Runs analysis on JavaScript codes
    
    methods:
        __init__: Initializes the class with the files to be analyzed and the dictionary of additions
        retrieve_file_comments: Retrieve the number of comments in a file
        retrieve_file_level_analysis: Retrieve the file level analysis
        retrieve_repo_summary: Retrieve the repo summary
        run_analysis: Runs the analysis
    """
    
    def __init__(self, files, additions_dict):
        """
        Initialize the class with the files to be analyzed and the dictionary of additions
        
        Args:
            files (List): List of tupples to files to be analyzed
            additions_dict (Dict): Dictionary of additions per file

        Returns:
            None
        """
        self.files = [tup[0] for tup in files if tup[0].endswith(".js")]
        self.additions_dict = additions_dict
        self.file_analysis = [lizard.analyze_file(f) for f in self.files]
        self.file_level = []
        self.repo_summary = dict()


    def retrieve_file_comments(self,file_path) -> int:
        """
        Retrieve the number of comments in a file
        
        Args:
            file_path (str): Path to the file to be analyzed
        
        Returns:
            int: Number of comments in the file
        """
        code = lizard.auto_read(file_path)
        context = lizard.FileInfoBuilder(file_path)
      
        reader = (lizard.get_reader_for(file_path))(context)
        tokens = reader.generate_tokens(code)
        count = 0   
        for t in tokens:
            c = reader.get_comment_from_token(t)
            if c is not None:
                for _ in c.splitlines():
                    count += 1
        return count




    def retrieve_file_level_analysis(self) -> None:
        """
        Retrieve the file level analysis
            
            Args:
                None
            
            Returns:
                None
            """

        for analysis in self.file_analysis:
            hld = analysis.__dict__
            hld["cc"] = analysis.average_cyclomatic_complexity
            hld["cc_rank"] = cc_rank(hld["cc"])
            hld["additions"] = self.additions_dict[hld["filename"]]
            hld["comments"] = self.retrieve_file_comments(hld["filename"])
            hld["tot_lines"] = hld["nloc"] + hld["comments"]
            hld["func_details"] = []

            if len(hld["function_list"]) > 0:
                hld["num_functions"] = len(hld["function_list"])
                hld["avg_lines_per_function"] = []
                hld["avg_token_per_function"] = []
                for funct in hld["function_list"]:
                    func_hld = funct.__dict__
                    func_hld["comments"] = func_hld["length"] - func_hld["nloc"]

                    hld["avg_lines_per_function"].append(func_hld["length"])
                    hld["avg_token_per_function"].append(func_hld["token_count"])
                    hld["func_details"].append(func_hld)
                hld["avg_lines_per_function"] = sum(hld["avg_lines_per_function"]) / hld["num_functions"]
                hld["avg_token_per_function"] = sum(hld["avg_token_per_function"]) / hld["num_functions"]
            
            else:
                hld["num_functions"] = 0
                hld["avg_lines_per_function"] = 0
                hld["avg_token_per_function"] = 0

            f_name = hld["filename"][2:]
            hld["file_name"] = f_name
            del hld["filename"]
            del hld["function_list"]
            self.file_level.append(hld)

    

    def retrieve_repo_summary(self) -> None:
        """
        Retrieve the repo summary

        Args:
            None
        
        Returns:
            None
        """

        keys = list(self.file_level[0].keys())
        keys.remove("func_details")
        keys.remove("file_name")
        keys.remove("cc_rank")
        hld = {key:[] for key in keys}

        for dict in self.file_level:
            for key in keys:
                hld[key].append(dict[key])
        
        for key in keys:
            if key not in ["cc", "avg_lines_per_function", "avg_token_per_function"]:
                hld[key] = sum(hld[key])
            else:
                hld[key] = sum(hld[key]) / len(self.file_level)
            
        hld["cc_rank"] = cc_rank(hld["cc"])
        self.repo_summary = hld

    

    def run_analysis(self) -> dict:
        """
        Runs the analysis

        Args:
            None
        
        Returns:
            dict: Repo summary
        """

        self.retrieve_file_level_analysis()
        self.retrieve_repo_summary()
        return {"repo_summary":self.repo_summary, "file_level":self.file_level}
        
    



