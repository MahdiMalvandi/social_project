from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register/', RegisterAndSendEmail.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/', GetUserToken.as_view(), name='token_obtain_pair'),
    path('resend/', ResendCode.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
