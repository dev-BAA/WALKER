import json
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from django.contrib.auth.models import User
from scripts.common_functions import save_proxies

class WalkerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        await self.close()

    async def receive(self, text_data=None, bytes_data=None):
        msg = json.loads(text_data)

        print(msg)
        method = msg['method']

        if method == 'save_proxies':
            user = User.objects.get(pk=msg['user_id'])
            proxies = await save_proxies(user=user, text_data=msg['data'])

        await self.send(text_data=json.dumps({
            'message': ''
        }))
