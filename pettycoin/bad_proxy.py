'''

  Bad  Pettycoin Proxy.

  This proxy is useful for a quick test where you can use HTTP JSON RPC.

  It is called 'bad' because pettycoin makes JSON RPC in a more efficient way,
  but you have to read the response (with unknown length) from an UNIX socket.

'''

from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, HTTPServer
from json_socket_reader import JsonSocketReader

import cgi
import json
import logging
import os
import socket_wrapper
import sys

HTTP_PORT = 10001
HTTP_HOST = 'localhost'
PETTYCOIN_SOCKET = '~/.pettycoin/pettycoin-rpc'

class HTTPPettycoinProxy(BaseHTTPRequestHandler):
    ''' Our HTTP handler. '''

    def __init__(self, *args, **kwargs):
        sock = socket_wrapper.Socket(unix_socket=True)
        sock.make_nonblocking()
        if not sock.connect_unix(os.path.expanduser(PETTYCOIN_SOCKET)):
            logging.error('Could not open socket: {}'.format(PETTYCOIN_SOCKET))
            sys.exit(1)
        self.petty_sock = sock
        self.petty_reader = JsonSocketReader(sock)
        self.html_parser = HTMLParser()
        BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

    def custom_error(self, status=400, message=''):
        ''' Send a custom error message with JSON content-type. '''
        self.send_response(status, message)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

    def do_GET(self): # pylint: disable=invalid-name
        ''' GET is not supported. '''
        self.custom_error(status=400, message='GET is not supported. Use POST.')

    def do_POST(self): # pylint: disable=invalid-name
        ''' POST Request. '''
        if self.path == '/jsonrpc':
            ctype, _ = cgi.parse_header(self.headers['content-type'])
            if ctype != 'application/json':
                self.custom_error(
                    status=400,
                    message='Wrong content type. It must be application/json.')
                return
            length = int(self.headers['content-length'])
            try:
                escaped_text = self.rfile.read(length).decode('utf-8')
                req_text = self.html_parser.unescape(escaped_text)
                # We waste time parsing the JSON. We could avoit it.
                json_request = json.loads(req_text)
                json_method = json_request['method']
            except Exception as err:
                message = 'Could not parse request. Error: {}'.format(str(err))
                self.custom_error(status=400, message=message)
                return
            logging.debug(json_request)
            logging.info('method: {}'.format(json_method))

            status = self.petty_sock.sendall(bytes(req_text, 'utf-8'))
            if status:
                status = self.petty_reader.wait_for_json(timeout=0.5)
                if status:
                    petty_response = self.petty_reader.get_json_str()
            if status:
                self.send_response(200, 'OK')
            else:
                self.send_response(400, 'Pettycoin call failed.')
            self.send_header('Content-type', 'text/json')
            self.end_headers()
            if status:
                self.wfile.write(bytes(petty_response, 'utf-8'))
        else:
            self.custom_error(status=404, message='Use /jsonrpc.')

    def finish(self):
        ''' Close the UNIX socket and the server. '''
        status = self.petty_sock.close()
        logging.info('Could close Pettycoin socket?: {}'.format(status))
        BaseHTTPRequestHandler.finish(self)

def main():
    ''' Our main function. '''
    logging.basicConfig(level=logging.INFO)
    http_server = HTTPServer((HTTP_HOST, HTTP_PORT), HTTPPettycoinProxy)
    logging.info('Proxy listening, {}:{}.'.format(HTTP_HOST, HTTP_PORT))
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
    http_server.server_close()
    logging.info('Proxy stopped.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
