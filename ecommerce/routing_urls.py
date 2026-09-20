from django.urls import re_path
from products.consumers import ProductConsumer
from orders.consumers import GroupBuyConsumer
from auctions.consumers import AuctionConsumer

websocket_urlpatterns = [
    re_path(r'ws/product/(?P<product_id>\w+)/$', ProductConsumer.as_asgi()),
    re_path(r'ws/group-buy/(?P<token>[\w-]+)/$', GroupBuyConsumer.as_asgi()),
    re_path(r'ws/auction/(?P<auction_id>\w+)/$', AuctionConsumer.as_asgi()),
]

