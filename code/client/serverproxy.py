# -*- coding: utf-8 -*-
# serverproxy.py

import socket
import uuid
import json

import conf
from channelproxy import ChannelProxy
from pubsubsocket import PubSubSocket
import apiclient


class ServerProxy(object):
	def __init__(self, sensor_name, port):
		assert isinstance(port, int)
		assert isinstance(sensor_name, str)

		super(ServerProxy, self).__init__()

		self.__port = port
		self.__sensor_name = sensor_name
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

			ret = apiclient.connect(conf.USER_NAME, conf.PASSWORD, self.__sensor_name)
			if ret:
				channel_server_address, channel = ret
				rx_channel = 'rx-' + str(uuid.uuid4())
				tx_channel = 'tx-' + str(uuid.uuid4())

				proxy = ChannelProxy(s, rx_channel, tx_channel, channel_server_address)
				proxy.start()
				self.__proxies.append(proxy)

				s = PubSubSocket(channel_server_address)
				s.send(ret['result']['channel'], 'connect',
				       json.dumps({'tx_channel': rx_channel,
				                   'rx_channel': tx_channel,
				                   'channel_server_address': channel_server_address}))

			else:
				s.close()

	def stop(self):
		self.__running = False
		self.__socket.close()
		self.__socket = None
