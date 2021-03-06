import json
import socket
import threading
import time
import traceback
from threading import Thread
from typing import Tuple, Optional

from . import apiclient
from . import conf
from .channelproxy import ChannelProxy
from .pubsubsocket import PubSubSocket


class ClientProxy(object):
    def __init__(self, proxy_id: int, sensor_name: str, server_address: Tuple[str, int]):
        assert isinstance(proxy_id, int)
        assert isinstance(server_address, (tuple, list))
        assert len(server_address) == 2
        assert isinstance(server_address[0], str)
        assert isinstance(server_address[1], int)
        assert isinstance(sensor_name, str)

        super().__init__()

        self.__id = proxy_id
        self.__server_address: Tuple[str, int] = tuple(server_address)
        self.__receive_thread: Optional[Thread] = None
        self.__sensor_name = sensor_name
        self.__running = False
        self.__channel_proxies = []
        self.__lock = threading.Lock()
        self.__thread: Optional[Thread] = None
        self.__ps_socket: Optional[PubSubSocket] = None
        self.__main_thread: Optional[Thread] = None

    @property
    def id(self):
        return self.__id

    @property
    def sensor_name(self):
        return self.__sensor_name

    @property
    def server_address(self):
        return self.__server_address

    def start(self):
        assert not self.__main_thread
        self.__main_thread = threading.Thread(target=self.run_main_loop)
        self.__main_thread.start()

    def stop(self):
        assert self.__main_thread
        self.__running = False
        self.__main_thread.join()
        self.__main_thread = None

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

                    # check channel continuously
                    while self.__running:
                        try:
                            ret = apiclient.check_listen_channel(conf.USER_NAME, conf.PASSWORD, self.__sensor_name, channel)

                        except Exception:
                            traceback.print_exc()
                            continue

                        if ret:
                            for i in range(10):
                                time.sleep(1.0)
                                if not self.__running:
                                    break

                        else:
                            with self.__lock:
                                self.__ps_socket.request_stop_receiving()
                                self.__ps_socket.send(channel, 'quit')
                                self.__thread.join()
                                self.__ps_socket = None
                                self.__thread = None

                            break

                else:
                    time.sleep(3.0)

        except Exception:
            traceback.print_exc()

        finally:
            with self.__lock:
                if self.__ps_socket and self.__thread:
                    self.__ps_socket.request_stop_receiving()
                    self.__ps_socket.send(channel, 'quit')
                    self.__thread.join()
                    self.__ps_socket = None
                    self.__thread = None

            print('stopping channel proxies...')
            with self.__lock:
                for p in self.__channel_proxies:
                    if p.running:
                        p.stop()

                self.__channel_proxies = []

            print('run_loop terminates.')

    def recv_thread(self, channel_server_address, channel):
        def channel_message_received(command: bytes, payload: bytes):
            if command == b'connect':
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

            elif command == b'quit':
                return False

            return self.__running

        self.__ps_socket = PubSubSocket(channel_server_address)
        self.__ps_socket.recv(channel, channel_message_received)

        print('recv_thread terminates.')
