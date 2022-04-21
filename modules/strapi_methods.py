import requests
import json

def insert_data_strapi(data, pluralapi,token=False)->None:
    """ 
    Insert data into strapi table given data, pluralapi and strapi token
    Returns None
    
    Args:
        data: json data to be inserted
        pluralapi: plural api of the table in which data is to be inserted
        token: strapi token to be used for authentication

    Returns:
        None
    """
    # set headers for authentication
    if token:
        headers = { "Authorization": "Bearer {}".format(token), "Content-Type": "application/json"}
    else:
        headers = {"Content-Type": "application/json"}
    
    insert_url =  "https://dev-cms.10academy.org/api/{}".format(pluralapi)
    
    try:
        r = requests.post(
                        insert_url,
                        data = json.dumps({"data":data}),
                        headers = headers
                        ).json()
        
        if "error" in r:
            print("Error: {}".format(r["error"]))
        
        else:
            print("Data uploaded successfully into {}".format(pluralapi))
            print(r["data"],"\n")
    
    except Exception as e:
        print("Error: {}".format(e))


def update_data_strapi(data, pluralapi,entry_id, token=False)->None:
    """
    Update data in strapi table given data, pluralapi and strapi token
    Returns None

    Args:
        data: json data to be updated
        pluralapi: plural api of the table in which data is to be updated
        token: strapi token to be used for authentication
        entry_id: strapi entry id of the data to be updated

    Returns:
        None
    """
    # set headers for authentication
    if token:
        headers = { "Authorization": "Bearer {}".format(token), "Content-Type": "application/json"}
    else:
        headers = {"Content-Type": "application/json"}
    
    insert_url =  "https://dev-cms.10academy.org/api/{}/{}".format(pluralapi,entry_id)
    
    try:
        r = requests.put(
                        insert_url,
                        data = json.dumps({"data":data}),
                        headers = headers
                        ).json()
        
        if "error" in r:
            print("Error: {}".format(r["error"]))
        
        else:
            print("Data updated successfully into {}".format(pluralapi))
            print(r["data"],"\n")
    
    except Exception as e:
        print("Error: {}".format(e))


    
    

def get_table_data_strapi(pluralapi,token=False)->list:
    """
    Get data from strapi table given pluralapi and strapi token
    Returns list of data retireved data.

    Args:
        pluralapi: plural api of the table from which data is to be retrieved
        token: strapi token to be used for authentication

    Returns:
        list of data retireved data.
    """

    # set headers for authentication
    if token:
        headers = { "Authorization": "Bearer {}".format(token), "Content-Type": "application/json"}
    else:
        headers = {"Content-Type": "application/json"}
    
    insert_url =  "https://dev-cms.10academy.org/api/{}?pagination[start]=0&pagination[limit]=100".format(pluralapi)
    
    try:
        r = requests.get(
                        insert_url,
                        headers = headers
                        ).json()
            
        if "error" in r:
            print("Error: {}".format(r["error"]))
            return [r["error"]]
        else:
            print("Data retrieved successfully from {}".format(pluralapi))
            return r["data"]
    except Exception as e:
        return [{"error": e}]
    

    
    
def upload_to_strapi(strapi_table_pairing, token=False)->None:
    """
    Upload data to strapi table given strapi_table_pairing and local dataframe pairing dictionary
    Returns None

    Args:
        strapi_table_pairing: dictionary of strapi table and local dataframe pairing
        token: strapi token to be used for authentication

    Returns:
        None
    """
    for p_api, df in strapi_table_pairing.items():
        df.replace("N/A", None, regex=True, inplace=True)
        for data in json.loads(df.to_json(orient="records")):
            insert_data_strapi(pluralapi=p_api, data=data, token=token)