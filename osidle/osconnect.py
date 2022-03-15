#
#    Copyright 2022 - Carlos A. <https://github.com/dealfonso>
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
import os
import requests
import json
from dateutil.parser import parse as datetimeparser
from .common import *

class Token:
    def __str__(self):
        return "Token: {}\nURL: {}\nExpiration: {}".format(self._token, self._url, self._expiration)

    def __init__(self):
        self._token = None
        self._url = None
        self._expiration = None

    """
    Method to force getting a token from OpenStack
    """
    def get(self):
        passwd = os.environ.get('OS_PASSWORD')
        url_base = os.environ.get('OS_AUTH_URL')
        user = os.environ.get('OS_USERNAME')

        headers = {'Content-Type': 'application/json', "X-OpenStack-Nova-API-Version": "2.48"}
        obj = { "auth": { "scope":"system", "identity": { "methods": [ "password" ], "password": { "user": { "name": user, "domain": { "id": "default" }, "password": passwd } } } } }

        now = datetime.now().timestamp()

        # Make a request to create the token
        try:
            p_debugv("creating a new token at {}/auth/tokens".format(url_base))
            token_req = requests.post("{}/auth/tokens".format(url_base), data=json.dumps(obj), headers=headers, timeout = 5)
        except Exception as e:
            p_error("Could not connect to OpenStack: {}".format(e))
            return False

        # Check if the request was successful
        if (token_req.status_code < 200 or token_req.status_code >= 300):
            p_error("Failed to connect to OpenStack")
            return False

        if 'X-Subject-Token' not in token_req.headers:
            p_error("Failed to obtain the token")
            return False

        token = token_req.headers['X-Subject-Token']

        # Now deal with the content of the request
        token_req = token_req.json()

        # Get the nova endpoint
        nova_ep = None
        for endpoint in token_req["token"]["catalog"]:
            if endpoint["name"] == "nova":
                nova_ep = endpoint
                break

        if nova_ep is None:
            p_error("could not get nova endpoint")
            return False

        admin_ep = None
        for ep in nova_ep["endpoints"]:
            if ep["interface"] == "admin":
                admin_ep = ep
                break

        if admin_ep is None:
            p_error("could not get nova admin endpoint")
            return False

        token_issued = datetimeparser(token_req['token']['issued_at'])
        token_expires = datetimeparser(token_req['token']['expires_at'])

        # Now store the information about the token
        p_debug("Token obtained: {}".format(token))
        self._expiration = datetime.fromtimestamp(now + token_expires.timestamp() - token_issued.timestamp() )
        self._url = admin_ep['url']
        p_debugv("Token expiration at: {}".format(self._expiration))
        p_debugv("Token URL: {}".format(self._url))
        self._token = token
        return True

    def isValid(self):
        if self._token is None:
            return False
        if self._expiration < datetime.now():
            return False
        return True

    def renewIfNeeded(self):
        if not self.isValid():
            return self.get()
        return True

    @property
    def url(self):
        return self._url
    @property
    def token(self):
        return self._token

def getServers(token):
    # Gets the information regarding to the servers, using the provided token
    # @param token: the token to use
    # @return: a list of dictionaries, each one containing the information about a server or None if an error happened
    if not token.renewIfNeeded():
        p_error("could not get a valid token")
        return None

    try:
        servers_req = requests.get(token.url + "/servers?all_tenants=1", headers = {'X-Auth-Token': token.token }, timeout = 5)
    except Exception as e:
        print(e)
        p_error("Could not connect to OpenStack")
        return None

    servers = servers_req.json()
    return servers["servers"]

def getServerInfo(token, id):
    # Gets the information regarding to the server with the given id, using the provided token
    # @param token: the token to use
    # @param id: the id of the server
    # @return: a json object containing the information about the server or None if an error happened
    if not token.renewIfNeeded():
        p_error("could not get a valid token")
        return None

    try:
        serverinfo_req = requests.get("{}/servers/{}/diagnostics".format(token.url, id), headers = {'X-Auth-Token': token.token , "X-OpenStack-Nova-API-Version": "2.48"}, timeout = 15)
    except:
        p_error("Could not connect to OpenStack")
        return None

    return serverinfo_req.json()

def checkConnection(token):
    # Checks if the token is still valid
    # @param token: the token to use
    # @return: True if the token is still valid, False otherwise
    if not token.renewIfNeeded():
        p_error("could not get a valid token")
        return False

    return True
