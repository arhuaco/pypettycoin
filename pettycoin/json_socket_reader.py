'''
  Read a JSON from a socket stream.

  TODO:

    - Does not work when the JSON has a '{' or '}' inside a string. Fix.
    - Move test to another file.
    -
'''

import logging
import socket_wrapper
import sys
import time

class JsonSocketReader:
    ''' Read JSON strings from a noblocking socket.
        The length of the JSON string is not known in advance. '''
    def __init__(self, sock, max_json_size=1024*1024):
        self.sock = sock
        self.last_chunk = bytes()
        self.json_buff = ''
        self.json_ready = ''
        self.n_open = 0 # Number of '{' chars open.
        self.max_json_reply_size = max_json_size

    def should_read_more(self):
        ''' Is the socket healthy? Can we read more? '''
        return self.sock.is_healthy()

    def match_next(self, timeout):
        ''' Try to match a JSON string. '''
        if len(self.last_chunk) == 0:
            # Mixing bytes and unicode concepts here. Not an issue, we hope.
            #len(bytes('á', 'utf-8')) == 2, len('á') == 1.
            allowed_read_size = self. max_json_reply_size - len(self.json_buff)
            assert allowed_read_size >= 0
            status, self.last_chunk = self.sock.receive(allowed_read_size,
                                                        timeout)
            if not status:
                return False

        try:
            self.last_chunk = bytes.decode(self.last_chunk)
        except UnicodeDecodeError:
            logging.warning('Unicode decode error. Recovering...')
            # We probably read an incomplete character. Let's keep reading.
            return False

        for idx in range(len(self.last_chunk)):
            if self.last_chunk[idx] == '{':
                self.n_open += 1
            elif self.last_chunk[idx] == '}':
                self.n_open -= 1
                assert self.n_open >= 0 # malformed JSON will break this assert.
            self.json_buff += self.last_chunk[idx]
            if self.n_open == 0 and max(len(self.json_buff), idx) > 0: # {...}
                # Inneficient if we expect multiple JSON answers in a reply.
                self.last_chunk = bytes(self.last_chunk[idx + 1:], 'utf-8')
                self.json_ready = self.json_buff
                self.json_buff = ''
                return True
        self.last_chunk = bytes()
        return False

    def get_json(self):
        ''' Get the matched json. '''
        return self.json_ready

    def wait_for_json(self, timeout=0):
        ''' Try to match a JSON sting with the given timeout. '''
        assert timeout >= 0
        first_time = True
        while first_time or timeout >= 0.0:
            time_before = time.time()
            if self.sock.wait_until_read_available(timeout):
                if self.match_next(0):
                    return True
            timeout -= time.time() - time_before
            first_time = False
        logging.error('Timeout in wait_for_json.')
        return False

def main():
    ''' Our main function. Only for testing. '''
    sock = socket_wrapper.Socket()
    if not sock.connect_inet('localhost', 2020):
        return 1
    sock.make_nonblocking()
    reader = JsonSocketReader(sock)
    while reader.should_read_more():
        if reader.wait_for_json(timeout=0.1):
            print('Got json:{}'.format(reader.get_json()), file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(main())
