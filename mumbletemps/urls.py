from django.urls import path

from . import views

app_name = "mumbletemps"

urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("join/<link_ref>/", views.TempLinkLogin.as_view(), name="join"),
    path("delete/<link_ref>/", views.DeleteTempLink.as_view(), name="delete"),
]
