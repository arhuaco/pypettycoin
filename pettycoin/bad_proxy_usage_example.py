import requests
import json
import sys

def main():
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
        print('response:', json.loads(response.text))
    except Exception as e:
        print('Got exception:', e)
    return 0

if __name__ == "__main__":
    sys.exit(main())
