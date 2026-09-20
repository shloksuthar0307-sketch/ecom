import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import GroupPurchase

class GroupBuyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.token = self.scope['url_route']['kwargs']['token']
        self.group_name = f'groupbuy_{self.token}'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        
        # Send current count on connect
        count = await self.get_member_count(self.token)
        await self.send(text_data=json.dumps({
            'type': 'member_count',
            'count': count
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        pass

    async def groupbuy_update(self, event):
        count = event['count']
        is_locked = event.get('is_locked', False)
        
        await self.send(text_data=json.dumps({
            'type': 'member_count',
            'count': count,
            'is_locked': is_locked
        }))

    @sync_to_async
    def get_member_count(self, token):
        try:
            group = GroupPurchase.objects.get(token=token)
            return group.members.count()
        except GroupPurchase.DoesNotExist:
            return 0
