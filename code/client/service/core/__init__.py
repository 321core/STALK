# -*- coding: utf-8 -*-
# core/__init__.py

import os
import json

import conf
from clientproxy import ClientProxy
from serverproxy import ServerProxy

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


def server(channel, target):
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


def client(channel, port):
    global next_id

    assert isinstance(channel, str)
    assert isinstance(port, int)

    p = ServerProxy(next_id, channel, port)
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


# persistency

def restore():
    global proxies
    global next_id

    assert len(proxies) == 0
    assert next_id == 1

    path = os.path.join(conf.DATA_DIR, 'status')

    try:
        f = open(path, 'r')
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
        path = os.path.join(conf.DATA_DIR, 'status')
        f = open(path, 'w')
        f.write(ret)
        f.close()

    except IOError, e:
        print e.message
