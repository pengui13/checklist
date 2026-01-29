from django.urls import path, include
from .views import GetUserInfo, UpdateUserColor, UpdateActivity, CreateUser, GetAllUsers, SendInvitationView, AcceptInvitationView
urlpatterns = [
    
    path('', include('dj_rest_auth.urls')),  
    path('registration/', include('dj_rest_auth.registration.urls')),
    path('user/', GetUserInfo.as_view(), name = 'user_details'),  
    path('users/', GetAllUsers.as_view(), name = 'users'), 
    path('set_color/', UpdateUserColor.as_view(), name = 'set_color'),  
    path('users/create/', CreateUser.as_view(), name = 'create_user'),  
    path("invitations/send/", SendInvitationView.as_view(), name="invitation-send"),
    path("invitations/accept/", AcceptInvitationView.as_view(), name="invitation-accept"),
    path("toggle_active/", UpdateActivity.as_view(), name="toggle_activity"),
    
]
