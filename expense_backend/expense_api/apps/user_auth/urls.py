from django.urls import path
from .models import User
from .views import (
    UserRegisterView, MeView, loginView, UdateAccessToken, 
    logoutView, UserListView, UserDetailView, UpdateUserDetails, 
    UpdateUserProfile, FriendsListView, ManageFriendView
)

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', loginView.as_view(), name='login'),
    path('logout/', logoutView.as_view(), name='logout'),
    path('users-list/', UserListView.as_view(), name='users-list'),
    path('users-list/<int:user_id>/', UserDetailView.as_view(), name='users-detail'),
    path('update/', UpdateUserDetails.as_view(), name='update'),
    path('update-profile/', UpdateUserProfile.as_view(), name='update-profile'),
    path('updateAcessToken/', UdateAccessToken.as_view(), name='update'),
    path("me/", MeView.as_view(), name="me"),
    path('friends/', FriendsListView.as_view(), name='friends-list'),
    path('friends/manage/', ManageFriendView.as_view(), name='manage-friend'),
]