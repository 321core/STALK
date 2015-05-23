# -*- coding: utf-8 -*-
# apiclient.py

import time
import thread
import threading
import traceback

import requests

import conf

TIMEOUT = 10


class APIClient(object):
	def __init__(self):
		super(APIClient, self).__init__()
		self.__running = False
		self.__queue = []
		self.__lock = threading.Lock()

	@property
	def is_running(self):
		return self.__running

	def start(self):
		assert not self.__running
		thread.start_new_thread(self.thread_main, tuple()).setDaemon(True)
		self.__running = True

	def report_status(self, is_running, num_channels, cpu_rate, memory_rate):
		assert isinstance(is_running, bool)
		assert isinstance(num_channels, int) and 0 <= num_channels
		assert isinstance(cpu_rate, (int, float)) and 0 <= cpu_rate <= 1
		assert isinstance(memory_rate, (int, float)) and 0 <= memory_rate <= 1

		params = {
			'base_url': conf.BASE_URL,
		    'is_running': is_running,
		    'num_channels': num_channels,
		    'cpu_rate': cpu_rate,
		    'memory_rate': memory_rate,
		    'time': time.time()
		}

		with self.__lock:
			self.__queue.append(params)

	def thread_main(self):
		while True:
			with self.__lock:
				params = self.__queue
				self.__queue = []

			if params:
				for param in params:
					url = 'http://%s/report_channel_server_status/%s/' % (conf.INDEX_SERVER_BASE_URL, conf.NAME)
					try:
						ret = requests.get(url, params=param, timeout=TIMEOUT)
						return ret.ok and ret.json()['code'] == 'ok'
					except Exception:
						traceback.print_exc()
						return False

			else:
				time.sleep(0.1)
