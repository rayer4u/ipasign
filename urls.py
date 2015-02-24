from django.conf.urls import patterns, include, url
from django.views.generic import FormView
from views import upload
from forms import UploadModelFileForm

urlpatterns = patterns('',
#     url(r'^$', views.index, name='index'),
    url(r'^$', upload, name='upload'),
)
