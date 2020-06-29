from django.urls import re_path


from . import views

urlpatterns = [
    re_path(r'^$', views.groups, name='groups'),
    re_path(r'^groups/$', views.groups, name='groups'),
    re_path(r'^group/$', views.group_page, name='group'),
    re_path(r'^group/(?P<group_id>[0-9]+)/$', views.group_page, name='group'),
    re_path(r'^group/(?P<group_id>[0-9]+)/gtask/$', views.gtask_page, name='gtask'),
    re_path(r'^group/(?P<group_id>[0-9]+)/gtask/(?P<gtask_id>[0-9]+)/$', views.gtask_page, name='gtask'),
    re_path(r'^gtask/$', views.gtask_page, name='gtask'),
    re_path(r'^add-gtask/(?P<group_id>[0-9]+)$', views.gtask_page, name='gtask'),
    re_path(r'^remove-gtask/group/(?P<group_id>[0-9]+)/gtask/(?P<gtask_id>[0-9]+)/$', views.remove_gtask, name='remove_gtask'),
    re_path(r'^remove-group/group/(?P<group_id>[0-9]+)/$', views.remove_group, name='remove_group'),
    re_path(r'^remove-proxy/(?P<proxy_id>[0-9]+)/$', views.remove_proxy, name='remove_proxy'),
    re_path(r'^remove-proxy1/(?P<proxy_id>[0-9]+)/$', views.remove_proxy1, name='remove_proxy1'),
    re_path(r'^change-proxy-status/(?P<proxy_id>[0-9]+)/$', views.change_proxy_status, name='change_proxy_status'),
    re_path(r'^change-proxy-status1/(?P<proxy_id>[0-9]+)/$', views.change_proxy_status1, name='change_proxy_status1'),
    re_path(r'^change-gtask-status/group/(?P<group_id>[0-9]+)/gtask/(?P<gtask_id>[0-9]+)/$', views.change_gtask_status, name='change_gtask_status'),
    re_path(r'^logs/$', views.logs, name='logs'),
    re_path(r'^historys/$', views.historys, name='historys'),
    re_path(r'^errors/$', views.errors, name='errors'),
    re_path(r'^ap/$', views.ap, name='ap'),
    re_path(r'^results/$', views.results, name='results'),
    re_path(r'^proxy/$', views.proxy, name='proxy'),
    re_path(r'^proxy1/$', views.proxy1, name='proxy1'),
    re_path(r'^settings/$', views.settings, name='settings'),
    re_path(r'^sign-up/$', views.sign_up, name='sign_up'),
    re_path(r'^sign-in/$', views.sign_in, name='sign_in'),
    re_path(r'^sign-out/$', views.sign_out, name='sign_out'),
    #re_path(r'^getpage/(?P<url>.+)/$', views.getpage, name='getpage'),
    re_path(r'^getpage/$', views.getpage, name='getpage'),
    re_path(r'^getgglposition/$', views.getgglposition, name='getgglposition'),
    #re_path(r'^getavito?url=(?P<url>.+)/$', views.getavito, name='getavito'),
    #re_path(r'^getavito/(?P<url>[0-9]+)/$', views.getavito, name='getavito'),
]