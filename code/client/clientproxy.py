# -*- coding: utf-8 -*-
# clientproxy.py

import socket
import json
import threading
import time
import traceback

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
		self.__lock = threading.Lock()
		self.__thread = None
		self.__pubsubsocket = None

	def run_main_loop(self):
		assert not self.__running

		self.__running = True

		try:
			while self.__running:
				try:
					ret = apiclient.listen(conf.USER_NAME, conf.PASSWORD, self.__sensor_name)
				except Exception:
					traceback.print_exc()
					time.sleep(3.0)
					continue

				if ret:
					channel_server_address, channel = ret
					self.__thread = threading.Thread(target=self.recv_thread, args=(channel_server_address, channel))
					self.__thread.start()

					# check channel continously
					while True:
						try:
							ret = apiclient.check_listen_channel(conf.USER_NAME, conf.PASSWORD,
							                                     self.__sensor_name, channel)

						except Exception:
							traceback.print_exc()
							continue

						if ret:
							time.sleep(10.0)

						else:
							with self.__lock:
								self.__pubsubsocket.request_stop_receiving()
								self.__pubsubsocket.send(channel, 'quit')
								self.__thread.join()
								self.__pubsubsocket = None
								self.__thread = None

							break

				else:
					time.sleep(3.0)

		except Exception:
			traceback.print_exc()

		finally:
			with self.__lock:
				if self.__pubsubsocket and self.__thread:
					self.__pubsubsocket.request_stop_receiving()
					self.__pubsubsocket.send(channel, 'quit')
					self.__thread.join()
					self.__pubsubsocket = None
					self.__thread = None

			print 'stopping channel proxies...'
			with self.__lock:
				for p in self.__channel_proxies:
					if p.running:
						p.stop()

				self.__channel_proxies = []

			print 'run_loop terminates.'

	def recv_thread(self, channel_server_address, channel):
		def channel_message_received(command, payload):
			if command == 'connect':
				message = json.loads(payload)
				tx_channel = message['tx_channel']
				rx_channel = message['rx_channel']
				new_channel_server_address = message['channel_server_address']

				s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
				s.connect(self.__server_address)

				proxy = ChannelProxy(s, rx_channel, tx_channel, new_channel_server_address)
				proxy.start()

				with self.__lock:
					self.__channel_proxies.append(proxy)

			elif command == 'quit':
				return False

			return self.__running

		self.__pubsubsocket = PubSubSocket(channel_server_address)
		self.__pubsubsocket.recv(channel, channel_message_received)

		print 'recv_thread terminates.'
