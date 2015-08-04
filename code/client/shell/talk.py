#! /usr/bin/python
# -*- coding: utf-8 -*-
# talk.py

import optparse
import json
from socket import AF_INET, SOCK_STREAM, SOL_SOCKET, SO_KEEPALIVE, IPPROTO_TCP, \
                   TCP_KEEPINTVL, TCP_KEEPCNT
import socket

DEFAULT_SERVICE_PORT = 8989
service_port = DEFAULT_SERVICE_PORT


class RequestError(Exception):
    pass


def request(line):
    assert isinstance(line, str)
    s = socket.socket(AF_INET, SOCK_STREAM)
    s.setsockopt(SOL_SOCKET, SO_KEEPALIVE, 1)
    #s.setsockopt(IPPROTO_TCP, TCP_KEEPIDLE, 1)
    s.setsockopt(IPPROTO_TCP, TCP_KEEPINTVL, 3)
    s.setsockopt(IPPROTO_TCP, TCP_KEEPCNT, 5)

    try:
        s.connect(('localhost', service_port))
        s.sendall(line + '\n')
        buf = ''
        while not buf or buf[-1] != '\0':
            ret = s.recv(4096)
            if not ret:
                raise RequestError('stalk service error.')

            buf += ret

    except socket.error:
        raise RequestError('stalk service error.')

    ret = ret[:-1]
    if ret:
        ret = json.loads(ret)
        return ret

    return ''


def status():
    try:
        items = request('status')

    except RequestError, e:
        print e.message
        return

    assert isinstance(items, list)

    if items:
        print 'id\ttype\tchannel\tdescription'
        print '-' * 80
        for item in items:
            assert isinstance(item, dict)
            assert 'kind' in item
            assert item['kind'] in ('server', 'client')
            assert 'channel' in item

            if item['kind'] == 'server':
                assert 'target' in item
                assert isinstance(item['target'], list)
                assert len(item['target']) == 2
                addr, port = item['target']
                txt = '%s:%d' % (addr, port)

            elif item['kind'] == 'client':
                assert 'port' in item
                assert isinstance(item['port'], int)
                txt = '%d' % item['port']

            print '%d\t%s\t%s\t%s' % (item['id'], item['kind'], item['channel'], txt)
    else:
        print 'No any entries.'


def server(channel, target):
    assert isinstance(channel, str)
    assert isinstance(target, tuple)
    assert len(target)==2
    assert isinstance(target[0], str)
    assert isinstance(target[1], int)

    addr, port = target
    line = 'server %s %s %d' % (channel, addr, port)

    try:
        ret = request(line)
        assert isinstance(ret, str)

    except RequestError, e:
        print e.message
        return

    if ret:
        print ret


def client(channel, port):
    assert isinstance(channel, str)
    assert port is None or isinstance(port, int)

    if port is None:
        line = 'client %s' % channel

    else:
        line = 'client %s %d' % (channel, port)

    try:
        ret = request(line)

    except RequestError, e:
        print e.message
        return

    return ret


def kill(id):
    assert isinstance(id, int)

    line = 'kill %d' % id

    try:
        ret = request(line)
        assert isinstance(ret, str)

    except RequestError, e:
        print e.message
        return

    if ret:
        print ret


# parse options
parser = optparse.OptionParser()
parser.add_option('--service-port', dest='service_port', type=int, default=DEFAULT_SERVICE_PORT)
options, args = parser.parse_args()

service_port = options.service_port

# process command
if args:
    cmd = args[0]
else:
    cmd = None

if cmd == 'status':
    status()

elif cmd == 'server':
    channel = args[1]
    addr = args[2]
    port = int(args[3])
    server(channel, (addr, port))

elif cmd == 'client':
    channel = args[1]

    port = None
    if len(args) >= 3:
        port = int(args[2])

    ret = client(channel, port)

    if port is None:
        print 'Local port:%d' % ret

elif cmd == 'kill':
    id = int(args[1])
    kill(id)

else: # TODO: print usage (help)
    pass

