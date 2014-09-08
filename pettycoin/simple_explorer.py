''' Let's show some Pettycoin information in the WEB. '''

from flask import Flask
from json_socket_reader import JsonSocketReader

import json
import logging
import os
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

    def info(self):
        ''' Pettycoin info. '''


PTC = Pettycoin()

APP = Flask(__name__)

@APP.route('/')
def index():
    ''' Generate the homepage. '''
    return 'Index Page'

def main():
    ''' Our main function. '''
    APP.run(host=HTTP_HOST, port=HTTP_PORT)

if __name__ == '__main__':
    main()
