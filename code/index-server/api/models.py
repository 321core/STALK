# -*- coding utf-8 -*-
# models.py

from django.db import models


class Entry(models.Model):
	sensor_name = models.CharField(db_index=True, primary_key=True, max_length=255)
	channel = models.CharField(db_index=True, max_length=256)
	time = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return u'%s@%s' % (self.sensor_name, self.time)
