# urls.py

from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^listen/(?P<user_name>.*)/(?P<sensor_name>.*)/$', 'api.views.listen', name='listen'),
    url(r'^kill/(?P<user_name>.*)/(?P<sensor_name>.*)/$', 'api.views.kill', name='kill'),
    url(r'^check_listen_channel/(?P<user_name>.*)/(?P<sensor_name>.*)/$',
        'api.views.check_listen_channel', name='check_listen_channel'),
    url(r'^connect/(?P<user_name>.*)/(?P<sensor_name>.*)/$', 'api.views.connect', name='connect'),
    url(r'^report_channel_server_status/(?P<server_name>.*)/$', 'api.views.report_channel_server_status',
        name='report_channel_server_status'),
    url(r'^sweep_garbages/$', 'api.views.sweep_garbages', name='sweep_garbages'),
    url(r'^identity/$', 'api.views.identity', name='identity'),
]
