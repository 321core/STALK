# urls.py

from django.conf.urls import include, url
from django.contrib import admin


urlpatterns = [
    url(r'^register/(?P<sensor_name>.*)/$', 'api.views.register', name='register'),
    url(r'^query/(?P<sensor_name>.*)/$', 'api.views.query', name='query')
]
