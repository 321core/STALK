import json
import optparse
import socket
import threading
import time
import traceback
from socket import AF_INET, SOCK_STREAM, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SO_KEEPALIVE, SO_BROADCAST
from typing import Sequence

import requests

import core
import webui


def add_server_if_not_registered(channel: str, port: int):
    for entry in json.loads(core.status()):
        if entry['kind'] == 'server' and (entry['target'][0], entry['target'][1]) == ('localhost', port):
            return

    core.server(channel, ('localhost', port))


def init():  # 자동으로 SSH 포트를 등록한다. 이게 옳은 건지 판단해보아야.
    # restore
    core.restore()

    # SSH
    channel = socket.gethostname().lower().replace('.', '-')
    add_server_if_not_registered(channel + '-ssh', 22)
    core.save()


# service handler
def process_line(line: bytes):
    line: str = line.decode()
    args: Sequence[str] = line.split()

    cmd = args[0]

    if cmd == 'status':
        return core.status()

    elif cmd == 'server':
        channel = args[1]
        addr = args[2]
        port = int(args[3])
        ret = core.server(channel, (addr, port))
        core.save()
        return ret

    elif cmd == 'client':
        channel = args[1]
        try:
            port = int(args[2])
        except IndexError:
            port = None

        ret = core.client(channel, port)
        core.save()
        return ret

    elif cmd == 'kill':
        pid = int(args[1])
        ret = core.kill(pid)
        core.save()
        return ret

    assert False


def service_handler(s: socket.socket, addr):
    assert isinstance(s, socket.socket)

    buf: bytes = b''
    while True:
        try:
            ret = s.recv(4096)
            if not ret:
                s.close()
                return

            buf += ret

        except socket.error as e:
            s.close()
            return

        try:
            idx = buf.index(b'\n')
            line = buf[:idx]
            buf = buf[idx + 1:]
            ret = process_line(line)
            try:
                s.sendall(ret.encode() + b'\0')
            except socket.error as e:
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

        except requests.exceptions.RequestException:
            traceback.print_exc()
            pass

        message = 'STALKAGENT@%s\nWEB_UI:%d\nACCOUNT:%s\nSERVER:%s' % (socket.gethostname(), core.conf.WEBUI_PORT, core.conf.USER_NAME, server_key)

        try:
            if s is None:
                s = socket.socket(AF_INET, SOCK_DGRAM)
                s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

            s.sendto(message.encode(), ('<broadcast>', core.conf.BROADCAST_PORT))
            time.sleep(3.0)

        except socket.error:
            traceback.print_exc()
            time.sleep(1.0)
            s = None


def main():
    init()

    # constants
    service_port: int = core.conf.PORT

    # parse options
    parser = optparse.OptionParser()
    parser.add_option('--service-port', dest='service_port', type=int, default=service_port)
    options, args = parser.parse_args()

    service_port = options.service_port

    t = threading.Thread(target=broadcast)
    t.setDaemon(True)
    t.start()

    # web ui
    t = threading.Thread(target=webui.run)
    t.setDaemon(True)
    t.start()

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
        print('Shutting down...')
        core.killall()
        save_on_exit = False

    finally:
        if save_on_exit:
            print('saving...')
            core.save()

    print('Good bye.')


if __name__ == '__main__':
    main()
