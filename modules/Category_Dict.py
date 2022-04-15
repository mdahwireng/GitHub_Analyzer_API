class Metrics_Summary_Dict:
    """
    Class to create the meta dictionary to hold the max, min and breakpoints of measured metrics.

    Methods:
        get_metrics_summary_dict(): Returns the metrics summary dict.
        set_min_max_dict(): Sets the min and max dict.
        get_category_break_points(): Returns the category break points.
    """
    def __init__(self, metrics_list, github_analysis_dict, sum_list)->None:
        """
        Initialize the class.
        Returns None.

        Parameters:
        metrics_list (list): list of metrics to be analyzed.
        github_analysis_dict (dict): dictionary of github analysis data.
        sum_list (list): list of metrics for which a sum should be generated.

        Returns:
            None.
        """
        self.metrics_list = metrics_list
        self.df = github_analysis_dict
        self.sum_list = sum_list
        self.metrics_summary_dict = dict()
        self.sum_dict = dict()

    def set_min_max_dict(self)->None:
        """
        Gets the min and max dict for the given metrics list and github analysis dict.
        Returns None.

        Args:
            metrics_list (list): The list of metrics for which min and max values should be retrieved.
            github_analysis_dict (dict): The github analysis dict.

        Returns:
            None.
        """
        hld = {m:{"max":-1, "min":10000000} for m in self.metrics_list}

        min_max_dict = dict()
        min_max_dict.update(hld)

        for k in min_max_dict.keys():
            for user_id in self.df.keys():
                if "error" not in self.df[user_id]["repo_anlysis_metrics"]:
                    val = self.df[user_id]["repo_anlysis_metrics"][k]

                    if val < hld[k]["min"]:
                        min_max_dict[k]["min"] = val 

                    if val > hld[k]["max"]:
                        min_max_dict[k]["max"] = val
        self.min_max_dict =  min_max_dict

    def set_sum_dict(self)->None:
        """
        Sets values for self.sum_dict.

        Returns:
            None.
        """
        sum_dict = {m:(0 if m in self.sum_list else None) for m  in self.metrics_list}

        for m in self.sum_list:
            for user_id in self.df.keys():
                if "error" not in self.df[user_id]["repo_anlysis_metrics"]:
                    val = self.df[user_id]["repo_anlysis_metrics"][m]
                    sum_dict[m] += val

        self.sum_dict = sum_dict



    def get_break_points(self,_min,_max, num_cat=4)->list:
        """
        Gets the break points for the given min and max values.
        Returns the break points.
        
            Args:
                _min (int): The min value.
                _max (int): The max value.
                num_cat (int): The number of categories.
        
            Returns:
                list: The break points.
        """
        div = (_max  - _min)/num_cat
        if div == 0:
            return [0 for i in range(num_cat)]
        return [_min + (i*div) for i in range(1,num_cat)]


    def get_category_break_points(self)->dict:
        """
        Gets the category break points for the given min and max values.
        Returns the category break points.

        Args:
            min_max_dict (dict): The min and max dict.

        Returns:
            dict: The category break points.
        """
        self.set_min_max_dict()
        hld = {i:{"break_points":self.get_break_points(self.min_max_dict[i]["min"], self.min_max_dict[i]["max"])}
            for i in self.min_max_dict.keys()}
        return hld


    def get_metrics_summary_dict(self)->dict:
        """
        Gets the metrics summary dict for the given metrics list and github analysis dict.
        Returns the metrics summary dict.

        Args:
            metrics_list (list): The list of metrics for which min and max values should be retrieved.
            github_analysis_dict (dict): The github analysis dict.

        Returns:
            dict: The metrics summary dict.
        """
        self.set_sum_dict()
        category_break_points = self.get_category_break_points()
        self.metrics_summary_dict.update(self.min_max_dict)
        for k,v in category_break_points.items():
            self.metrics_summary_dict[k]["break_points"] = v["break_points"]
            self.metrics_summary_dict[k]["sum"] = self.sum_dict[k]
        return self.metrics_summary_dict