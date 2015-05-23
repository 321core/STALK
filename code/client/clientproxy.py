# -*- coding: utf-8 -*-
# clientproxy.py

import socket
import uuid
import threading
import time
import traceback

import requests

from pubsubclient import PubSubClient
from channelproxy import ChannelProxy


class ClientProxy(object):  # tx_channel 을 subscribe 하며, tx_channel 로 수신되는 모든 데이터를 serveraddr 로 커넥팅.
	def __init__(self, sensor_name, server_address):
		assert isinstance(server_address, (tuple, list))
		assert len(server_address) == 2
		assert isinstance(server_address[0], str)
		assert isinstance(server_address[1], int)
		assert isinstance(sensor_name, str)

		super(ClientProxy, self).__init__()

		self.__server_address = tuple(server_address)
		self.__pubsub_client = PubSubClient()
		self.__receive_thread = None
		self.__sensor_name = sensor_name
		self.__running = False
		self.__channel_proxies = []
		self.__channel = None

	def start(self):
		assert not self.__running

		self.__running = True
		self.__channel = 'c-' + str(uuid.uuid4())

		th = threading.Thread(target=self.register_thread_main)
		th.setDaemon(True)
		th.start()

		th = threading.Thread(target=self.pubsub_thread_main)
		th.setDaemon(True)
		th.start()

	def register_thread_main(self):
		while True:
			try:
				ret = requests.get('http://nini.duckdns.org:8100/api/register/%s/?channel=%s' % (self.__sensor_name, self.__channel), timeout=60)
				print 'register sensor:%s as channel:%s' % (self.__channel, self.__sensor_name)
				print '--> ', ret.ok

			except Exception:
				traceback.print_exc()

			time.sleep(60.0)

	def pubsub_thread_main(self):
		def channel_message_received(message):
			cmd = message['command']
			if cmd == 'connect':
				tx_channel = message['tx_channel']
				rx_channel = message['rx_channel']

				s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
				s.connect(self.__server_address)

				proxy = ChannelProxy(s, rx_channel, tx_channel)
				proxy.start()
				self.__channel_proxies.append(proxy)

				print 'new connection estabilished. tx:%s rx:%s' % (tx_channel, rx_channel)

			return True

		self.__pubsub_client.subscribe({
			'channel': self.__channel,
			'callback': channel_message_received
		})

