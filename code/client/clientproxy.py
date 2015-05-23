# -*- coding: utf-8 -*-
# clientproxy.py

import socket
import uuid
import json

import requests

from pubsubsocket import PubSubSocket
from channelproxy import ChannelProxy


class ClientProxy(object):  # tx_channel 을 subscribe 하며, tx_channel 로 수신되는 모든 데이터를 serveraddr 로 커넥팅.
	def __init__(self, sensor_name, server_address, channel_server_address):
		assert isinstance(server_address, (tuple, list))
		assert len(server_address) == 2
		assert isinstance(server_address[0], str)
		assert isinstance(server_address[1], int)
		assert isinstance(sensor_name, str)
		assert isinstance(channel_server_address, (str, unicode))

		super(ClientProxy, self).__init__()

		self.__server_address = tuple(server_address)
		self.__pubsubsocket = PubSubSocket(channel_server_address)
		self.__channel_server_address = channel_server_address
		self.__receive_thread = None
		self.__sensor_name = sensor_name
		self.__running = False
		self.__channel_proxies = []

	def start(self):
		assert not self.__running

		self.__running = True

		channel = 'c-' + str(uuid.uuid4())
		ret = requests.get('http://nini.duckdns.org:8100/api/register/%s/?channel=%s' % (self.__sensor_name, channel), timeout=60)

		# FIXME: channel server address 를 index server 에서 가져오는 것으로.

		self.__pubsubsocket.recv(channel, self.channel_message_received)

	def channel_message_received(self, command, payload):
		if command == 'connect':
			message = json.loads(payload)
			tx_channel = message['tx_channel']
			rx_channel = message['rx_channel']

			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
			s.connect(self.__server_address)

			proxy = ChannelProxy(s, rx_channel, tx_channel, self.__channel_server_address)
			proxy.start()
			self.__channel_proxies.append(proxy)

		return True
