#!/usr/bin/python
# -*- coding: utf-8 -*-
# channelserver.py


import time
import struct
import json
import base64

from twisted.web import server
from twisted.web.server import Site
from twisted.web.resource import Resource, NoResource
from twisted.internet import task
from twisted.application import internet, service
from twisted.python import log
import psutil

import conf
import apiclient


class RequestExtraInfo(object):
	def __init__(self):
		super(RequestExtraInfo, self).__init__()
		self.__action = None
		self.__time_token = None

	@property
	def action(self):
		return self.__action

	@action.setter
	def action(self, value):
		assert isinstance(value, str)
		assert value
		self.__action = value

	@property
	def time_token(self):
		return self.__time_token

	@time_token.setter
	def time_token(self, value):
		assert isinstance(value, (float, int, long))
		self.__time_token = value


class Channel(Resource):
	isLeaf = True

	def __init__(self, channel_name):
		assert isinstance(channel_name, str)
		assert channel_name

		Resource.__init__(self)

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
	def create_response_as_octetstream(success, time_token=None, messages=None):
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
					assert isinstance(data, str)
					res += struct.pack('>I', len(data)) + data

		else:
			res = struct.pack('>B', 0)

		return res

	@staticmethod
	def create_response_as_json(success, time_token=None, messages=None):
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

		return json.dumps(res)

	def render(self, request):
		request.extra_info = RequestExtraInfo()

		try:
			action = request.postpath[0]
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

	def send(self, request):
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

	def recv(self, request):
		request.responseHeaders.addRawHeader("Content-Type", "application/octet-stream")
		self.__last_access_time = time.time()

		try:
			time_token = float(request.args['timetoken'][0])
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

	def publish(self, request):
		request.responseHeaders.addRawHeader("Content-Type", "application/json")
		self.__last_access_time = time.time()

		try:
			messages = request.args['message']
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

	def subscribe(self, request):
		request.responseHeaders.addRawHeader("Content-Type", "application/json")
		self.__last_access_time = time.time()

		try:
			time_token = float(request.args['timetoken'][0])
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

	def update_last_time_token(self):
		res = float(str(time.time() * 1000))
		if self.__last_time_token is not None:
			if res <= self.__last_time_token:
				res = self.__last_time_token + 0.1

		self.__last_time_token = res
		return res

	def try_convert_message_to_binary_format(self, message):
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

	def try_restore_message_from_binary_format(self, message):
		isinstance(message, str)
		try:
			if message[0] == '(' and message[-1] == ')':
				idx = message.find(',')
				if idx >= 0:
					command, payload = message[1:idx], message[idx+1:-1]
					payload = base64.b64encode(payload)
					return json.dumps({'command': command, 'payload': payload})
				else:
					command = message[1:-1]
					return json.dumps({'command':command})

		except:
			log.msg(exc=True)

		return message


class Server(Resource):
	isLeaf = False

	def __init__(self):
		Resource.__init__(self)

		self.__channels = {}
		self.__apiclient = apiclient.APIClient()

		task.LoopingCall(self.collect_garbages).start(60.0, False)
		task.LoopingCall(self.report_to_index_server).start(3.0, False)

	def getChild(self, name, request):
		if name:  # 채널에 대한 요청이라면
			try:
				return self.__channels[name]

			except KeyError:
				self.__channels[name] = Channel(name)
				return self.__channels[name]

		return NoResource(message='invalid operation')

	def collect_garbages(self):
		cur_time = time.time()
		tmp = []
		for channel in self.__channels.values():
			channel.remove_old_messages()
			if channel.last_access_time + 60 * 5 < cur_time:
				tmp.append(channel.name)

		for channelName in tmp:
			del self.__channels[channelName]

	def get_channels(self):
		return self.__channels.values()

	def get_channel_names(self):
		return self.__channels.keys()

	def report_to_index_server(self):
		if not self.__apiclient.is_running:  # i don't know why, but  call 'start' here (not __init__)
			self.__apiclient.start()

		cpu_rate = psutil.cpu_percent() / 100.0
		memory_rate = psutil.phymem_usage().percent / 100.0
		self.__apiclient.report_status(True, len(self.__channels), cpu_rate, memory_rate)


# twistd -y ./channelserver.py
application = service.Application('web')
internet.TCPServer(conf.PORT, Site(Server())).setServiceParent(service.IServiceCollection(application))

