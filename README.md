# GitHub API Task
### Navigation
  - [Introduction](#introduction)
  - [Directory Structure](#directory-structure)
    - [Modules](#modules)
    - [Images](#images)
    - [Tests](#tests)
  - [Setup](#setup)
  - [Endpoints](#endpoints)
    - [User](#user)
        - [Demo](#user_demo)
    - [Repo_metadata](#repo_metadata)
        - [Demo](#Repo_metadata_demo)
    - [Yet to be implemented endpoints](#yet-to-be-implemented-endpoints)
## Introduction
This project creates a **backend API** using **GitHub API** as the source with endpoints for retrieving GitHub account users details and repositories associated with given username. The following information is returned by user and repo metadata endpoints respectively:
<ul>
    <li>
        <b>Profile</b>
            <ul>
               <li> name </li>
               <li> email </li>
               <li> bio </li>
               <li> total number of repos </li>
               <li> number of followers </li>
               <li> numbers following </li>
            </ul>
    </li> </br>
    <li>
        <b>Metadata per repo</b>
            <ul>
               <li> Repo name </li>
               <li> Clones </li>
               <li> Forks </li>
               <li> Contributors </li>
               <li> Visitors </li>
               <li> Number of Branches </li>
               <li> Top 3 languages used in the repo (percentage showing their contribution)  </li>
            </ul>
    </li>
</ul>


## Directory Structure
## Modules
This directory has created modules and functions which are used for the routing. It has **controller.py** which is a python scripts which has self-written functions serve as a soure of imports for use in other section in the future when the need be.

## Images
This directory has the images for the project. It has the images which demonstrates the usage of the API.

## Tests
This directory has the tests for the modules (Yet to be built)

## Setup
You should create a **GitHub Token** associated with the username to be used. The link here will guide you through the process: [create GitHub Personal Acess Token](##https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

Create a python virtual environment with python 3.8, activate the environment and install the requirements. Then run the **app.py** to run the **API Server**.

```
pip install -r requirements.txt
python app.py
```

## Endpoints
## User
### User_Demo

Request in the format <em>host:port/user/{username}/{token}</em>:
 <img src='images/user_endpoint_request.jpeg'>
```
host:port/user/mdahwireng/XXXXXXXXXXXXXXXX
```
 
Response:
```
{
  "bio": null, 
  "email": "kaaymike@hotmail.co.uk", 
  "followers": 4, 
  "following": 3, 
  "name": "M. D. Ahwireng", 
  "repos": {
    "owned_private_repos": 6, 
    "public_repos": 29, 
    "total_private_repos": 6
  }
}
```

## Repo_metadata
### Repo_metadata_Demo

Request in the format <em>host:port/repos_meta/{username}/{token}</em>:
<img src='images/repo_meta_endpoint_request.jpeg'>
```
host:port/user/mdahwireng/XXXXXXXXXXXXXXXX
```

Response:
```
{
  "10academy_week2": {
    "branches": 2, 
    "branches_url": "https://api.github.com/repos/mdahwireng/10academy_week2/branches{/branch}", 
    "clones": {
      "count": 0, 
      "uniques": 0
    }, 
    "contributors": [
      "mdahwireng"
    ], 
    "contributors_url": "https://api.github.com/repos/mdahwireng/10academy_week2/contributors", 
    "forks": 0, 
    "languages": [
      [
        "Jupyter Notebook", 
        100.0
      ]
    ], 
    "languages_url": "https://api.github.com/repos/mdahwireng/10academy_week2/languages", 
    "total_commits": 4, 
    "visitors": {
      "count": 0, 
      "uniques": 0
    }
  }, 
  "2021-Better-Working-World-Data-Challenge": {
    "branches": 2, 
    "branches_url": "https://api.github.com/repos/mdahwireng/2021-Better-Working-World-Data-Challenge/branches{/branch}", 
    "clones": {
      "count": 0, 
      "uniques": 0
    }, 
    "contributors": [
      "patrickmuston1", 
      "codeindulgence", 
      "alexgleith", 
      "GypsyBojangles", 
      "jlkerches"
    ], 
    "contributors_url": "https://api.github.com/repos/mdahwireng/2021-Better-Working-World-Data-Challenge/contributors", 
    "forks": 0, 
    "languages": [
      [
        "Jupyter Notebook", 
        99.25
      ], 
      [
        "Python", 
        0.72
      ], 
      [
        "Shell", 
        0.02
      ]
    ], 
    "languages_url": "https://api.github.com/repos/mdahwireng/2021-Better-Working-World-Data-Challenge/languages", 
    "total_commits": 39, 
    "visitors": {
      "count": 1, 
      "uniques": 1
    }
  }, ...
}
```
## Yet to be implemented endpoints

As this is a work in progress, there are endpoints yet to be added examples are:
- Endpoint for repository code analysis
- Endpoints for code analysis pertaining to specific languages like **Python** and **JavaScript**
