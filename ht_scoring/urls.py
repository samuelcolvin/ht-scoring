from django.conf.urls import patterns, include, url
import SkeletalDisplay.urls
import ht_scoring.scoring.views as s_views

from django.contrib import admin
admin.autodiscover()

urlpatterns = SkeletalDisplay.urls.urlpatterns
urlpatterns += patterns('',
    url(r'^$', s_views.Index.as_view(), name='index'),
    url(r'^comp/(?P<comp>\d+)$', s_views.CompetitionDisplay.as_view(), name='comp_display'),
    url(r'^faults/(?P<comp>\d+)$', s_views.Faults.as_view(), name='faults'),
    url(r'^times/(?P<comp>\d+)$', s_views.Times.as_view(), name='times'),
    url(r'^completeness/(?P<comp>\d+)$', s_views.CompletenessDisplay.as_view(), name='completeness'),
    url(r'^results/(?P<comp>\d+)$', s_views.Results.as_view(), name='results'),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)

# for page in s_views.competition_pages:
# 	urlpatterns += patterns('ht_scoring.scoring.views',
#     url(r'^' + page['page'] + r'/submit', page['page'] + '_submit'),
#     url(r'^' + page['page'] + r'/', page['page']))