#! /usr/bin/python
# -*- coding: utf-8 -*-
# talk.py

import optparse
import time

from clientproxy import ClientProxy
from serverproxy import ServerProxy


class Application(object):
	def __init__(self):
		super(Application, self).__init__()
		self.__server_proxies = []
		self.__client_proxies = []

	def add_server_proxy(self, sensor_name, port):
		proxy = ServerProxy(sensor_name, port)
		proxy.start()
		self.__server_proxies.append(proxy)

	def add_client_proxy(self, sensor_name, server_address):
		proxy = ClientProxy(sensor_name, server_address)
		proxy.start()
		self.__client_proxies.append(proxy)


def main():
	app = Application()

	parse = optparse.OptionParser()
	parse.add_option('--file', dest='file', type=str)
	(options, args) = parse.parse_args()

	cmd = args[0]

	if cmd == 'client':
		sensor_name = args[1]
		port = int(args[2])
		app.add_server_proxy(sensor_name, port)

	elif cmd == 'server':
		sensor_name = args[1]
		if options.file:
			server_name, port = open(options.file, 'r').read().split()
			port = int(port)

		else:
			server_name = args[2]
			port = int(args[3])

		app.add_client_proxy(sensor_name, (server_name, port))

	else:
		print 'unknown command:%s' % cmd


if __name__ == '__main__':
	main()

	while True:
		time.sleep(0.1)
