from flask import Flask, jsonify
import requests

app = Flask(__name__)

@app.route('/user/<string:user>/<string:token>',methods=["GET"])
def get_user(user, token):
    headers = {"Authorization":"Bearer {}".format(token)}
    resp = requests.get('https://api.github.com/users/{}'.format(user), headers=headers)
    if resp.status_code == 200:
        d = resp.json()
        info_list = ['name', 'email', 'bio','followers', 'following']
        dt = {k:d[k] for k in info_list}
        dt["repos"] = {"public_repos": d["public_repos"], "total_private_repos":d["total_private_repos"], \
             "owned_private_repos":d["owned_private_repos"]}
        return jsonify(dt)
    else:
        return jsonify({"error":"Not Found"})