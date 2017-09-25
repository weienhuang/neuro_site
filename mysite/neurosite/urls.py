from django.conf.urls import url

from . import views

urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^(?P<page>[0-9]+)/$', views.index, name='index'),
	url(r'^(?P<page>[0-9]+)/detail/(?P<pmid>[0-9]+)/$', views.detail, name='detail')
]