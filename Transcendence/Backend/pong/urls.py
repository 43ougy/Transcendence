from django.urls import include, path
from . import views
from .views import *

urlpatterns = [
    path('api/client-id/', GetClientIdView.as_view(), name='get_client_id'),
    path('api/login/', UserLoginView.as_view(), name='user-login'),
    path('api/register/', user_register, name='user-register'),
    path('api/logout/', user_logout, name='user-logout'),
    path('api/matchmaking/', matchmaking, name='matchmaking'),
    path('pong/',     views.pong, name='pong'),
    path('',          UserLoginView.as_view(), name='user-login'),
    path('profile/',  profile_view, name='profile'),
    path('profile/edit/', edit_profile_view, name='edit_profile'),
    path('auth/callback', views.oauth_callback, name='oauth_callback'),
# from .views import UserLoginView, user_register, user_logout, pong, profile_view, edit_profile_view, JoinQueue, CheckJoinGame, ExitQueue
from . import views

urlpatterns = [
    path('api/login/', views.UserLogin.as_view(), name='user-login'),  # Updated class name
    path('api/register/', views.UserRegister.as_view(), name='user-register'),  # Change to class-based view if applicable
    path('api/logout/', views.UserLogout.as_view(), name='user-logout'),  # Change to class-based view if applicable
    path('pong/', views.pong, name='pong'),  # Keep as is if `pong` is a function-based view
    path('profile/', views.profile_view, name='profile'),  # Profile view
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),  # Edit profile view
    path('api/join-queue/', views.JoinQueue.as_view(), name='join_queue'),  # JoinQueue view
    path('api/check-game/', views.CheckJoinGame.as_view(), name='check_game'),  # CheckJoinGame view
    path('api/exit-queue/', views.ExitQueue.as_view(), name='exit_queue'),  # ExitQueue view
]

