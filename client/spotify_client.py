#!/usr/bin/env python
# coding: utf-8

# In[1]:


import base64
import datetime
from urllib.parse import urlencode

import requests


# In[19]:


class SpotifyAPI(object):
    # default variables
    access_token = None
    access_token_expires = datetime.datetime.now()
    access_token_did_expire = True
    client_id = None
    client_secret = None
    token_url = "https://accounts.spotify.com/api/token"
    base_url = "https://api.spotify.com"
    
    def __init__(self, client_id, client_secret, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_id = client_id
        self.client_secret = client_secret
    
    def get_client_credentials(self):
        """
        Returns a base64 encoded string
        """
        client_id = self.client_id
        client_secret = self.client_secret
        
        # if client_id / client_secret are not set raise exception
        if client_id == None or client_secret == None:
            raise Exception("You must set client_id and client_secret")
        client_creds = f"{client_id}:{client_secret}"
        client_creds_b64 = base64.b64encode(client_creds.encode()) # encode to byte then convert to b64
        return client_creds_b64.decode() # decode the b64 from bytes
    
    def get_token_data(self):
        return {
            "grant_type": "client_credentials"
        }
    
    def get_token_headers(self):
        client_creds_b64 = self.get_client_credentials()
        return {
            "Authorization": f"Basic {client_creds_b64}"
        }
    
    def perform_auth(self):
        token_url = self.token_url
        token_data = self.get_token_data()
        token_headers = self.get_token_headers()
        
        # sends a request to Spotify API
        r = requests.post(token_url, data=token_data, headers=token_headers)
        # checks if valid request
        if r.status_code not in range(200, 299):
            raise Exception("Could not authenticate client.")
        data = r.json() # our token received from Spotify
        access_token = data['access_token'] # token needed to request data from Spotify
        expires_in = data['expires_in'] # seconds until the token expires
        now = datetime.datetime.now() # datetime right now to create datetime of when token expires
        expires = now + datetime.timedelta(seconds=expires_in) # gives expiration a datetime stamp
        self.access_token = access_token
        self.access_token_expires = expires # sets access_token_expires = expires
        self.access_token_did_expire = expires < now # boolean, checks if access token expired
        return True
    
    def get_access_token(self):
        token = self.access_token
        expires = self.access_token_expires
        now = datetime.datetime.now()
        if expires < now:
            self.perform_auth()
            return self.get_access_token()
        elif token == None:
            self.perform_auth()
            return self.get_access_token()
        return token
    
    def get_resource_header(self):
        access_token = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        return headers
    
    def get_resource(self, lookup_id, resource_type="artists", version="v1"):
        base_url = self.base_url
        endpoint = f"{base_url}/{version}/{resource_type}/{lookup_id}"
        headers = self.get_resource_header()
        r = requests.get(endpoint, headers=headers)
        if r.status_code not in range(200,299):
            return {}
        return r.json()
    
    def get_album(self, _id):
        return self.get_resource(_id, resource_type='albums')
    
    def get_artist(self, _id):
        return self.get_resource(_id, resource_type='artists')
    
    def base_search(self, query_params):
        base_url = self.base_url
        endpoint = f"{base_url}/v1/search"
        headers = self.get_resource_header()
        lookup_url = f"{endpoint}?{query_params}"
        r = requests.get(lookup_url, headers=headers)
        if r.status_code not in range(200, 299):
            return {}
        return r.json()
    
    def search(self, query=None, operator=None, operator_query=None, search_type="artist"):
        if query == None:
            raise Exception("A query is required")
        if isinstance(query,dict):
            query = " ".join([f"{k}:{v}" for k,v in query.items()])
        if operator != None and operator_query != None:
            if operator.lower() == "or" or operator.lower() == "not":
                operator = operator.upper()
                if isinstance(operator_query, str):
                    query = f"{query} {operator} {operator_query}"
        query_params = urlencode({"q": query, "type": search_type.lower()})
        return self.base_search(query_params)

