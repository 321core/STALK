# /usr/bin/python
# -*- coding: utf-8 -*-
# app.py

import optparse

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
	parse.add_option('--port', dest='port', type='int')
	parse.add_option('--server', dest='server')

	(options, args) = parse.parse_args()

	cmd = args[0]

	if cmd == 'bind':
		sensor_name = args[1]
		app.add_server_proxy(sensor_name, options.port)

	elif cmd == 'proxy':
		sensor_name = args[1]
		app.add_client_proxy(sensor_name, (options.server, options.port))

	else:
		print 'unknown command:%s' % cmd


if __name__ == '__main__':
	main()

	cmd = raw_input('>')