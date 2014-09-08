''' How to use the Bad Pettycoin Proxy. '''

import requests
import json
import pprint
import sys

def main():
    ''' Main function. '''
    url = 'http://localhost:10001/jsonrpc'
    headers = {'content-type': 'application/json'}
    payload = {
        'method': 'getinfo',
        'params': [],
        'jsonrpc': '2.0',
        'id': 0,
    }
    data = json.dumps(payload)
    try:
        response = requests.post(url, data=data, headers=headers)
        pprint.pprint(json.loads(response.text))
        return 0
    except Exception as error:
        print('Got exception:', error)
        return 1

if __name__ == "__main__":
    sys.exit(main())
