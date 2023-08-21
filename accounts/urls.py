from django.urls import path
from . import views
from django.contrib.auth import views as auth_view

urlpatterns = [
    path('', auth_view.LoginView.as_view(template_name='accounts/login.html'), name = 'accounts-login'),
    path('dashboard/', views.index, name = 'accounts-dashboard'),
    path('add/user/', views.create_user, name = 'accounts-create-user'),
    path('profile/update/', views.profile_update, name = 'accounts-profile-update'),
    path('user/profile/', views.profile, name = 'accounts-profile'),
    path('logout/', auth_view.LogoutView.as_view(template_name='accounts/logout.html'), name = 'accounts-logout'),
]