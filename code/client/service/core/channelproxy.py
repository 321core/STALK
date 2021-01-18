import socket
import threading
import time
import traceback
from threading import Thread
from typing import Optional

from .pubsubsocket import PubSubSocket


class ChannelProxy:
    def __init__(self, sock: socket.socket, rx_channel: str, tx_channel: str, channel_server_address: str):
        assert isinstance(sock, socket.socket)
        assert isinstance(rx_channel, str)
        assert isinstance(tx_channel, str)
        assert isinstance(channel_server_address, str)

        super().__init__()

        self.__socket = sock
        self.__rx_channel = rx_channel
        self.__tx_channel = tx_channel
        self.__ps_socket = PubSubSocket(channel_server_address)
        self.__running = False
        self.__socket_receiving_thread: Optional[Thread] = None
        self.__channel_receiving_thread: Optional[Thread] = None
        self.__lock = threading.Lock()
        self.__subscribed = False
        self.__other_ready = False
        self.__start_time: Optional[float] = None

    def start(self):
        assert not self.__running

        self.__running = True
        self.__start_time = time.time()

        self.__socket_receiving_thread = threading.Thread(target=self._socket_receiver_thread_main)
        self.__socket_receiving_thread.setDaemon(True)
        self.__socket_receiving_thread.start()

        self.__channel_receiving_thread = threading.Thread(target=self._channel_receiver_thread_main)
        self.__channel_receiving_thread.setDaemon(True)
        self.__channel_receiving_thread.start()

    def stop(self):
        if self.__running:
            self.__running = False

            with self.__lock:
                if self.__socket:
                    self.__socket.shutdown(socket.SHUT_RDWR)
                    self.__socket = None

                self.__ps_socket.send(self.__rx_channel, 'quit')

            self.__socket_receiving_thread.join()
            self.__socket_receiving_thread = None

            self.__channel_receiving_thread.join()
            self.__channel_receiving_thread = None

    def _socket_receiver_thread_main(self):
        while not self.__other_ready:
            time.sleep(0.01)

        while self.__running:
            try:
                raw = self.__socket.recv(1024 * 1024)  # 1MB
            except socket.error:
                traceback.print_exc()
                raw = ''

            with self.__lock:
                if len(raw):
                    self.__ps_socket.send(self.__tx_channel, 'send', raw)

                else:
                    self.__ps_socket.send(self.__tx_channel, 'close')
                    if self.__socket:
                        self.__socket.close()
                        self.__socket = None

                    self.__running = False
                    self.__ps_socket.send(self.__rx_channel, 'quit')
                    break

        print('socket receiver thread exits.')

    def _channel_receiver_thread_main(self):
        def callback(command, payload):
            if command is None and payload is None:
                print('im subscribed channel.')
                if not self.__subscribed:
                    self.__subscribed = True
                    self.__ps_socket.send(self.__tx_channel, 'imready')
                    print(' and send message.')

                return True

            else:
                assert isinstance(command, bytes)
                with self.__lock:
                    if command == b'send':
                        if self.__socket:
                            self.__socket.sendall(payload)

                        return True

                    elif command == b'close':
                        print('close socket...')
                        if self.__socket:
                            self.__socket.shutdown(socket.SHUT_RDWR)
                            self.__socket = None

                        self.__running = False
                        return False

                    elif command == b'quit':
                        return False

                    elif command == b'imready':
                        if not self.__other_ready:
                            print('other side has subscirbed channel.')
                            self.__other_ready = True

                            # send again
                            if self.__subscribed:
                                self.__ps_socket.send(self.__tx_channel, 'imready')
                                print(' send imready message again.')

                    return True

        self.__ps_socket.recv(self.__rx_channel, callback)
        print('channel receiver thread exits.')

    @property
    def running(self):
        return self.__running

    @property
    def has_hand_shake_done(self):
        return self.__subscribed and self.__other_ready
