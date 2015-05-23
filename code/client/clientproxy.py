# -*- coding: utf-8 -*-
# clientproxy.py

import socket
import json

import conf
from pubsubsocket import PubSubSocket
from channelproxy import ChannelProxy
import apiclient


class ClientProxy(object):
	def __init__(self, sensor_name, server_address):
		assert isinstance(server_address, (tuple, list))
		assert len(server_address) == 2
		assert isinstance(server_address[0], str)
		assert isinstance(server_address[1], int)
		assert isinstance(sensor_name, str)

		super(ClientProxy, self).__init__()

		self.__server_address = tuple(server_address)
		self.__receive_thread = None
		self.__sensor_name = sensor_name
		self.__running = False
		self.__channel_proxies = []

	def start(self):
		assert not self.__running

		self.__running = True

		ret = apiclient.listen(conf.USER_NAME, conf.PASSWORD, self.__sensor_name)
		if ret:
			channel_server_address, channel = ret
			s = PubSubSocket(channel_server_address)
			s.recv(channel, self.channel_message_received)

	def channel_message_received(self, command, payload):
		if command == 'connect':
			message = json.loads(payload)
			tx_channel = message['tx_channel']
			rx_channel = message['rx_channel']
			channel_server_address = message['channel_server_address']

			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
			s.connect(self.__server_address)

			proxy = ChannelProxy(s, rx_channel, tx_channel, channel_server_address)
			proxy.start()
			self.__channel_proxies.append(proxy)

		return True
