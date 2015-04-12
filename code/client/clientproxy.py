# -*- coding: utf-8 -*-
# clientproxy.py

import base64
import socket
import thread
import threading
import sys
from pubsubclient import PubSubClient


class ClientProxy(object):  # tx_channel 을 subscribe 하며, tx_channel 로 수신되는 모든 데이터를 serveraddr 로 커넥팅.
	def __init__(self, server_address, tx_channel, rx_channel):
		assert isinstance(server_address, (tuple, list))
		assert len(server_address) == 2
		assert isinstance(server_address[0], str)
		assert isinstance(server_address[1], int)
		assert isinstance(tx_channel, str)
		assert isinstance(rx_channel, str)

		super(ClientProxy, self).__init__()

		self.__server_address = tuple(server_address)
		self.__tx_channel = tx_channel
		self.__rx_channel = rx_channel
		self.__pubsub_client = PubSubClient()
		self.__receive_thread = None
		self.__lock = threading.Lock()
		self.__socket = None

	def start(self):
		self.__pubsub_client.subscribe({
			'channel': self.__tx_channel,
			'callback': self.channel_message_received
		})

	def channel_message_received(self, message):
		assert isinstance(message, dict)
		assert 'command' in message

		cmd = message['command']
		assert cmd in ('connect', 'close', 'send')

		if cmd == 'connect':
			self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
			self.__socket.connect(self.__server_address)
			self.__receive_thread = thread.start_new_thread(self.receive_thread_main, tuple())

		elif cmd == 'close':
			if self.__socket:
				self.__socket.close()
				self.__socket = None

		elif cmd == 'send':
			if self.__socket:
				assert 'payload' in message
				payload = message['payload']
				assert isinstance(payload, (str, unicode))
				raw = base64.b64decode(payload)
				self.__socket.sendall(raw)

		else:
			assert False

		return True

	def receive_thread_main(self):
		while True:
			data = self.__socket.recv(1024)
			with self.__lock:
				if len(data):
					payload = base64.b64encode(data)
					self.__pubsub_client.publish({
						'channel': self.__rx_channel,
						'message': {
							'event': 'received',
						    'payload': payload
						}
					})

				else:
					self.__pubsub_client.publish({
						'channel': self.__rx_channel,
						'message': {
							'event': 'closed'
						}
					})


if __name__ == '__main__':
	proxy = ClientProxy(('127.0.0.1', 22), 'tx-raspi', 'rx-raspi')
	proxy.start()
