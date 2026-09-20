from django.urls import path
from . import views

urlpatterns = [
    path('chat_api/', views.chat_api, name='chat_api'),
    path('ai-search/', views.ai_search, name='ai_search'),
]
