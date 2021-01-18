import requests

from . import conf
from .error import *

TIMEOUT = 10


def listen(username: str, password: str, sensor_name: str):
    assert isinstance(username, str)
    assert isinstance(password, str)
    assert isinstance(sensor_name, str)
    # data = json.dumps({'password': password})  # NOTE: currently, not used

    resp = requests.get('http://%s/listen/%s/%s/' % (conf.INDEX_SERVER_BASE_URL, username, sensor_name), headers={'Content-Type': 'application/json'})

    try:
        ret = resp.json()
        if ret['code'] == 'CODE_OK':
            return ret['result']['channel-server-address'], ret['result']['channel']

        else:
            raise APIError(ret['message'])

    except requests.exceptions.RequestException:
        raise NetworkError('connection failed.')


def kill(username: str, password: str, sensor_name: str):
    assert isinstance(username, str)
    assert isinstance(password, str)
    assert isinstance(sensor_name, str)
    # data = json.dumps({'password': password})  # NOTE: currently, not used

    resp = requests.get('http://%s/kill/%s/%s/' % (conf.INDEX_SERVER_BASE_URL, username, sensor_name), headers={'Content-Type': 'application/json'})

    try:
        ret = resp.json()
        if ret['code'] == 'CODE_OK':
            return ''

        else:
            raise APIError(ret['message'])

    except requests.exceptions.RequestException:
        raise NetworkError('connection failed.')


def check_listen_channel(username: str, password: str, sensor_name: str, channel_name: str):
    assert isinstance(username, str)
    assert isinstance(password, str)
    assert isinstance(sensor_name, str)
    assert isinstance(channel_name, str)
    # data = json.dumps({'password': password})  # NOTE: currently, not used

    try:
        resp = requests.get('http://%s/check_listen_channel/%s/%s/' % (conf.INDEX_SERVER_BASE_URL, username, sensor_name), {'channel': channel_name}, headers={'Content-Type': 'application/json'})
        ret = resp.json()
        return ret['code'] == 'CODE_OK'

    except requests.exceptions.RequestException:
        raise NetworkError('connection failed.')


def connect(username: str, password: str, sensor_name: str):
    assert isinstance(username, str)
    assert isinstance(password, str)
    assert isinstance(sensor_name, str)
    # data = json.dumps({'password': password})  # NOTE: currently, not used.

    try:
        resp = requests.get('http://%s/connect/%s/%s/' % (conf.INDEX_SERVER_BASE_URL, username, sensor_name), headers={'Content-Type': 'application/json'})
        ret = resp.json()
        if ret['code'] == 'CODE_OK':
            return ret['result']['channel-server-address'], ret['result']['channel'], ret['result']['transfer-channel-server-address']

        else:
            raise APIError(ret['message'])

    except requests.exceptions.RequestException:
        raise NetworkError('connection failed.')
