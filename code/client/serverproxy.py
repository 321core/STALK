# -*- coding: utf-8 -*-
# serverproxy.py

import socket
import uuid

import requests

from channelproxy import ChannelProxy
from pubsubclient import PubSubClient


class ServerProxy(object):  # port 를 리슨하며, 수신되는 데이터를 모두 channel 로 redirecting
	def __init__(self, sensor_name, port):
		assert isinstance(port, int)
		assert isinstance(sensor_name, str)

		super(ServerProxy, self).__init__()

		self.__port = port
		self.__sensor_name = sensor_name
		self.__pubsubclient = PubSubClient()
		self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
		self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.__socket.bind(('', self.__port))
		self.__running = False
		self.__proxies = []

	def start(self):
		assert not self.__running

		self.__running = True

		while self.__running:
			print 'listening...'

			self.__socket.listen(1)
			s, addr = self.__socket.accept()

			# find channel
			ret = requests.get('http://nini.duckdns.org:8100/api/query/%s/' % self.__sensor_name, timeout=60)
			ret = ret.json()
			# print ret  # print channel finding result.

			if ret['code'] == 'ok':
				rx_channel = 'rx-' + str(uuid.uuid4())
				tx_channel = 'tx-' + str(uuid.uuid4())

				proxy = ChannelProxy(s, rx_channel, tx_channel)
				proxy.start()
				self.__proxies.append(proxy)

				self.__pubsubclient.publish({
					'channel': ret['result']['channel'],
					'message': {
						'command': 'connect',
						'tx_channel': rx_channel,
						'rx_channel': tx_channel
					}
				})

			else:
				s.close()

	def stop(self):
		self.__running = False
		self.__socket.close()
		self.__socket = None
