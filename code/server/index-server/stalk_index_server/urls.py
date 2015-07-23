from django.conf.urls import include, url
from django.contrib import admin
from api import urls as api_urls

admin.autodiscover()

urlpatterns = [
    url('^admin/', include(admin.site.urls)),
    url('^api/', include(api_urls))
]
