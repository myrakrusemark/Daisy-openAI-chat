from django.urls import path
from .views import ChatView

urlpatterns = [
    path('', ChatView.as_view(), name='dashboard'),
]
