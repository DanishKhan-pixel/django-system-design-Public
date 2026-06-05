from django.urls import path

from . import views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('token/refresh/', views.token_refresh_view, name='token-refresh'),
    path('profile/', views.profile_view, name='profile'),
]
