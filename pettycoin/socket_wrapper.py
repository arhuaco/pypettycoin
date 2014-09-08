'''

Simple socket wrapper. Is there anything I should be using instead?

'''

import errno
import logging
import select
import socket
import sys

MAX_RECV_LEN = 4096

class Socket:
    ''' Just a socket wrapper. '''

    def __init__(self, unix_socket=False):
        if unix_socket:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        else:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.unix_socket = unix_socket
        self.is_ok = False

    def make_nonblocking(self):
        ''' Make the socket nonblocking. '''
        self.sock.setblocking(0)
        return True

    def connect_inet(self, host, port):
        ''' Connet an Internet socket. '''
        assert not self.unix_socket
        try:
            self.sock.connect((host, port))
        except socket.error as error:
            logging.error('Socket.connect got exception: {}'.format(error))
            return False
        self.is_ok = True
        return True

    def connect_unix(self, path):
        ''' Connect an UNIX socket. '''
        assert self.unix_socket
        try:
            self.sock.connect(path)
        except socket.error as error:
            logging.error('Socket.connect got exception: {}'.format(error))
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
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
        except socket.error as error:
            logging.error('Socket close got exception: {}'.format(error))
            return False
        return True

    def sendall(self, msg, timeout=None):
        ''' Send with timeout. If timeout is None, write can block. '''
        assert self.is_ok
        self.sock.settimeout(timeout)
        try:
            return self.sock.sendall(msg) == None
        except socket.error as error:
            self.is_ok = error.args[0] == errno.EWOULDBLOCK
            if not self.is_ok:
                logging.error('Socket.sendall got exception: {}'.format(error))
        return self.is_ok

    def receive(self, max_len, timeout=None):
        ''' Receive from socket. If timeout is None, read can block. '''
        assert self.is_ok
        self.sock.settimeout(timeout)
        received = bytes()
        while len(received) < max_len:
            len_before = len(received)
            try:
                received += self.sock.recv(min(max_len -
                                               len(received), MAX_RECV_LEN))
            except socket.error as error:
                self.is_ok = error.args[0] == errno.EWOULDBLOCK
                if not self.is_ok:
                    logging.error('Socket.recv got exception: {}'.format(error))
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
            logging.error('Socket.select exception: {}'.format(error))
            self.is_ok = False # TODO: Is this OK?
            return False
