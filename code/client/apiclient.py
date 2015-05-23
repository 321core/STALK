# -*- coding: utf-8 -*-
# apiclient.py

import json

import requests

from error import *
import conf


TIMEOUT = 10


def listen(username, password, sensor_name):  #FIXME: requests 모듈로부터의 오류를 잡아주어야 한다.
	assert isinstance(username, str)
	assert isinstance(password, str)
	assert isinstance(sensor_name, str)
	data = json.dumps({'password': password})

	ret = requests.post('http://%s/listen/%s/%s/' % (conf.INDEX_SERVER_BASE_URL, username, sensor_name), data=data,
	                    headers={'Content-Type': 'application/json'}, timeout=TIMEOUT)

	if ret.ok:
		ret = ret.json()
		if ret['code'] == 'CODE_OK':
			return ret['result']['channel-server-address'], ret['result']['channel']

		else:
			raise APIError(message=ret['message'])

	else:
		raise NetworkError(message='connection failed.')


def connect(username, password, sensor_name):  #FIXME: requests 모듈로부터의 오류를 잡아주어야 한다.
	assert isinstance(username, str)
	assert isinstance(password, str)
	assert isinstance(sensor_name, str)
	data = json.dumps({'password': password})
	ret = requests.post('http://%s/connect/%s/%s/' % (conf.INDEX_SERVER_BASE_URL, username, sensor_name), data=data,
	                    headers={'Content-Type': 'application/json'}, timeout=TIMEOUT)

	if ret.ok:
		ret = ret.json()
		if ret['code'] == 'CODE_OK':
			return ret['result']['channel-server-address'], ret['result']['channel']

		else:
			raise APIError(message=ret['message'])

	else:
		raise NetworkError(message='connection failed.')
