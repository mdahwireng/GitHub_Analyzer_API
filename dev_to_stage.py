import json
import os
import sys

from modules.api_utils import send_get_req
from modules.strapi_methods import get_table_data_strapi, insert_data_strapi, update_data_strapi



def retrieve_table_data(url, index_cols, token):
    """Retrieves table data and returns a dictionary with table index as key and table values in cluding index as values"""
    table_data_dict = get_table_data_strapi(url, token)

    # create an a dictionary with table index as key and table values in cluding index as values
    try:
        if len(table_data_dict) > 0 and "error" not in table_data_dict[0]:
            time_keys = ["createdAt","updatedAt","publishedAt"]
           
            # dictionary without the time columns
            data_dict = {tuple([d["attributes"][i] for i in index_cols]):({"attributes":{k:v for k,v in d["attributes"].items() if k not in time_keys}, "id":d["id"]}) for d in table_data_dict}
        else:
            if len(table_data_dict) == 0:
                data_dict = {}
            else:
                data_dict = table_data_dict[0]
    except Exception as e:
        data_dict = {"error": e}
    return data_dict



def query_table(url, pluralapi, index_cols, data, token):
    """Queries strapi tables and returns data"""
    q_url = url

    # create the query url string
    for i in range(len(index_cols)):
        if i == 0:
            q_url = q_url + "/{}?filters[{}][$eq]={}".format(pluralapi, index_cols[i], data[index_cols[i]])
        else:
            q_url = q_url + "&filters[{}][$eq]={}".format(index_cols[i], data[index_cols[i]])
    
    q_data = retrieve_table_data(q_url, index_cols, token)
    return q_data


def run_checks(dev_key, dev_values, prod_data, token, prod_base_url=None, table=None):
    """Runs check to determine whether an in dev table exist in production table and returns 
    a string of the appropriate action to take"""
    
    print("\nChecking if entry exist in production table...\n\n")
    
    if dev_key in prod_data:

        print("\nEntry exists in production table\n")
        print("Checking if entry is the same...\n\n")

        if table and prod_base_url:
            prod_entry_id = prod_data[dev_key]["id"]
            prod_data[dev_key]["attributes"]["trainee"] = get_trainee_relation_id(base_url=prod_base_url, table=table, entry_id=prod_entry_id, token=token)
        
        if dev_values == prod_data[dev_key]["attributes"]:
           
            print("Entry is the same in both production and development tables")
            return "pass"
        else:
            print("Entry is not the same in production table\n")
            return "update"

    else:
        print("\nEntry does not exists in production table\n")
        return "insert"

def get_trainee_relation_id(base_url, table, entry_id, token):
    """Retrieves the relation id using graphql and return it"""
    if "dev" in base_url:
        print("\nRetrieving trainee relationship on {} in dev...\n".format(table))
    else:
        print("\nRetrieving trainee relationship on {} in prod...\n".format(table))

    query = """query{{
                    {}(id:"{}"){{
                                data{{
                                    id
                                    attributes{{
                                                trainee_id
                                                    trainee{{
                                                        data{{
                                                            id
                                                            attributes{{
                                                                        trainee_id
                                                                        }}
                                                            }}
                                                            }}
                                                }}
                                                }}
                                }}
                    }}""".format(table, entry_id)

    if token:
        headers = { "Authorization": "Bearer {}".format(token), "Content-Type": "application/json"}
    else:
        headers = {"Content-Type": "application/json"}


    url = base_url+"graphql?query={}".format(query)
    resp, resp_status = send_get_req(url, headers)
    try:
        trainee_relation_id = resp.json()['data'][table]['data']['attributes']['trainee']['data']['id']
    except:
        trainee_relation_id = None
    return trainee_relation_id


def dev_to_prod(dev_url, prod_url, plural_api, index_cols, token, table=None):
    """Runs the migration of changes from dev tables to production tables"""
    
    print("\nWorking on {} table...\n".format(plural_api))
    if table:
        dev_base_url = dev_url[:-3]
        prod_base_url = prod_url[:-3]

    dev_data = retrieve_table_data(url=dev_url+"/"+plural_api, index_cols=index_cols, token=token["dev"])
    
    for k,v in dev_data.items():
        dev_entry_id = v["id"]
        
        if table:
            v["attributes"]["trainee"] = get_trainee_relation_id(base_url=dev_base_url, table=table, entry_id=dev_entry_id, token=token["dev"])

        dev_key = k
        dev_values = v["attributes"]
        
        prod_data = query_table(url=prod_url, pluralapi=plural_api, index_cols=index_cols, data = dev_values, token=token["stage"])

        if table:
            check = run_checks(dev_key=dev_key, dev_values=dev_values, prod_data=prod_data, prod_base_url=prod_base_url, table=table, token=token["stage"])
        else:
            check = run_checks(dev_key=dev_key, dev_values=dev_values, prod_data=prod_data, token=token["stage"])

        if check == "pass":
            pass

        elif check == "update":
            print("Updating entry in production table...\n")
            prod_value_id = prod_data[dev_key]["id"]
            
            #update production table
            update_data_strapi(data=dev_values, pluralapi=plural_api, entry_id=prod_value_id, url=prod_url, token=token["stage"])

        elif check == "insert":
            print("Creating entry in production table...\n\n")
            
            #insert entry in production table
            insert_data_strapi(data=dev_values, pluralapi=plural_api, url=prod_url, token=token["stage"])


if __name__ == "__main__":

    if os.path.exists(".env/secret.json"):
        with open(".env/secret.json", "r") as s:
            secret = json.load(s)
            try:
                strapi_token = secret["strapi_token"]
            except:
                strapi_token = None
    else:
        strapi_token = None

    
    if strapi_token:


        dev_url = "https://dev-cms.10academy.org/api"
        prod_url = "https://stage-cms.10academy.org/api"

        p_api_index_dict = {"github-user-metas":{"index":["trainee_id", "week"], "graphql":"githubUserMeta"}, 
                            "github-repo-metas":{"index":["trainee_id", "week"], "graphql":"githubRepoMeta"}, 
                            "github-repo-metrics":{"index":["trainee_id", "week"], "graphql":"githubRepoMetric"}, 
                            "github-repo-metric-ranks":{"index":["trainee_id", "week"], "graphql":"githubRepoMetricRank"}, 
                            "github-metrics-summaries":{"index":["metrics", "batch", "week"]}}

        for k,v in p_api_index_dict.items():
            plural_api = k
            index_cols = v["index"]

            if "graphql" in v:
                table = v["graphql"]
            else:
                table = None
            dev_to_prod(dev_url=dev_url, prod_url=prod_url, plural_api=plural_api, index_cols=index_cols, table=table, token=strapi_token)
    
    else:
        # if token is not returned
        print("Error: Strapi tokens were not found")
