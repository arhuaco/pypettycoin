'''
  Let's show some Pettycoin information in the WEB.
  TODO:
    - Reconnect UNIX socket if the connection is lost.
'''

from flask import Flask
from json_socket_reader import JsonSocketReader

import json
import logging
import os
import pprint
import socket_wrapper
import sys

HTTP_PORT = 10002
HTTP_HOST = 'localhost'
PETTYCOIN_SOCKET = '~/.pettycoin/pettycoin-rpc'

def make_request(method, params=None):
    ''' Make the JSON string. '''
    if params == None:
        params = []
    req = {
        'method': method,
        'params': params,
        'jsonrpc': '2.0',
        'id': 0,
    }
    return json.dumps(req)

class Pettycoin:
    ''' Manage Pettycoin socket and make JSON-RPC calls. '''

    def __init__(self):
        self.sock = socket_wrapper.Socket(unix_socket=True)
        self.sock.make_nonblocking()
        if not self.sock.connect_unix(os.path.expanduser(PETTYCOIN_SOCKET)):
            logging.error('Could not open socket: {}'.format(PETTYCOIN_SOCKET))
            sys.exit(1)
        self.petty_reader = JsonSocketReader(self.sock)

    def send(self, method='', params=None):
        ''' Send JSON request. '''
        if params == None:
            params = []
        buff = bytes(make_request(method=method, params=params), 'utf-8')
        return self.sock.sendall(buff)

    def get_reply(self):
        ''' Get the Pettycoin reply from UNIX socket. '''
        status = self.petty_reader.wait_for_json(timeout=5.0)
        if status:
            return True, self.petty_reader.get_json_str()
        return False, ''

    def info(self):
        ''' Pettycoin info. '''
        if self.send(method='getinfo'):
            status, json_str = self.get_reply()
            if status:
                try:
                    return True, pprint.pformat(json.loads(json_str))
                except Exception as err:
                    logging.error('Could not get info JSON'.format(str(err)))
        return False, ''

PTC = Pettycoin()

APP = Flask(__name__)

@APP.route('/')
def index():
    ''' Generate the homepage. '''
    status, info_json = PTC.info()
    if status:
        return '<pre>{}</pre>'.format(info_json)
    else:
        return 'Could not get Pettycoin info.'

def main():
    ''' Our main function. '''
    logging.basicConfig(level=logging.INFO)
    APP.run(host=HTTP_HOST, port=HTTP_PORT)

if __name__ == '__main__':
    main()
