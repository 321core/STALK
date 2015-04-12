# -*- coding: utf-8 -*-
# serverproxy.py

import socket
import thread
import threading
import base64
from pubsubclient import PubSubClient


class ClientChannel(object):
	def __init__(self, sock, addr, txchannel, rxchannel):
		assert isinstance(sock, socket.socket)
		assert isinstance(addr, (tuple, list))
		assert len(addr) == 2
		assert isinstance(txchannel, str)
		assert isinstance(rxchannel, str)

		super(ClientChannel, self).__init__()

		self.__socket = sock
		self.__client_address = addr
		self.__tx_channel = txchannel
		self.__rx_channel = rxchannel
		self.__pubsubclient = PubSubClient()

	def start(self):
		thread.start_new_thread(self.thread_main, tuple())

		while True:
			data = self.__socket.recv(1024)
			if len(data):
				payload = base64.b64encode(data)
				self.__pubsubclient.publish({
					'channel': self.__tx_channel,
					'message': {
						'command': 'send',
						'payload': payload
					}
				})
			else:
				self.__pubsubclient.publish({
					'channel': self.__tx_channel,
					'message': {
						'command': 'close'
					}
				})
				self.__client_socket.close()
				self.__client_socket = None
				break

	def thread_main(self):
		self.__pubsubclient.subscribe({
			'channel': self.__rx_channel,
		    'callback': self.channel_message_received
		})

	def channel_message_received(self, message):
		event = message['event']

		if event == 'received':
			payload = message['payload']
			raw = base64.b64decode(payload)
			self.__client_socket.sendall(raw)

		elif event == 'closed':
			self.__client_socket.close()

		return True






class ServerProxy(object):  # port 를 리슨하며, 수신되는 데이터를 모두 channel 로 redirecting
	def __init__(self, port, tx_channel, rx_channel):
		assert isinstance(port, int)
		assert isinstance(tx_channel, str)
		assert isinstance(rx_channel, str)

		super(ServerProxy, self).__init__()

		self.__port = port
		self.__tx_channel = tx_channel
		self.__rx_channel = rx_channel
		self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
		self.__socket.bind(('', self.__port))
		self.__pubsubclient = PubSubClient()
		self.__client_socket = None
		self.__client_address = None

	def start(self):
		while True:
			self.__socket.listen(1)
			s, addr = self.__socket.accept()
			self.__client_socket = s
			self.__client_address = addr

			thread.start_new_thread(self.thread_main, tuple())

			self.__pubsubclient.publish({
				'channel': self.__tx_channel,
			    'message': {
				    'command': 'connect'
			    }
			})

			while True:
				data = s.recv(1024)
				if len(data):
					payload = base64.b64encode(data)
					self.__pubsubclient.publish({
						'channel': self.__tx_channel,
					    'message': {
						    'command': 'send',
					        'payload': payload
					    }
					})
				else:
					self.__pubsubclient.publish({
						'channel': self.__tx_channel,
					    'message': {
						    'command': 'close'
					    }
					})
					self.__client_socket.close()
					self.__client_socket = None
					break


	def thread_main(self):
		self.__pubsubclient.subscribe({
			'channel': self.__rx_channel,
		    'callback': self.channel_message_received
		})

	def channel_message_received(self, message):
		event = message['event']

		if event == 'received':
			payload = message['payload']
			raw = base64.b64decode(payload)
			self.__client_socket.sendall(raw)

		elif event == 'closed':
			self.__client_socket.close()

		return True


if __name__ == '__main__':
	proxy = ServerProxy(9300, 'tx-raspi', 'rx-raspi')
	proxy.start()
