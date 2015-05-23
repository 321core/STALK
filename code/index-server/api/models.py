# -*- coding utf-8 -*-
# models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User


class ChannelServer(models.Model):
	server_name = models.CharField(db_index=True, max_length=64)
	base_url = models.CharField(max_length=128, null=True, blank=True)
	is_visible = models.BooleanField(default=True)
	is_running = models.BooleanField(default=False)
	last_reporting_time = models.DateTimeField(null=True, blank=True)
	num_channels = models.PositiveIntegerField(default=0)
	cpu_rate = models.FloatField(default=0)
	memory_rate = models.FloatField(default=0)

	def __unicode__(self):
		return u'%s' % self.server_name


class Entry(models.Model):
	user = models.ForeignKey(User)
	sensor_name = models.CharField(db_index=True, max_length=64)
	channel_server = models.ForeignKey(ChannelServer, null=True, blank=True)
	channel = models.CharField(max_length=64, null=True, blank=True)
	last_listening_time = models.DateTimeField(auto_now=True)
	last_connecting_time = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return u'%s@%s' % (self.sensor_name, self.last_listening_time)
