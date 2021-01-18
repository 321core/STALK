from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('stalk/master/admin/', admin.site.urls),
    path('stalk/master/api/', include('api.urls'))
]
