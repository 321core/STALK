# -*- coding: utf-8 -*-
# serverproxy.py

import socket
import uuid
import json
import traceback
import time
import threading

import conf
from channelproxy import ChannelProxy
from pubsubsocket import PubSubSocket
import apiclient


class ServerProxy(object):
    def __init__(self, id, sensor_name, port=None):
        assert isinstance(id, int)
        assert port is None or isinstance(port, int)
        assert isinstance(sensor_name, str)

        super(ServerProxy, self).__init__()

        self.__id = id
        self.__sensor_name = sensor_name
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        if port is None:
            self.__socket.bind(('0.0.0.0', 0))
            self.__port = self.__socket.getsockname()[1]

        else:
            self.__port = port
            self.__socket.bind(('0.0.0.0', self.__port))

        self.__running = False
        self.__proxies = []
        self.__thread = None

    @property
    def id(self):
        return self.__id

    @property
    def sensor_name(self):
        return self.__sensor_name

    @property
    def port(self):
        return self.__port

    def start(self):
        assert not self.__thread
        self.__thread = threading.Thread(target=self.run_main_loop)
        self.__thread.start()

    def stop(self):
        assert self.__thread
        self.__running = False
        self.__thread.join()
        self.__thread = None

    def run_main_loop(self):  # TODO: check channel proxies health, if not synchronized too long, should kill it.
        assert not self.__running

        self.__running = True

        try:
            while self.__running:
                self.__socket.listen(5)
                s, addr = self.__socket.accept()

                try:
                    ret = apiclient.connect(conf.USER_NAME, conf.PASSWORD, self.__sensor_name)
                except Exception:
                    traceback.print_exc()
                    time.sleep(3.0)
                    continue

                if ret:
                    channel_server_address, channel, transfer_channel_server_address = ret
                    rx_channel = 'rx-' + str(uuid.uuid4())
                    tx_channel = 'tx-' + str(uuid.uuid4())

                    proxy = ChannelProxy(s, rx_channel, tx_channel, transfer_channel_server_address)
                    proxy.start()
                    self.__proxies.append(proxy)

                    s = PubSubSocket(channel_server_address)
                    s.send(channel, 'connect',
                           json.dumps({'tx_channel': rx_channel,
                                       'rx_channel': tx_channel,
                                       'channel_server_address': transfer_channel_server_address}))

                else:
                    s.close()

        finally:
            print 'stopping channel proxies...'
            for p in self.__proxies:
                if p.running:
                    p.stop()

            self.__proxies = []

    def stop(self):
        self.__running = False
        self.__socket.close()
        self.__socket = None
