from django.urls import path

from rest_framework.authtoken.views import obtain_auth_token

from . import views

urlpatterns = [
    # Côté parent (super-admin, auth Token)
    path("devices/", views.DeviceListView.as_view()),
    path("devices/<int:pk>/", views.DeviceDetailView.as_view()),
    path("invites/", views.InviteView.as_view()),
    path("login/", obtain_auth_token),
    # Côté appareil enfant (device_token)
    path("enroll/", views.enroll),
    path("ping/", views.ping),
    path("sharing/", views.set_sharing),
]
