# -*- coding: utf-8 -*-
# apiclient.py

import json
import urllib
import urllib2
import traceback

from error import *
import conf

TIMEOUT = 10


def request_get(url, params=None, headers=None):
    if params:
        url += '?' + urllib.urlencode(params)

    req = urllib2.Request(url, headers=headers)
    try:
        res = urllib2.urlopen(req, timeout=TIMEOUT)
        if res.code == 200:
            return res.read()

    except Exception:
        traceback.print_exc()

    return None


def listen(username, password, sensor_name):
    assert isinstance(username, str)
    assert isinstance(password, str)
    assert isinstance(sensor_name, str)
    # data = json.dumps({'password': password})  # NOTE: currently, not used

    ret = request_get('http://%s/listen/%s/%s/' % (conf.INDEX_SERVER_BASE_URL, username, sensor_name),
                      headers={'Content-Type': 'application/json'})

    if ret is not None:
        ret = json.loads(ret)
        if ret['code'] == 'CODE_OK':
            return ret['result']['channel-server-address'], ret['result']['channel']

        else:
            raise APIError(ret['message'])

    else:
        raise NetworkError('connection failed.')


def check_listen_channel(username, password, sensor_name, channel_name):
    assert isinstance(username, (str, unicode))
    assert isinstance(password, (str, unicode))
    assert isinstance(sensor_name, (str, unicode))
    assert isinstance(channel_name, (str, unicode))
    # data = json.dumps({'password': password})  # NOTE: currently, not used

    ret = request_get('http://%s/check_listen_channel/%s/%s/' % (conf.INDEX_SERVER_BASE_URL, username, sensor_name),
                      params={'channel': channel_name},
                      headers={'Content-Type': 'application/json'})

    if ret is not None:
        ret = json.loads(ret)
        return ret['code'] == 'CODE_OK'

    else:
        raise NetworkError('connection failed.')


def connect(username, password, sensor_name):
    assert isinstance(username, str)
    assert isinstance(password, str)
    assert isinstance(sensor_name, str)
    # data = json.dumps({'password': password})  # NOTE: currently, not used.

    ret = request_get('http://%s/connect/%s/%s/' % (conf.INDEX_SERVER_BASE_URL, username, sensor_name),
                      headers={'Content-Type': 'application/json'})

    if ret is not None:
        ret = json.loads(ret)
        if ret['code'] == 'CODE_OK':
            return ret['result']['channel-server-address'], ret['result']['channel'], \
                   ret['result']['transfer-channel-server-address']

        else:
            raise APIError(ret['message'])

    else:
        raise NetworkError('connection failed.')
