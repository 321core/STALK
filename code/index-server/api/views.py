# -*- coding: utf-8 -*-
# views.py

import json
import time
import datetime
import uuid

from django.http import HttpResponse
from django.contrib.auth.models import User
from django.utils import timezone
import models
import error


def get_available_channel_server():
	min_memusage = None
	min_server = None

	threshold = timezone.now() - datetime.timedelta(seconds=60)

	print threshold

	for server in models.ChannelServer.objects.all():
		print server.last_reporting_time
		if server.is_visible and server.is_running and server.last_reporting_time > threshold:
			if min_server is None or server.memory_rate < min_memusage:
				min_server = server
				min_memusage = server.memory_rate

	return min_server


def listen(req, user_name, sensor_name):
	try:
		user = User.objects.get(username=user_name)
	except User.DoesNotExist:
		res = {
			'code': error.CODE_NO_USER,
		    'message': 'User name "%s" does not exist.' % user_name
		}
		return HttpResponse(json.dumps(res, sort_keys=True, indent=4), content_type='application/json')

	channelserver = get_available_channel_server()

	if channelserver:
		entry, _ = models.Entry.objects.get_or_create(user=user, sensor_name=sensor_name)
		entry.channel = 'l-' + str(uuid.uuid4())
		entry.channel_server = get_available_channel_server()
		entry.last_listening_time = datetime.datetime.now()
		entry.save()

		res = {
			'code': error.CODE_OK,
		    'result': {
			    'channel': entry.channel,
		        'channel-server-address': entry.channel_server.base_url
		    }
		}

	else:
		res = {
			'code': error.CODE_NO_SERVER,
		    'message': 'there are no available channel server.'
		}

	return HttpResponse(json.dumps(res, sort_keys=True, indent=4), content_type="application/json")


def connect(req, user_name, sensor_name):
	try:
		user = User.objects.get(username=user_name)
	except User.DoesNotExist:
		res = {
			'code': error.CODE_NO_USER,
		    'message': 'User name "%s" does not exist.' % user_name
		}
		return HttpResponse(json.dumps(res, sort_keys=True, indent=4), content_type='application/json')

	try:
		entry = models.Entry.objects.get(user=user, sensor_name=sensor_name)
	except models.Entry.DoesNotExist:
		res = {
			'code': error.CODE_NO_SENSOR,
			'message': 'Sensor name "%s" does not exist.' % sensor_name
		}
		return HttpResponse(json.dumps(res, sort_keys=True, indent=4), content_type="application/json")

	res = {
		'code': error.CODE_OK,
		'result': {
			'channel': entry.channel,
		    'channel-server-address': entry.channel_server.base_url
		}
	}

	return HttpResponse(json.dumps(res, sort_keys=True, indent=4), content_type="application/json")


def report_channel_server_status(req, server_name):
	base_url = req.GET.get('base_url', None)
	is_running = req.GET.get('is_running', None)
	num_channels = req.GET.get('num_channels', None)
	cpu_rate = req.GET.get('cpu_rate', None)
	memory_rate = req.GET.get('memory_rate', None)
	timestamp = req.GET.get('timestamp', None)
	if timestamp is not None:
		timestamp = float(timestamp)
	else:
		timestamp = time.time()

	server, _ = models.ChannelServer.objects.get_or_create(server_name=server_name)
	server.base_url = base_url if base_url is not None else server.base_url
	server.is_running = is_running if is_running is not None else server.is_running
	server.num_channels = num_channels if num_channels is not None else server.num_channels
	server.cpu_rate = cpu_rate if cpu_rate is not None else server.cpu_rate
	server.memory_rate = memory_rate if memory_rate is not None else server.memory_rate
	server.last_reporting_time = datetime.datetime.fromtimestamp(timestamp).replace(tzinfo=timezone.get_current_timezone())
	server.save()

	res = {
		'code': error.CODE_OK
	}
	return HttpResponse(json.dumps(res, sort_keys=True, indent=4), content_type='application/json')
