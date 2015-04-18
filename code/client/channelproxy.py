# -*- coding: utf-8 -*-
# channelproxy.py

import thread
import socket
import base64
import threading
import time
import traceback

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
		self.__subscribed = False
		self.__other_ready = False

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
		while not self.__other_ready:
			time.sleep(0.5)

		while self.__running:
			try:
				raw = self.__socket.recv(1024 * 1024) # 1MB
			except socket.error:
				traceback.print_exc()
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
					if self.__socket:
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
		def ttcallback():
			print 'im subscribed channel.'
			if not self.__subscribed:
				self.__subscribed = True
				self.__pubsubclient.publish({
					'channel': self.__tx_channel,
					'message': {
						'command': 'imready'
					}
				})

				print ' and send message.'

		def callback(message):
			with self.__lock:
				cmd = message['command']
				if cmd == 'send':
					payload = message['payload']
					# print 'received from channel:"' + payload +'"'  #

					raw = base64.b64decode(payload)
					self.__socket.sendall(raw)

					# print 'sending to socket:' + payload  #
					return True

				elif cmd == 'close':
					print 'close socket...'
					if self.__socket:
						self.__socket.shutdown(socket.SHUT_RDWR)
						self.__socket = None

					self.__running = False
					return False

				elif cmd == 'quit':
					return False

				elif cmd == 'imready':
					if not self.__other_ready:
						print 'other side has subscirbed channel.'
						self.__other_ready = True

						# send again
						if self.__subscribed:
							self.__pubsubclient.publish({
								'channel': self.__tx_channel,
								'message': {
									'command': 'imready'
								}
							})

							print ' send imready message again.'



				return True

		self.__pubsubclient.subscribe({
			'channel': self.__rx_channel,
			'callback': callback,
		    'ttcallback': ttcallback
		})

		print 'channel receiver thread exits.'

	@property
	def running(self):
		return self.__running
