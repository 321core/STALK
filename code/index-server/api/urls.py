# urls.py

from django.conf.urls import include, url
from django.contrib import admin


urlpatterns = [
	# for compatibility
	url(r'^register/(?P<sensor_name>.*)/$', 'api.views.register', name='register'),
	url(r'^query/(?P<sensor_name>.*)/$', 'api.views.query', name='query'),

	# new APIs
	url(r'^listen/(?P<user_name>.*)/(?P<sensor_name>.*)/$', 'api.views.listen', name='listen'),
	url(r'^connect/(?P<user_name>.*)/(?P<sensor_name>.*)/$', 'api.views.connect', name='connect'),
	url(r'^report_channel_server_status/(?P<server_name>.*)/$', 'api.views.report_channel_server_status',
	    name='report_channel_server_status'),
]
