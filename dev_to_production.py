from modules.strapi_methods import get_table_data_strapi, insert_data_strapi, update_data_strapi



def retrieve_table_data(url, index_cols):
    """Retrieves table data and returns a dictionary with table index as key and table values in cluding index as values"""
    table_data_dict = get_table_data_strapi(url)

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



def query_table(url, pluralapi, index_cols, data):
    """Queries strapi tables and returns data"""
    q_url = url

    # create the query url string
    for i in range(len(index_cols)):
        if i == 0:
            q_url = q_url + "/{}?filters[{}][$eq]={}".format(pluralapi, index_cols[i], data[index_cols[i]])
        else:
            q_url = q_url + "&filters[{}][$eq]={}".format(index_cols[i], data[index_cols[i]])
    
    q_data = retrieve_table_data(q_url, index_cols)
    return q_data


def run_checks(dev_key, dev_values, prod_data):
    """Runs check to determine whether an in dev table exist in production table and returns 
    a string of the appropriate action to take"""
    
    print("\nChecking if entry exist in production table...\n\n")
    
    if dev_key in prod_data:

        print("\nEntry exists in production table\n")
        print("Checking if entry is the same...\n\n")
        
        if dev_values == prod_data[dev_key]["attributes"]:
           
            print("Entry is the same in both production and development tables")
            return "same"
        else:
            print("Entry is not the same in production table\n")
            return "update"

    else:
        print("\nEntry does not exists in production table\n")
        return "insert"


def dev_to_prod(dev_url, prod_url, plural_api, index_cols):
    """Runs the migration of changes from dev tables to production tables"""
    
    print("\nWorking on {} table...\n".format(plural_api))

    dev_data = retrieve_table_data(url=dev_url+"/"+plural_api, index_cols=index_cols)
    
    for k,v in dev_data.items():
        dev_key = k
        dev_values = v["attributes"]
        
        prod_data = query_table(url=prod_url, pluralapi=plural_api, index_cols=index_cols, data = dev_values)

        check = run_checks(dev_key, dev_values, prod_data)

        if check == "same":
            pass

        elif check == "update":
            print("Updating entry in production table...\n")
            prod_value_id = prod_data[dev_key]["id"]
            
            #update production table
            update_data_strapi(data=dev_values, pluralapi=plural_api, entry_id=prod_value_id, url=prod_url)

        elif check == "insert":
            print("Creating entry in production table...\n\n")
            
            #insert entry in production table
            insert_data_strapi(data=dev_values, pluralapi=plural_api, url=prod_url)


if __name__ == "__main__":
    
    dev_url = "https://dev-cms.10academy.org/api"
    prod_url = "https://cms.10academy.org/api"

    p_api_index_dict = {"github-user-metas":["trainee_id", "week"], 
                        "github-repo-metas":["trainee_id", "week"], 
                        "github-repo-metrics":["trainee_id", "week"], 
                        "github-repo-metric-ranks":["trainee_id", "week"], 
                        "github-metrics-summaries":["metrics", "batch", "week"]}

    for k,v in p_api_index_dict.items():
        plural_api = k
        index_cols = v
        dev_to_prod(dev_url, prod_url, plural_api=plural_api, index_cols=index_cols)