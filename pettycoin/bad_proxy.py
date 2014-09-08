'''

  Bad  Pettycoin Proxy.

  This proxy is useful for a quick test where you can use HTTP JSON RPC.

  It is called 'bad' because pettycoin makes JSON RPC in a more efficient way,
  but you have to read the response (with unknown length) from an UNIX socket.

'''

import cgi
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging
import sys

HTTP_PORT = 10001
HTTP_HOST = 'localhost'

class HTTPRequestHandler(BaseHTTPRequestHandler):
    ''' Our HTTP handler. '''

    def __init__(self, *args, **kwargs):
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
                text = self.html_parser.unescape(escaped_text)
                json_request = json.loads(text)
                json_method = json_request['method']
            except Exception as err:
                message = 'Could not parse request. Error: {}'.format(str(err))
                self.custom_error(status=400, message=message)
                return
            logging.debug(json_request)
            logging.info('method: {}'.format(json_method))
            self.send_response(200, 'OK')
            self.send_header('Content-type', 'text/json')
            self.end_headers()
            self.wfile.write(bytes('{"a" : "1"}', 'utf-8'))
        else:
            self.custom_error(status=404, message='Use /jsonrpc.')

def main():
    ''' Our main function. '''
    logging.basicConfig(level=logging.INFO)
    http_server = HTTPServer((HTTP_HOST, HTTP_PORT), HTTPRequestHandler)
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
