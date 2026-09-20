from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import ajax_views

urlpatterns = [
    path('', views.account_dashboard, name='account_dashboard'),
    path('orders/', views.account_orders, name='account_orders'),
    path('register/', views.register_view, name='register'),
    path('address/add-ajax/', ajax_views.add_address_ajax, name='add_address_ajax'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    
    # Password Reset
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='emails/password_reset.html',
        html_email_template_name='emails/password_reset.html',
        subject_template_name='emails/password_reset_subject.txt',
        success_url='/account/password_reset/done/'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url='/account/reset/done/'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
]
