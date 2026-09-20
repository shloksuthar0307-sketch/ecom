import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ProductConsumer(AsyncWebsocketConsumer):
    # Class-level dictionary to track viewers per product to avoid DB hits
    viewers = {}

    async def connect(self):
        self.product_id = self.scope['url_route']['kwargs']['product_id']
        self.group_name = f'product_{self.product_id}'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

        # Update viewer count
        if self.product_id not in self.viewers:
            self.viewers[self.product_id] = 0
        self.viewers[self.product_id] += 1

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'viewer_count_update',
                'count': self.viewers[self.product_id]
            }
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

        if self.product_id in self.viewers:
            self.viewers[self.product_id] = max(0, self.viewers[self.product_id] - 1)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'viewer_count_update',
                    'count': self.viewers[self.product_id]
                }
            )

    async def viewer_count_update(self, event):
        count = event['count']
        await self.send(text_data=json.dumps({
            'type': 'viewer_count',
            'count': count
        }))
        
    async def stock_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'stock_update',
            'stock': event['stock']
        }))
        
    async def purchase_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'purchase_update'
        }))
