from django.conf.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^listen/(?P<user_name>.*)/(?P<sensor_name>.*)/$', views.listen, name='listen'),
    re_path(r'^kill/(?P<user_name>.*)/(?P<sensor_name>.*)/$', views.kill, name='kill'),
    re_path(r'^check_listen_channel/(?P<user_name>.*)/(?P<sensor_name>.*)/$', views.check_listen_channel, name='check_listen_channel'),
    re_path(r'^connect/(?P<user_name>.*)/(?P<sensor_name>.*)/$', views.connect, name='connect'),
    re_path(r'^report_channel_server_status/(?P<server_name>.*)/$', views.report_channel_server_status, name='report_channel_server_status'),
    re_path(r'^sweep_garbages/$', views.sweep_garbages, name='sweep_garbages'),
    re_path(r'^identity/$', views.identity, name='identity'),
]
