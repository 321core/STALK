import json
import os
import socket
from typing import Optional, Tuple

from . import apiclient
from . import conf
from .clientproxy import ClientProxy
from .serverproxy import ServerProxy

# proxies
proxies = []
next_id = 1


def proxy_by_id(id):
    for p in proxies:
        if p.id == id:
            return p


def proxy_to_item(p):
    if isinstance(p, ClientProxy):
        return {
            'id': p.id,
            'kind': 'server',
            'channel': p.sensor_name,
            'target': p.server_address
        }

    elif isinstance(p, ServerProxy):
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


def server(channel: str, target: Tuple[str, int]):
    global next_id

    assert isinstance(channel, str)
    assert isinstance(target, tuple)
    assert len(target) == 2

    addr, port = target
    p = ClientProxy(next_id, channel, (addr, port))
    next_id += 1
    proxies.append(p)
    p.start()

    return ''


def client(channel: str, port: Optional[int] = None):
    global next_id

    assert port is None or isinstance(port, int)

    try:
        p = ServerProxy(next_id, channel, port)
    except socket.error:
        if isinstance(port, int):
            return '"port %d is already occupied."' % port

        return '"error occured."'

    next_id += 1
    proxies.append(p)
    p.start()

    return '%d' % p.port


def kill(id_: int):
    p = proxy_by_id(id_)
    if p:
        apiclient.kill(conf.USER_NAME, conf.PASSWORD, p.sensor_name)
        p.stop()
        proxies.remove(p)

        return ''

    return 'error'


def killall():
    global proxies

    for p in proxies:
        apiclient.kill(conf.USER_NAME, conf.PASSWORD, p.sensor_name)
        p.stop()

    proxies = []


# persistency

def status_file_path():
    if os.path.isabs(conf.DATA_DIR):
        res = conf.DATA_DIR

    elif conf.DATA_DIR.startswith('~'):
        res = os.path.expanduser(conf.DATA_DIR)

    else:
        res = os.path.dirname(os.path.realpath(__file__))
        res = os.path.join(res, "..")
        res = os.path.join(res, conf.DATA_DIR)

    if not os.path.exists(res):
        os.makedirs(res)

    res = os.path.join(res, 'status')
    return res


def restore():
    global proxies
    global next_id

    assert len(proxies) == 0
    assert next_id == 1

    try:
        f = open(status_file_path(), 'r')
        items = json.load(f)
        for item in items:
            if item['kind'] == 'server':
                p = ClientProxy(item['id'], str(item['channel']), (str(item['target'][0]), item['target'][1]))
                proxies.append(p)
                p.start()
                next_id = max(next_id, p.id + 1)

            elif item['kind'] == 'client':
                p = ServerProxy(item['id'], str(item['channel']), item['port'])
                proxies.append(p)
                p.start()
                next_id = max(next_id, p.id + 1)

            else:
                assert False

    except IOError:
        pass


def save():
    try:
        ret = status()
        f = open(status_file_path(), 'w')
        f.write(ret)
        f.close()

    except IOError as e:
        print(e.message)
