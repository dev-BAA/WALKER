from django.conf.urls import url

from walker_panel import consumers

websocket_urlpatterns = [
    url(r'^ws/$', consumers.WalkerConsumer)
    # (http->django views is added by default)
]