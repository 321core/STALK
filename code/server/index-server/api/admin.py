from django.contrib import admin

from . import models

admin.autodiscover()

admin.site.register(models.Entry)
admin.site.register(models.ChannelServer)
