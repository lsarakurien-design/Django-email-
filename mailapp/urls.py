# mailapp/urls.py
from django.urls import path
from . import views

app_name = 'mailapp'

urlpatterns = [
    path('', views.inbox_view, name='email_list'),           # root -> Inbox
    path('inbox/', views.inbox_view, name='email_list'),     # optional explicit inbox/
    path('inbox/<int:pk>/', views.email_detail, name='email_detail'),
    path('send/', views.send_email_view, name='send_email'),
    path('success/', views.success_view, name='success'),
    path('fetch/', views.fetch_emails, name='fetch_emails'),  # fetch from IMAP
]

