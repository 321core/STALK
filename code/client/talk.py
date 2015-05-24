#! /usr/bin/python
# -*- coding: utf-8 -*-
# talk.py

import optparse
import time

from clientproxy import ClientProxy
from serverproxy import ServerProxy


def main():
	parse = optparse.OptionParser()
	parse.add_option('--file', dest='file', type=str)
	(options, args) = parse.parse_args()

	cmd = args[0]

	if cmd == 'client':
		sensor_name = args[1]
		port = int(args[2])
		ServerProxy(sensor_name, port).run_main_loop()

	elif cmd == 'server':
		sensor_name = args[1]
		if options.file:
			server_name, port = open(options.file, 'r').read().split()
			port = int(port)

		else:
			server_name = args[2]
			port = int(args[3])

		ClientProxy(sensor_name, (server_name, port)).run_main_loop()

	else:
		print 'unknown command:%s' % cmd


if __name__ == '__main__':
	main()

	while True:
		time.sleep(0.1)
