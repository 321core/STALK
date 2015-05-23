# -*- coding: utf-8 -*-
# pubsubsocket.py

import time
import socket
import struct
import traceback

import requests


class PubSubSocket(object):
	def __init__(self, channel_server_address):
		assert isinstance(channel_server_address)
		super(PubSubSocket, self).__init__()
		self.__channel_server_address = channel_server_address
		self.__request_stop_receiving = False

	def request_stop_receiving(self):
		self.__request_stop_receiving = True

	@staticmethod
	def parse_binary_response(data):
		assert isinstance(data, str)
		if len(data) == 0:
			return struct.unpack('>B', data)

		elif len(data) == 5:
			success, time_token = struct.unpack('>Bf', data)
			return success, time_token

		elif len(data) >= 9:
			success, time_token, num = struct.unpack('>BfI', data[:9])
			offset = 9
			messages = []
			for idx in range(num):
				sz = struct.unpack('>I', data[offset:offset + 4])
				assert sz > 0
				offset += 4

				m = data[offset:offset + sz]
				messages.append(m)
				offset += sz

			return success, time_token, messages

		else:
			assert False

	def send(self, channel, command, payload=None):
		assert isinstance(channel, str)
		assert isinstance(command, str)
		assert payload is None or isinstance(payload, str)

		if payload:
			data = '(' + command + ',' + payload + ')'
		else:
			data = '(' + command + ')'

		ret = self.do_request(channel, 'send', data=data)
		if ret:
			return self.parse_binary_response(ret)

		return [0, "Not Sent", "0"]

	def recv(self, channel, callback, time_token=0):
		assert isinstance(channel, str)
		assert isinstance(time_token, (float, int, long))

		not_subscribed = True if time_token == 0 else False

		while not self.__request_stop_receiving:
			try:
				ret = self.do_request(channel, 'recv', params={'timetoken': "%f" % time_token})
				if ret is None:
					continue

				ret = self.parse_binary_response(ret)
				success = ret[0]
				time_token = ret[1]

				if len(ret) >= 3:
					messages = ret[2]
				else:
					messages = []

				if success and not_subscribed:
					not_subscribed = False
					callback(None, None)

				if not len(messages):
					continue

				for m in messages:
					assert m[0] == '('
					assert m[-1] == ')'
					idx = m.find(',')
					if idx >= 0:
						command, payload = m[1:idx], m[idx+1:-1]
					else:
						command = m[1:-1]
						payload = None

					if not callback(command, payload):
						return

			except Exception:
				traceback.print_exc()
				time.sleep(1)

		return True

	def do_request(self, channel, action, params=None, data=None):
		assert isinstance(channel, str)
		assert isinstance(action, str)
		assert params is None or isinstance(params, dict)
		assert data is None or isinstance(data, str)

		url = 'http://%s/%s/%s' % (self.__channel_server_address, channel, action)

		try:
			if data is not None:
				ret = requests.post(url, params=params, data=data, headers={'Content-Type': 'application/octet-stream'}, timeout=60)
			else:
				ret = requests.get(url, params=params, timeout=60)

			return ret.content

		except socket.timeout:
			return None

		except Exception:
			return None

