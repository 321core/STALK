#! /usr/bin/python
# -*- coding: utf-8 -*-
# talkd.py

import os
import optparse
from socket import AF_INET, SOCK_STREAM, SOCK_DGRAM, SOL_SOCKET, \
    SO_REUSEADDR, SO_KEEPALIVE, SO_BROADCAST
import socket
import threading
import time
import subprocess
import traceback

import requests

import core
import webui



#
core.restore()


# constants
service_port = core.conf.PORT


# parse options
parser = optparse.OptionParser()
parser.add_option('--service-port', dest='service_port', type=int, default=service_port)
options, args = parser.parse_args()

service_port = options.service_port


# service handler
def process_line(l):
    args = l.split()
    cmd = args[0]
    if cmd == 'status':
        return core.status()

    elif cmd == 'server':
        channel = args[1]
        addr = args[2]
        port = int(args[3])
        return core.server(channel, (addr, port))

    elif cmd == 'client':
        channel = args[1]
        try:
            port = int(args[2])
        except IndexError:
            port = None

        return core.client(channel, port)

    elif cmd == 'kill':
        id = int(args[1])
        return core.kill(id)

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
            buf = buf[idx + 1:]
            ret = process_line(line)
            try:
                s.sendall(ret + '\0')
            except socket.error:
                s.close()
                return

        except ValueError:
            pass


# discovery
def broadcast():
    server_key = ''
    s = None

    while True:
        try:
            url = 'http://%s/identity/' % core.conf.INDEX_SERVER_BASE_URL
            ret = requests.get(url, timeout=5)
            server_key = ret.json()['result']['identity']

        except Exception:
            traceback.print_exc()
            pass

        message = 'STALKAGENT@%s\nWEB_UI:%d\nWEB_SSH:%d\nACCOUNT:%s\nSERVER:%s' % \
                  (socket.gethostname(), core.conf.WEBUI_PORT, core.conf.WEBSSH_PORT, core.conf.USER_NAME, server_key)

        try:
            if s is None:
                s = socket.socket(AF_INET, SOCK_DGRAM)
                s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

            s.sendto(message, ('<broadcast>', core.conf.BROADCAST_PORT))
            time.sleep(3.0)

        except Exception:
            traceback.print_exc()
            time.sleep(1.0)
            s = None


t = threading.Thread(target=broadcast)
t.setDaemon(True)
t.start()

# web ui
t = threading.Thread(target=webui.run)
t.setDaemon(True)
t.start()

# web SSH
path = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(path, 'webshell')
path = os.path.join(path, 'webshell.py')
web_ssh_process = subprocess.Popen(['python', path, '-i', '0.0.0.0', '-p', str(core.conf.WEBSSH_PORT), '--ssl-disable'])


# service loop
s = socket.socket(AF_INET, SOCK_STREAM)
s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
s.setsockopt(SOL_SOCKET, SO_KEEPALIVE, 1)
s.bind(('localhost', service_port))

save_on_exit = True

try:
    while True:
        s.listen(5)
        c, addr = s.accept()
        t = threading.Thread(target=service_handler, args=(c, addr))
        t.setDaemon(True)
        t.start()

except KeyboardInterrupt:
    print 'Shutting down...'
    core.killall()
    save_on_exit = False

finally:
    web_ssh_process.kill()
    if save_on_exit:
        print 'saving...'
        core.save()

print 'Good bye.'
