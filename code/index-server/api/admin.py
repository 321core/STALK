# -*- coding: utf-8 -*-
# admin.py

from django.contrib import admin
import models


admin.autodiscover()

admin.site.register(models.Entry)
admin.site.register(models.ChannelServer)
