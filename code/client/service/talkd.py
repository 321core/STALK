#! /usr/local/bin/python
# -*- coding: utf-8 -*-
# talkd.py

import optparse
from socket import AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, SO_KEEPALIVE
import socket
import json
import threading

import core


# constants
service_port = core.conf.PORT


# parse options
parser = optparse.OptionParser()
parser.add_option('--service-port', dest='service_port', type=int, default=service_port)
options, args = parser.parse_args()

service_port = options.service_port


# proxies
proxies = []
next_id = 1


def proxy_by_id(id):
    for p in proxies:
        if p.id == id:
            return p


def proxy_to_item(p):
    if isinstance(p, core.ClientProxy):
        return {
            'id': p.id,
            'kind': 'server',
            'channel': p.sensor_name,
            'target': p.server_address
        }

    elif isinstance(p, core.ServerProxy):
        return {
            'id': p.id,
            'kind': 'client',
            'channel': p.sensor_name,
            'port': p.port
        }

    assert False


# interfaces

def status():
    res = []
    for p in proxies:
        res.append(proxy_to_item(p))

    return json.dumps(res)


def server(channel, target):
    global next_id

    assert isinstance(channel, str)
    assert isinstance(target, tuple)
    assert len(target) == 2

    addr, port = target
    p = core.ClientProxy(next_id, channel, (addr, port))
    next_id += 1
    proxies.append(p)
    p.start()

    return ''


def client(channel, port):
    global next_id

    assert isinstance(channel, str)
    assert isinstance(port, int)

    p = core.ServerProxy(next_id, channel, port)
    next_id += 1
    proxies.append(p)
    p.start()

    return ''


def kill(id):
    p = proxy_by_id(id)
    if p:
        p.stop()
        proxies.remove(p)

        return ''

    return 'error'


# service handler
def process_line(l):
    args = l.split()
    cmd = args[0]
    if cmd == 'status':
        return status()

    elif cmd == 'server':
        channel = args[1]
        addr = args[2]
        port = int(args[3])
        return server(channel, (addr, port))

    elif cmd == 'client':
        channel = args[1]
        port = int(args[2])
        return client(channel, port)

    elif cmd == 'kill':
        id = int(args[1])
        return kill(id)

    assert False


def service_handler(s, addr):
    assert isinstance(s, socket.socket)

    buf = ''
    while True:
        try:
            ret = s.recv(4096)
            if not ret:
                s.close()
                return

            buf += ret

        except socket.error:
            s.close()
            return

        try:
            idx = buf.index('\n')
            line = buf[:idx]
            buf = buf[idx+1:]
            ret = process_line(line)
            try:
                s.sendall(ret + '\0')
            except socket.error:
                s.close()
                return

        except ValueError:
            pass


# service loop
s = socket.socket(AF_INET, SOCK_STREAM)
s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
s.setsockopt(SOL_SOCKET, SO_KEEPALIVE, 1)
s.bind(('localhost', service_port))

while True:
    s.listen(5)
    c, addr = s.accept()
    t = threading.Thread(target=service_handler, args=(c, addr))
    t.setDaemon(True)
    t.start()
