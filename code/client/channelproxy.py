# -*- coding: utf-8 -*-
# channelproxy.py

import thread
import socket
import base64
import threading
import time

from pubsubclient import PubSubClient


class ChannelProxy(object):
	def __init__(self, sock, rx_channel, tx_channel):
		assert isinstance(sock, socket.socket)
		assert isinstance(rx_channel, (str, unicode))
		assert isinstance(tx_channel, (str, unicode))

		super(ChannelProxy, self).__init__()

		self.__socket = sock
		self.__rx_channel = rx_channel
		self.__tx_channel = tx_channel
		self.__pubsubclient = PubSubClient()
		self.__running = False
		self.__socket_receiving_thread = None
		self.__channel_receiving_thread = None
		self.__lock = threading.Lock()

	def start(self):
		assert not self.__running

		self.__running = True
		self.__socket_receiving_thread = thread.start_new_thread(self._socket_receiver_thread_main, tuple())
		self.__channel_receiving_thread = thread.start_new_thread(self._channel_receiver_thread_main, tuple())

	def stop(self):
		self.__running = False

		self.__socket_receiving_thread.join()
		self.__socket_receiving_thread = None

		self.__channel_receiving_thread.join()
		self.__channel_receiving_thread = None

	def _socket_receiver_thread_main(self, *args):
		time.sleep(10.0)  ## for debug

		while self.__running:
			try:
				raw = self.__socket.recv(1024 * 100)
			except socket.error:
				raw = ''

			with self.__lock:
				if len(raw):
					payload = base64.b64encode(raw)
					self.__pubsubclient.publish({
						'channel': self.__tx_channel,
						'message': {
							'command': 'send',
							'payload': payload
						}
					})

					# print 'sending to pubsub:' + payload

				else:
					self.__pubsubclient.publish({
						'channel': self.__tx_channel,
						'message': {
							'command': 'close'
						}
					})
					self.__socket.close()
					self.__socket = None
					self.__running = False
					self.__pubsubclient.publish({
						'channel': self.__rx_channel,
						'message': {
						    'command': 'quit'
						}
					})

		print 'socket receiver thread exits.'

	def _channel_receiver_thread_main(self, *args):
		def callback(message):
			with self.__lock:
				cmd = message['command']
				if cmd == 'send':
					payload = message['payload']
					raw = base64.b64decode(payload)
					self.__socket.sendall(raw)

					# print 'sending to socket:' + payload  #
					return True

				elif cmd == 'close':
					self.__socket.close()
					self.__socket = None
					self.__running = False
					return False

				elif cmd == 'quit':
					return False

				return True

		self.__pubsubclient.subscribe({
			'channel': self.__rx_channel,
			'callback': callback
		})

		print 'channel receiver thread exits.'

	@property
	def running(self):
		return self.__running
