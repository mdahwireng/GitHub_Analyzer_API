import requests
import os
import subprocess




def send_get_req(_url, _header=None) -> tuple:
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


def retrieve_topk_langs(user, repo, headers, topk=3) -> list:
    """
    Retrieves topk languages in a github repository. 
    Returns list of tuple of language and percentage of language in repository

    Args:
        user(str): github username
        repo(str): name of repo to retrieve meta data from
        headers(dict): header to attach to the request
        topk(int): the number of top languages to retrieve, default = 3

    Returns:
        list of tuple of language and percentage of language in repository
    """

    languages_url = "https://api.github.com/repos/{}/{}/languages".format(user,repo)
    languages = send_get_req(_url=languages_url, _header=headers)[0].json()
    
    #find the total contribution of all languages
    total_contribs = sum([languages[l] for l in languages]) 

    #calculate % of language contribution
    lang_list = [(l, float("{:.2f}".format(languages[l]/total_contribs * 100))) \
                        for l in languages]                 
    
    #sort languages by % of contribution
    lang_list.sort(key=lambda x:x[1], reverse=True)         
    
    #return topk languages
    return lang_list[:topk]



