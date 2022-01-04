import requests
import os
import json
import time
#import the stream rules from the config/rules.py
from config.rules import stream_rules

# For Security we are keeping these Confidential Data into Environment Variable
# Get Tweeter Bearer Token
bearer_token = os.environ.get("BEARER_TOKEN")
# Get Tweeter Bearer Token
PBI_URL = os.environ.get("PBI_URL")

import collections

def flatten(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, list):
            #print("test")
            items.extend(flatten(v[0], new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
class TwitterClient:
    def __init__(self, bearer_token):
        self.header = self.bearer_oauth(bearer_token)

    def bearer_oauth(self, bearer_token):
        """
        Method required by bearer token authentication.
        """
        headers={}
        headers["Authorization"] = f"Bearer {bearer_token}"
        headers["User-Agent"] = "v2FilteredStreamPython"
        return headers


    def get_rules(self):
        '''
        Fetch the existing rules in the twitter stream
        '''
        response = requests.get(
            "https://api.twitter.com/2/tweets/search/stream/rules", headers=self.header
        )
        if response.status_code != 200:
            raise Exception(
                "Cannot get rules (HTTP {}): {}".format(response.status_code, response.text)
            )
        print(json.dumps(response.json()))
        return response.json()


    def delete_all_rules(self, rules):
        if rules is None or "data" not in rules:
            return None

        ids = list(map(lambda rule: rule["id"], rules["data"]))
        payload = {"delete": {"ids": ids}}
        response = requests.post(
            "https://api.twitter.com/2/tweets/search/stream/rules",
            headers=self.header,
            json=payload
        )
        if response.status_code != 200:
            raise Exception(
                "Cannot delete rules (HTTP {}): {}".format(
                    response.status_code, response.text
                )
            )
        print(json.dumps(response.json()))


    def set_rules(self, delete):
        payload = {"add": stream_rules}
        response = requests.post(
            "https://api.twitter.com/2/tweets/search/stream/rules",
            headers=self.header,
            json=payload,
        )
        if response.status_code != 201:
            raise Exception(
                "Cannot add rules (HTTP {}): {}".format(response.status_code, response.text)
            )
        print(json.dumps(response.json()))


    def get_stream(self, PBI_URL):
        response = requests.get(
            "https://api.twitter.com/2/tweets/search/stream?expansions=author_id&tweet.fields=author_id,created_at,in_reply_to_user_id,lang,referenced_tweets,reply_settings,source,text", headers=self.header, stream=True,
        )
        print(response.status_code)
        if response.status_code != 200:
            raise Exception(
                "Cannot get stream (HTTP {}): {}".format(
                    response.status_code, response.text
                )
            )
        for response_line in response.iter_lines():
            if response_line:
                json_response = json.loads(response_line)
                print(json.dumps(json_response, indent=4, sort_keys=True))
                try:
                    json_response['data']['user'] = json_response['includes']['users'] 
                except:
                    json_response['data']['user'] = "KEY ERROR"
                    print('Could not fetch users')
                data_to_pbi =flatten(json_response['data'])
                print(data_to_pbi)
                pbi_res = StreamToPBI(data_to_pbi,PBI_URL)
                print(pbi_res)

def StreamToPBI(data, url):
    '''
    Stream a dataset to PowerBI
    '''
    data = [data]

    # post/push data to the streaming API
    headers = {
    "Content-Type": "application/json"
    }

    response = requests.request(
        method="POST",
        url=url,
        headers=headers,
        data=json.dumps(data)
    )
    return response

def main():
    tw= TwitterClient(bearer_token)
    rules = tw.get_rules()
    delete = tw.delete_all_rules(rules)
    set = tw.set_rules(delete)
    tw.get_stream(PBI_URL)


if __name__ == "__main__":
    # while True:
    #     try:
    #         main()
    #     except:
    #         print("Errror Occured")
    main()