# -*- coding: utf-8 -*-
# views.py

import json
from django.http import HttpResponse
import models


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
