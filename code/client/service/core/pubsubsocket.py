# -*- coding: utf-8 -*-
# pubsubsocket.py

import time
import socket
import struct
import traceback
import requests


class PubSubSocket(object):
    def __init__(self, channel_server_address):
        assert isinstance(channel_server_address, (str, unicode))
        super(PubSubSocket, self).__init__()
        self.__channel_server_address = channel_server_address
        self.__request_stop_receiving = False
        self.__session = requests.Session()

    def request_stop_receiving(self):
        self.__request_stop_receiving = True

    @staticmethod
    def parse_binary_response(data):
        assert isinstance(data, str)

        if len(data) == 0:
            return struct.unpack('>B', data)

        elif len(data) == 9:
            success, time_token = struct.unpack('>Bd', data)
            return success, time_token

        elif len(data) >= 13:
            success, time_token, num = struct.unpack('>BdI', data[:13])
            offset = 13
            messages = []
            for idx in range(num):
                sz, = struct.unpack('>I', data[offset:offset + 4])
                assert sz > 0
                offset += 4

                m = data[offset:offset + sz]
                messages.append(m)
                offset += sz

            return success, time_token, messages

        else:
            assert False

    def send(self, channel, command, payload=None):
        assert isinstance(channel, (str, unicode))
        assert isinstance(command, (str, unicode))
        assert payload is None or isinstance(payload, str)

        if payload:
            data = '(' + command + ',' + payload + ')'
        else:
            data = '(' + command + ')'

        ret = self.do_request(channel, 'send', data=data)
        if ret:
            return self.parse_binary_response(ret)

        return [0, "Not Sent", "0"]

    def recv(self, channel, callback, time_token=0):
        assert isinstance(channel, (str, unicode))
        assert isinstance(time_token, (float, int, long))

        not_subscribed = True if time_token == 0 else False

        while not self.__request_stop_receiving:
            try:
                ret = self.do_request(channel, 'recv', params={'timetoken': "%f" % time_token})
                if ret is None:
                    continue

                ret = self.parse_binary_response(ret)
                success = ret[0]
                time_token = ret[1]

                if len(ret) >= 3:
                    messages = ret[2]
                else:
                    messages = []

                if success and not_subscribed:
                    not_subscribed = False
                    callback(None, None)

                if not len(messages):
                    continue

                for m in messages:
                    assert m[0] == '('
                    assert m[-1] == ')'
                    idx = m.find(',')
                    if idx >= 0:
                        command, payload = m[1:idx], m[idx + 1:-1]
                    else:
                        command = m[1:-1]
                        payload = None

                    if not callback(command, payload):
                        return True

            except Exception:
                traceback.print_exc()
                time.sleep(1)

        return True

    def do_request(self, channel, action, params=None, data=None):
        assert isinstance(channel, (str, unicode))
        assert isinstance(action, (str, unicode))
        assert params is None or isinstance(params, dict)
        assert data is None or isinstance(data, str)

        url = 'http://%s/%s/%s' % (self.__channel_server_address, channel, action)

        try:
            if data is not None:
                ret = self.do_request_post(url, params=params, data=data,
                                           headers={'Content-Type': 'application/octet-stream'}, timeout=60)
                return ret

            else:
                ret = self.do_request_get(url, params=params, timeout=60)
                return ret

        except socket.timeout:
            return None

        except Exception:
            traceback.print_exc()
            return None

    def do_request_get(self, url, params=None, headers={}, timeout=10):
        try:
            ret = self.__session.get(url, params=params, headers=headers, timeout=timeout)
            if ret.ok:
                return ret.content

        except Exception:
            traceback.print_exc()

    def do_request_post(self, url, params=None, data=None, headers={}, timeout=10):
        try:
            ret = self.__session.post(url, params=params, headers=headers, timeout=timeout, data=data)
            if ret.ok:
                return ret.content

        except Exception:
            traceback.print_exc()
