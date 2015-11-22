from django.conf.urls import include, url
from django.contrib import admin
from api import urls as api_urls

admin.autodiscover()

urlpatterns = [
    url('^stalk/master/admin/', include(admin.site.urls)),
    url('^stalk/master/api/', include(api_urls))
]
