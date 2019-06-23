"""test_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls import url
from apache_logs.views import *

urlpatterns = [
    url(r'^$', redirect_view, name='root'),
    url(r'^admin/', admin.site.urls),
    url(r'^logs/$', LogsView.as_view(), name='logs'),
    url(r'^list/$', ApacheLogListView.as_view(), name='apachelog-list'),
]
