'''

Simple socket wrapper.

'''

import errno
import select
import socket
import sys

MAX_RECV_LEN = 4096

class Socket:
    ''' Just a socket wrapper. Is there anything better I should be using? '''

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.is_ok = False

    def make_nonblocking(self):
        ''' Make the socket nonblocking. '''
        self.sock.setblocking(0)

    def connect(self, host, port):
        ''' Connect the socket. '''
        try:
            self.sock.connect((host, port))
        except socket.error as error:
            print('Socket.connect got exception: {}'.format(error),
                  file=sys.stderr)
            return False
        self.is_ok = True
        return True

    def fileno(self):
        '''' Return the file number of this socket. '''
        return self.sock.fileno()

    def is_healthy(self):
        ''' Retuns true if the socket is open and ready. '''
        return self.is_ok

    def close(self):
        ''' Close the socket. '''
        self.is_ok = False
        try:
            self.sock.shutdown()
            self.sock.close()
        except socket.error as error:
            print('Socket.shutdown/close got exception: {}'.format(error),
                  file=sys.stderr)
            return False
        return True

    def sendall(self, msg, timeout=None):
        ''' Send with timeout. If timeout is None, write can block. '''
        self.sock.settimeout(timeout)
        try:
            return self.sock.sendall(msg) == None
        except socket.error as error:
            print('Socket.sendall got exception: {}'.format(error),
                  file=sys.stderr)
            self.is_ok = error.args[0] != errno.EWOULDBLOCK
        return False

    def receive(self, max_len, timeout=None):
        ''' Receive from socket. If timeout is None, read can block. '''
        self.sock.settimeout(timeout)
        received = bytes()
        while len(received) < max_len:
            len_before = len(received)
            try:
                received += self.sock.recv(min(max_len -
                                               len(received), MAX_RECV_LEN))
            except socket.error as error:
                print('Socket.recv got exception: {}'.format(error),
                      file=sys.stderr)
                assert self.is_ok
                self.is_ok = error.args[0] != errno.EWOULDBLOCK
            if len(received) == len_before:
                # When the socket has an error condtion the first time we
                # might return true but the next call should fail.
                if len(received) == 0:
                    self.is_ok = False
                break
        return len(received) > 0, received

    def wait_until_read_available(self, timeout):
        ''' Wait until the socket can be read. Fail if a timeout is reached. '''
        try:
            ready, _, _ = select.select([self.fileno()], [], [], timeout)
            return len(ready) > 0
        except socket.error as error:
            print('Socket exception: {}'.format(error), file=sys.stderr)
            self.is_ok = False # TODO: Is this OK?
            return False