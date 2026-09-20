import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db import transaction
from django.utils import timezone
from .models import Auction, AuctionBid
from decimal import Decimal, InvalidOperation

class AuctionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.auction_id = self.scope['url_route']['kwargs']['auction_id']
        self.room_group_name = f'auction_{self.auction_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            action = text_data_json.get('action')
            
            if action == 'place_bid':
                amount = text_data_json.get('amount')
                user = self.scope['user']
                
                if not user.is_authenticated:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'You must be logged in to place a bid.'
                    }))
                    return
                
                try:
                    amount = Decimal(str(amount))
                except (InvalidOperation, ValueError, TypeError):
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Invalid bid amount.'
                    }))
                    return
                
                # Attempt to place bid with select_for_update
                result = await self.place_bid(user, amount)
                
                if result.get('success'):
                    # Broadcast the new bid to the group
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'auction_bid',
                            'amount': str(result['amount']),
                            'user_email': result['user_email'],
                            'timestamp': result['timestamp']
                        }
                    )
                else:
                    # Send error to the specific user
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': result.get('message', 'Failed to place bid.')
                    }))
        except json.JSONDecodeError:
            pass

    @database_sync_to_async
    def place_bid(self, user, amount):
        with transaction.atomic():
            try:
                auction = Auction.objects.select_for_update().get(id=self.auction_id)
            except Auction.DoesNotExist:
                return {'success': False, 'message': 'Auction not found.'}
            
            if not auction.is_live:
                return {'success': False, 'message': 'Auction is not live.'}
            
            highest_bid_val = auction.highest_bid
            min_increment = auction.min_increment
            
            if amount < (highest_bid_val + min_increment):
                return {
                    'success': False, 
                    'message': f'Bid must be at least {highest_bid_val + min_increment}'
                }
            
            bid = AuctionBid.objects.create(
                auction=auction,
                user=user,
                amount=amount
            )
            
            return {
                'success': True,
                'amount': bid.amount,
                'user_email': user.email,
                'timestamp': bid.timestamp.isoformat()
            }

    async def auction_bid(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'new_bid',
            'amount': event['amount'],
            'user_email': event['user_email'],
            'timestamp': event['timestamp']
        }))
