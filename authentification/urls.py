from .views import RegisterApiView, CustomObtainAuthToken, AccountApiEditView, AccountView
from django.urls import path


app_name = 'authenticate'

urlpatterns = [
    path('register/', RegisterApiView.as_view(), name='registration'),
    path('login/', CustomObtainAuthToken.as_view(), name='login'),
    path('account/<slug:slug>/', AccountApiEditView.as_view(), name='account'),
    path('account/public/<slug:slug>/', AccountView.as_view(), name='account_view')
]