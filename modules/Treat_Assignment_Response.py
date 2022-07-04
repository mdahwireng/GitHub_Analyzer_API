import json
import pandas as pd
from datetime import datetime
from dateutil import parser
import pytz
import requests


class Get_Assignment_Data:
    def __init__(self, week, batch, base_url, token, previous_analyzed_assignments=[]):
        self.week = week
        self.batch = batch
        self.base_url = base_url
        self.token = token
        self.previous_analyzed_assignments = previous_analyzed_assignments



    def send_get_req(self, _url, _header=None) -> tuple:
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



    def get_assignment_data(self):
        """
        Gets assignment data from assignment table
        """

        week = "week "+ self.week[4:]

        q_query = """query getAssingmentCategroy($batch: Int!,$topic:String!) {
        assignments(
            pagination: { start: 0, limit: 1000 }
            filters: {
            
            assignment_category: { topic:{eq:$topic} batch: { Batch: { eq: $batch } } }
            }
        ) {
            data {
            id
            attributes {
                assignment_submission_content
                gclass_submission_identifier
                assignment_category{
                data{
                    attributes{
                    name
                    topic
                    due_date
                    }
                }
                }
                trainee {
                data {
                    id
                    attributes {
                    email
                    trainee_id
                    }
                }
                }
            }
            }
        }
        }"""

        q_variables = {"batch": self.batch, "topic": week}
        

        url = self.base_url+"/graphql?query={}&variables={}".format(q_query, json.dumps(q_variables))

        #url = base_url+"/graphql?query={}".format(query)

        if self.token:
            headers = { "Authorization": "Bearer {}".format(self.token), "Content-Type": "application/json"}
        else:
            headers = {"Content-Type": "application/json"}

        try:
            resp, resp_status = self.send_get_req(url, headers)

            return resp.json()
        except Exception as e:
            return {"error": e} # return error message if any

    
    def link_root(self, lnk):
        if "blob" in lnk:
            lnk = lnk.replace("blob","tree")

        if "tree" in lnk:
            txt = lnk
            txt_split = txt.split("tree/")
            root = txt_split[0] + "tree/" + txt_split[1].split("/")[0]
        else:
            root = lnk

        return root



    def get_filtered_assignment_data(self, assignments):
        details = {}
        subs_dict = {}
        analyzed_assignments = set()
        utc=pytz.UTC

        default_due_date = datetime.now().replace(tzinfo=utc)
        run_date = datetime.now().replace(tzinfo=utc)
        
        for asn in assignments["data"]['assignments']["data"]:
            for dt in asn['attributes']['assignment_submission_content']:
                due_date = asn["attributes"]["assignment_category"]["data"]["attributes"]["due_date"]
                
                assignment_name = asn['attributes']['assignment_category']['data']['attributes']['name']

                if not due_date:
                    due_date = default_due_date
                else:
                    due_date = parser.parse(due_date).replace(tzinfo=utc)
                
                
                
                if dt['type'] == "github-link" and due_date < run_date and assignment_name not in self.previous_analyzed_assignments:
                    
                    lnk = dt['url']
                    root = self.link_root(lnk)
                    dt.update({"root_url":root})
                    trainee_data = asn['attributes']["trainee"]["data"]
                    trainee = trainee_data["id"]
                    trainee_id = trainee_data["attributes"]["trainee_id"]
                    assignment_id = asn['id']
                    
                    if assignment_name not in analyzed_assignments:

                        print("\nAnalyzing {}\n".format(assignment_name))

                    
                    if trainee_id not in subs_dict:
                        subs_dict[trainee_id] = {"final":[], "interim":[], "other":[]}
                    
                    if "final" in assignment_name.lower():
                        subs_dict[trainee_id]["final"].append(lnk)
                    elif "interim" in assignment_name.lower():
                        subs_dict[trainee_id]["interim"].append(lnk)
                    else:
                        subs_dict[trainee_id]["other"].append(lnk)
                    
                    
                    if trainee_id not in details.keys():
                        details[trainee_id] = {}

                    if "root_url" not in details[trainee_id].keys():
                        details[trainee_id]["root_url"] = []
                    
                    if "assignments_ids" not in details[trainee_id].keys():
                        details[trainee_id]["assignments_ids"] = set()

                    if "trainee" not in details[trainee_id].keys():
                        details[trainee_id]["trainee"] = trainee
                    
                    details[trainee_id]["root_url"].append(root)
                    details[trainee_id]["assignments_ids"].add(assignment_id)
                    
                    analyzed_assignments.add(assignment_name)
         
        self.analyzed_assignments = set(analyzed_assignments)
        self.subs_dict = subs_dict

        return details


    
    def get_filtered_assignment_data_records(self, filtered_assignment_data):
        asn_df_list = []
        for k,v in filtered_assignment_data.items():
            
            if self.subs_dict[k]["final"]:
                root_url = self.subs_dict[k]["final"][0]
            elif self.subs_dict[k]["interim"]:
                root_url = self.subs_dict[k]["interim"][0]
            else:
                other_urls = self.subs_dict[k]["other"]
                other_urls.sort()
                root_url = other_urls[0]

            asn_df_dict = {"trainee":v["trainee"], "trainee_id":k, "root_url":root_url, "assignments_ids":list(v["assignments_ids"])}
            asn_df_list.append(asn_df_dict)

        return asn_df_list


    
    def filtered_data_df(self):
        try:
            assignment_data = self.get_assignment_data()
            filtered_assignment_data = self.get_filtered_assignment_data(assignment_data)
            filtered_assignment_data_records = self.get_filtered_assignment_data_records(filtered_assignment_data)
            data_df = pd.DataFrame(filtered_assignment_data_records)
            return data_df
        except Exception as e:
            return {"error": e}

    def get_analyzed_assignments(self):
        """
        Returns a list of assignments that have been analyzed
        """
        return self.analyzed_assignments







