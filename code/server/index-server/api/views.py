# -*- coding: utf-8 -*-
# views.py

import datetime
import json
import random
import time
import traceback
import uuid

import requests
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.utils import timezone

import error
import models


def get_available_channel_server():
    min_memusage = None
    min_server = None

    threshold = timezone.now() - datetime.timedelta(seconds=60)

    servers = list(models.ChannelServer.objects.all())
    random.shuffle(servers)

    for server in servers:
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


def kill(req, user_name, sensor_name):
    try:
        user = User.objects.get(username=user_name)
    except User.DoesNotExist:
        res = {
            'code': error.CODE_NO_USER,
            'message': 'User name "%s" does not exist.' % user_name
        }
        return HttpResponse(json.dumps(res, sort_keys=True, indent=4), content_type='application/json')

    models.Entry.objects.filter(user=user, sensor_name=sensor_name).delete()
    res = {
        'code': error.CODE_OK,
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

    channelserver = get_available_channel_server()

    if channelserver:
        res = {
            'code': error.CODE_OK,
            'result': {
                'channel': entry.channel,
                'channel-server-address': entry.channel_server.base_url,
                'transfer-channel-server-address': channelserver.base_url
            }
        }

    else:
        res = {
            'code': error.CODE_NO_SERVER,
            'message': 'there are no available channel server.'
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
    server.last_reporting_time = datetime.datetime.fromtimestamp(timestamp).replace(
        tzinfo=timezone.get_current_timezone())
    server.save()

    res = {
        'code': error.CODE_OK
    }
    return HttpResponse(json.dumps(res, sort_keys=True, indent=4), content_type='application/json')


def sweep_garbages(req):
    # check server is running
    threshold = timezone.now() - datetime.timedelta(seconds=60)
    for server in models.ChannelServer.objects.all():
        server.is_running = (server.last_reporting_time > threshold)
        server.save()

    #
    garbages = []

    for server in models.ChannelServer.objects.all():
        entries = models.Entry.objects.filter(channel_server=server)
        if len(entries):
            #
            if not server.is_running:
                garbages += list(entries)

            else:
                try:
                    ret = requests.get('http://%s/__status/channels/' % server.base_url)
                    if ret.ok:
                        channel_names = ret.json()
                        for entry in entries:
                            if entry.channel not in channel_names:
                                garbages.append(entry)

                except Exception:
                    traceback.print_exc()

            for entry in garbages:
                entry.delete()

    res = {
        'code': error.CODE_OK
    }
    return HttpResponse(json.dumps(res, sort_keys=True, indent=4), content_type='application/json')


def check_listen_channel(req, user_name, sensor_name):
    channel = req.GET.get('channel', None)
    if not channel:
        res = {
            'code': error.CODE_INVALID_PARAMETER,
            'message': '"channel" parameter is missing.'
        }
        return HttpResponse(json.dumps(res, sort_keys=True, indent=4), content_type='application/json')

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

    if entry.channel == channel:
        res = {
            'code': error.CODE_OK,
        }
        return HttpResponse(json.dumps(res, sort_keys=True, indent=4), content_type="application/json")

    else:
        res = {
            'code': error.CODE_VALUE_MISMATCH,
            'message': 'sensor "%s" listen to channel "%s", but got "%s"' % (entry.sensor_name, entry.channel, channel)
        }
        return HttpResponse(json.dumps(res, sort_keys=True, indent=4), content_type="application/json")


def identity(req):
    try:
        key = models.Identity.objects.latest('creation_time')
    except models.Identity.DoesNotExist:
        key = models.Identity()
        key.unique_id = str(uuid.uuid4())
        key.save()

    res = {
        'code': error.CODE_OK,
        'result': {
            'identity': key.unique_id,
        }
    }
    return HttpResponse(json.dumps(res, sort_keys=True, indent=4), content_type="application/json")
