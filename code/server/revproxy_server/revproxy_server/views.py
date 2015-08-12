# -*- coding: utf-8 -*-
# views.py

import requests
from revproxy.views import ProxyView
from django.http import HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt


__proxy_views = {}
__counter = 0


def get_proxy_view(ip_address, port):
    global __counter

    key = 'http://%s:%d' % (ip_address, port)
    try:
        return __proxy_views[key]

    except KeyError:
        pass

    name = 'ProxyClass_%04d' % (__counter)
    __counter += 1
    cls = type(name, (ProxyView,), {'upstream': key})
    __proxy_views[key] = cls
    return __proxy_views[key]


@csrf_exempt
def index(req, path):
    hostname = req.META['HTTP_HOST']
    arr = hostname.split('.')
    channel = arr[0]
    account = arr[1]

    ret = requests.get('http://localhost:8987/bind?channel=%s&account=%s' % (channel, account))

    if ret.ok and ret.json()['code'] == 'success':
        ip_address = ret.json()['ip_address']
        port = int(ret.json()['port'])
        return get_proxy_view(ip_address, port).as_view()(req, path=path)

    return HttpResponseNotFound('<h1>Channel Not Found</h1><p>channel:%s<br/>account:%s</p>' % (channel, account))

