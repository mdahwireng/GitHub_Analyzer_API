import requests
import json

from modules.api_utils import send_get_req

def insert_data_strapi(data, pluralapi, url="https://dev-cms.10academy.org/api", token=False)->None:
    """ 
    Insert data into strapi table given data, pluralapi and strapi token
    Returns None
    
    Args:
        data: json data to be inserted
        pluralapi: plural api of the table in which data is to be inserted
        url: link to the strapi table
        token: strapi token to be used for authentication

    Returns:
        None
    """
    # set headers for authentication
    if token:
        headers = { "Authorization": "Bearer {}".format(token), "Content-Type": "application/json"}
    else:
        headers = {"Content-Type": "application/json"}
    
    url = url + "/{}"

    insert_url =  url.format(pluralapi)
    
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


def update_data_strapi(data, pluralapi,entry_id, url="https://dev-cms.10academy.org/api", token=False)->None:
    """
    Update data in strapi table given data, pluralapi and strapi token
    Returns None

    Args:
        data: json data to be updated
        pluralapi: plural api of the table in which data is to be updated
        token: strapi token to be used for authentication
        url: link to the strapi table
        entry_id: strapi entry id of the data to be updated

    Returns:
        None
    """
    # set headers for authentication
    if token:
        headers = { "Authorization": "Bearer {}".format(token), "Content-Type": "application/json"}
    else:
        headers = {"Content-Type": "application/json"}
    
    url = url + "/{}/{}"

    insert_url =  url.format(pluralapi,entry_id)
    
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


    
    

def get_table_data_strapi(url,token=False)->list:
    """
    Get data from strapi table given pluralapi and strapi token
    Returns list of data retireved data.

    Args:
        url: url of strapi table
        token: strapi token to be used for authentication

    Returns:
        list of data retireved data.
    """

    # set headers for authentication
    if token:
        headers = { "Authorization": "Bearer {}".format(token), "Content-Type": "application/json"}
    else:
        headers = {"Content-Type": "application/json"}
    
    data = []
    start = 0
    
    if "?" in url:
        insert_url = url + "&pagination[start]={}&pagination[limit]=100"
    else:
        insert_url = url + "?pagination[start]={}&pagination[limit]=100"

    
    try:
        r = requests.get(
                        insert_url.format(start),
                        headers = headers
                        ).json()
                        
        total = r["meta"]["pagination"]["total"]
        data.extend(r["data"])

        # loop to retrieve all availabe data
        while len(data) < total:
            start += 100
            r = requests.get(
                            insert_url.format(start),
                            headers = headers
                            ).json()
            data.extend(r["data"])
            
        if "error" in r:
            print("Error: {}".format(r["error"]))
            return [{"error": r["error"]}]
        else:
            print("Data retrieved successfully from {}".format(url))
            return data
    except Exception as e:
        return [{"error": e}]


def get_trainee_data(batch, base_url, token):
    """
    Gets trainee data from trainee table
    """
    query = """query getTraineeId{{
    trainees(pagination:{{start:0,limit:200}} filters:{{batch:{{Batch:{{eq:{}}}}}}}){{
    data{{
      id
      attributes{{
        trainee_id
        email
      }}
    }}
    }}
    }}""".format(batch)

    url = base_url+"/graphql?query={}".format(query)

    if token:
        headers = { "Authorization": "Bearer {}".format(token), "Content-Type": "application/json"}
    else:
        headers = {"Content-Type": "application/json"}

    try:
        resp, resp_status = send_get_req(url, headers)

        return resp.json()["data"]["trainees"]["data"]
    except Exception as e:
        return {"error": e}


    
    
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