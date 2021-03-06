import base64
import json
import os
import platform
import socket
import struct
import sys
import time
from typing import Optional, Union, Sequence

import psutil
from twisted.application import internet, service
from twisted.internet import task
from twisted.python import log
from twisted.web import server
from twisted.web.resource import Resource, NoResource
from twisted.web.server import Site, Request

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import apiclient
import conf


class RequestExtraInfo(object):
    def __init__(self):
        super().__init__()
        self.__action: Optional[str] = None
        self.__time_token: Union[None, float, int] = None

    @property
    def action(self) -> str:
        return self.__action

    @action.setter
    def action(self, value: str):
        assert isinstance(value, str)
        assert value
        self.__action = value

    @property
    def time_token(self) -> Union[None, float, int]:
        return self.__time_token

    @time_token.setter
    def time_token(self, value: Union[float, int]):
        assert isinstance(value, (float, int))
        self.__time_token = value


class Channel(Resource):
    isLeaf = True

    def __init__(self, channel_name: str):
        super().__init__()

        assert isinstance(channel_name, str)

        self.name = channel_name
        self.__last_time_token = None
        self.update_last_time_token()

        self.__messages = []
        self.__delayed_requests = []
        self.__last_access_time = time.time()

    @property
    def last_access_time(self):
        return self.__last_access_time

    @staticmethod
    def create_response_as_octetstream(success: bool, time_token: Optional[float] = None, messages: Optional[Sequence] = None) -> bytes:
        assert isinstance(success, bool)
        assert time_token is None or isinstance(time_token, float)
        assert messages is None or isinstance(messages, (tuple, list))

        if success:
            assert time_token is not None

            if messages is None or len(messages) == 0:
                res = struct.pack('>Bd', 1, time_token)

            else:
                res = struct.pack('>BdI', 1, time_token, len(messages))
                for tt, data in messages:
                    assert isinstance(data, bytes)
                    res += struct.pack('>I', len(data)) + data

        else:
            res = struct.pack('>B', 0)

        return res

    @staticmethod
    def create_response_as_json(success: bool, time_token: Optional[float] = None, messages: Optional[Sequence] = None) -> bytes:
        assert isinstance(success, bool)
        assert time_token is None or isinstance(time_token, float)
        assert messages is None or isinstance(messages, (tuple, list))

        if success:
            assert time_token is not None
            if messages is None:
                res = [True, time_token]

            else:
                res = [True, time_token, messages]

        else:
            res = [False]

        return json.dumps(res).encode()

    def render(self, request: Request) -> bytes:
        request.extra_info = RequestExtraInfo()

        try:
            action: Optional[str] = request.postpath[0].decode()
        except IndexError:
            action = None

        if action:
            request.extra_info.action = action

        if action == 'send':
            return self.send(request)

        elif action == 'recv':
            return self.recv(request)

        elif action == 'publish':
            return self.publish(request)

        elif action == 'subscribe':
            return self.subscribe(request)

        else:
            res = NoResource(message="invalid command to channel.")
            return res.render(request)

    def send(self, request: Request) -> bytes:
        request.responseHeaders.addRawHeader("Content-Type", "application/octet-stream")
        self.__last_access_time = time.time()
        message = request.content.read()

        if message:
            time_token = self.update_last_time_token()
            self.__messages.append((time_token, message))
            self.process_delayed_requests()
            return self.create_response_as_octetstream(True, time_token)

        else:
            return self.create_response_as_octetstream(False)

    def recv(self, request) -> bytes:
        request.responseHeaders.addRawHeader("Content-Type", "application/octet-stream")
        self.__last_access_time = time.time()

        try:
            time_token = float(request.args[b'timetoken'][0])
        except KeyError:
            time_token = 0

        request.extra_info.time_token = time_token

        if time_token == 0:
            return self.create_response_as_octetstream(True, self.__last_time_token)

        messages = self.gather_messages_after(time_token)
        if len(messages) > 0:
            return self.create_response_as_octetstream(True, self.__last_time_token, messages)

        else:
            self.__delayed_requests.append(request)
            return server.NOT_DONE_YET

    def publish(self, request) -> bytes:
        request.responseHeaders.addRawHeader("Content-Type", "application/json")
        self.__last_access_time = time.time()

        try:
            messages = request.args[b'message']
        except KeyError:
            messages = None

        if messages:
            time_token = self.update_last_time_token()
            for message in messages:
                message = self.try_convert_message_to_binary_format(message)
                self.__messages.append((time_token, message))

            self.process_delayed_requests()
            return self.create_response_as_json(True, time_token)

        else:
            return self.create_response_as_json(False)

    def subscribe(self, request) -> bytes:
        request.responseHeaders.addRawHeader("Content-Type", "application/json")
        self.__last_access_time = time.time()

        try:
            time_token = float(request.args[b'timetoken'][0])
        except KeyError:
            time_token = 0

        request.extra_info.time_token = time_token

        if time_token == 0:
            return self.create_response_as_json(True, self.__last_time_token)

        messages = self.gather_messages_after(time_token)
        if len(messages) > 0:
            messages = messages[:]
            for idx in range(len(messages)):
                messages[idx] = self.try_restore_message_from_binary_format(messages[idx])

            return self.create_response_as_json(True, self.__last_time_token, messages)

        else:
            self.__delayed_requests.append(request)
            return server.NOT_DONE_YET

    def process_delayed_requests(self):
        for req in self.__delayed_requests:
            time_token = req.extra_info.time_token
            messages = self.gather_messages_after(time_token)
            assert len(messages)

            if req.extra_info.action == 'recv':
                res = self.create_response_as_octetstream(True, self.__last_time_token, messages)

            elif req.extra_info.action == 'subscribe':
                res = self.create_response_as_json(True, self.__last_time_token, messages)

            else:
                assert False

            try:
                req.write(res)
                req.finish()

            except Exception:  # 커넥션이 사라진 경우임.
                pass

        self.__delayed_requests = []

    def gather_messages_after(self, time_token_):
        messages = []
        for time_token, message in self.__messages:
            if time_token > time_token_:
                messages.append((time_token, message))

        return messages

    def remove_old_messages(self):
        cur_time = time.time()
        tmp = []
        for entry in self.__messages:
            time_token, message = entry
            send_time = time_token / 1000  # 대략적으로 1000 배 이므로.
            if send_time + 60 < cur_time:  # 1 분 이상 된 메시지는 지운다.
                tmp.append(entry)

        for entry in tmp:
            self.__messages.remove(entry)

    def update_last_time_token(self) -> float:
        res = float(str(time.time() * 1000))
        if self.__last_time_token is not None:
            if res <= self.__last_time_token:
                res = self.__last_time_token + 0.1

        self.__last_time_token = res
        return res

    def try_convert_message_to_binary_format(self, message: str):
        isinstance(message, str)
        try:
            obj = json.loads(message)
            command = obj['command']
            if 'payload' in obj:
                payload = base64.b64decode(obj['payload'])
                res = '(' + command + ',' + payload + ')'
            else:
                res = '(' + command + ')'

            return res

        except:
            log.msg(exc=True)
            return message

    def try_restore_message_from_binary_format(self, message: str):
        isinstance(message, str)
        try:
            if message[0] == '(' and message[-1] == ')':
                idx = message.find(',')
                if idx >= 0:
                    command, payload = message[1:idx], message[idx + 1:-1]
                    payload = base64.b64encode(payload)
                    return json.dumps({'command': command, 'payload': payload})
                else:
                    command = message[1:-1]
                    return json.dumps({'command': command})

        except:
            log.msg(exc=True)

        return message


