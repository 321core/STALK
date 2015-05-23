# -*- coding: utf-8 -*-
# views.py

import json
import datetime
import uuid

from django.http import HttpResponse

import models


def get_available_channel_server():
	min_memusage = None
	min_server = None

	for server in models.ChannelServer.objects.all():
		if min_server is None or server.memory_rate < min_memusage:
			min_server = server
			min_memusage = server.memory_rate

	return min_server


def listen(req, user_name, sensor_name):
	try:
		user = models.UserProfile.objects.get(username=user_name)
	except models.UserProfile.DoesNotExist:
		res = {
			'code': 'model_does_not_exists',
		    'message': 'User name "%s" does not exist.' % user_name
		}
		return HttpResponse(json.dumps(res, sort_keys=True, indent=4), content_type='application/json')

	entry, _ = models.Entry.objects.get_or_create(user=user, sensor_name=sensor_name)
	entry.channel = 'l-' + uuid.uuid4()
	entry.channel_server = get_available_channel_server()
	entry.last_listening_time = datetime.datetime.now()
	entry.save()

	res = {
		'code': 'ok',
	    'result': {
		    'channel': entry.channel,
	        'channel-server-address': entry.channel_server.base_url
	    }
	}
	return HttpResponse(json.dumps(res, sort_keys=True, indent=4), content_type="application/json")


def connect(req, user_name, sensor_name):
	try:
		user = models.UserProfile.objects.get(username=user_name)
	except models.UserProfile.DoesNotExist:
		res = {
			'code': 'model_does_not_exists',
		    'message': 'User name "%s" does not exist.' % user_name
		}
		return HttpResponse(json.dumps(res, sort_keys=True, indent=4), content_type='application/json')

	try:
		entry = models.Entry.objects.get(user=user, sensor_name=sensor_name)
	except models.Entry.DoesNotExist:
		res = {
			'code': 'model_does_not_exists',
			'message': 'Sensor name "%s" does not exist.' % sensor_name
		}
		return HttpResponse(json.dumps(res, sort_keys=True, indent=4), content_type="application/json")

	res = {
		'code': 'ok',
		'message': 'Sensor name "%s" redirects to channel "%s"' % (sensor_name, entry.channel),
		'result': {
			'channel': entry.channel,
		    'channel-server-address': entry.channel_server.base_url
		}
	}

	return HttpResponse(json.dumps(res, sort_keys=True, indent=4), content_type="application/json")


def report_channel_server_status(req, server_name):
	base_url = req.REQUEST.get('base_url', None)
	is_running = req.REQUEST.get('is_running', None)
	num_channels = req.REQUEST.get('num_channels', None)
	cpu_rate = req.REQUEST.get('cpu_rate', None)
	memory_rate = req.REQUEST.get('memory_rate', None)

	server, _ = models.ChannelServer.objects.get_or_create(server_name=server_name)
	server.base_url = base_url if base_url is not None else server.base_url
	server.is_running = is_running if is_running is not None else server.is_running
	server.num_channels = num_channels if num_channels is not None else server.num_channels
	server.cpu_rate = cpu_rate if cpu_rate is not None else server.cpu_rate
	server.memory_rate = memory_rate if memory_rate is not None else server.memory_rate
	server.last_reporting_time = datetime.datetime.now()
	server.save()

	res = {
		'code': 'ok'
	}
	return HttpResponse(json.dumps(res, sort_keys=True, indent=4, content_type='application/json'))


def register(req, sensor_name):
	channel = req.GET.get('channel', None)
	if channel is None:
		res = {
			'code': 'invalid_parameters',
			'message': '"channel" is missing.'
		}
		return HttpResponse(json.dumps(res, sort_keys=True, indent=4), content_type="application/json")

	entry = models.Entry.objects.get_or_create(pk=sensor_name)[0]
	entry.channel = channel
	entry.time = datetime.datetime.now()
	entry.save()

	res = {
		'code': 'ok',
		'message': 'Sensor name "%s" redirects to channel "%s"' % (sensor_name, channel)
	}
	return HttpResponse(json.dumps(res, sort_keys=True, indent=4), content_type="application/json")


def query(req, sensor_name):
	try:
		entry = models.Entry.objects.get(pk=sensor_name)
	except models.Entry.DoesNotExist:
		res = {
			'code': 'model_does_not_exists',
			'message': 'Sensor name "%s" does not exist.' % sensor_name
		}
		return HttpResponse(json.dumps(res, sort_keys=True, indent=4), content_type="application/json")

	res = {
		'code': 'ok',
		'message': 'Sensor name "%s" redirects to channel "%s"' % (sensor_name, entry.channel),
		'result': {
			'channel': entry.channel
		}
	}

	return HttpResponse(json.dumps(res, sort_keys=True, indent=4), content_type="application/json")
