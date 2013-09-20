from django.conf.urls import patterns, include, url
from ht_scoring.scoring.views import competition_pages

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'ht_scoring.scoring.views.index'),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)

for page in competition_pages:
	urlpatterns += patterns('ht_scoring.scoring.views',
    url(r'^' + page['page'] + r'/submit', page['page'] + '_submit'),
    url(r'^' + page['page'] + r'/', page['page']))