class Status(Resource):
    isLeaf = True

    def __init__(self, server_: 'Server'):
        super().__init__()
        self.__server = server_

    def render(self, request: Request) -> bytes:
        try:
            action: bytes = request.postpath[0]
            action: Optional[str] = action.decode()

        except IndexError:
            action = None

        if action == 'channels':
            return self.channels(request).encode()

        else:
            res = NoResource(message="invalid command to server.")
            return res.render(request)

    def channels(self, request: Request) -> str:
        try:
            prefix: bytes = request.args[b'prefix'][0]
            prefix: Optional[str] = prefix.decode()

        except KeyError:
            prefix = None

        if prefix:
            res = []
            for name in self.__server.get_channel_names():
                if name.startswith(prefix):
                    res.append(name)
        else:
            res = self.__server.get_channel_names()

        return json.dumps(res)


class Server(Resource):
    isLeaf = False

    def __init__(self):
        super().__init__()

        self.__channels = {}
        self.__apiclient = apiclient.APIClient()
        self.__status = Status(self)

        task.LoopingCall(self.collect_garbages).start(60.0, False)
        task.LoopingCall(self.report_to_index_server).start(3.0, False)

    def getChild(self, name: bytes, request: Request) -> Resource:
        #
        sock: socket.socket = request.transport.socket

        if platform.system() == 'Darwin':
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            TCP_KEEPALIVE = 0x10
            sock.setsockopt(socket.IPPROTO_TCP, TCP_KEEPALIVE, 1)

        else:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 3)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)

        #
        if name:
            name: str = name.decode()
            if name == '__status':
                return self.__status

            try:
                return self.__channels[name]

            except KeyError:
                self.__channels[name] = Channel(name)
                return self.__channels[name]

        return NoResource(message='invalid operation')

    def collect_garbages(self) -> None:
        cur_time = time.time()
        tmp = []
        for channel in self.__channels.values():
            channel.remove_old_messages()
            if channel.last_access_time + 60 * 5 < cur_time:
                tmp.append(channel.name)

        for channelName in tmp:
            del self.__channels[channelName]

    def get_channels(self) -> Sequence[Channel]:
        return tuple(self.__channels.values())

    def get_channel_names(self) -> Sequence[str]:
        return tuple(self.__channels.keys())

    def report_to_index_server(self) -> None:
        if not self.__apiclient.is_running:  # i don't know why, but  call 'start' here (not __init__)
            self.__apiclient.start()

        cpu_rate = psutil.cpu_percent() / 100.0
        memory_rate = psutil.virtual_memory().percent / 100.0
        self.__apiclient.report_status(True, len(self.__channels), cpu_rate, memory_rate)


class MySite(Site):
    def __init__(self):
        super().__init__(Server(), timeout=60)


application = service.Application('web')
internet.TCPServer(conf.PORT, MySite()).setServiceParent(service.IServiceCollection(application))
