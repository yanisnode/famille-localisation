from django.urls import include, path
from django.views.generic import TemplateView

from famille import views as fv

urlpatterns = [
    path("api/family/", include("famille.urls")),
    path("parent/", TemplateView.as_view(template_name="parent.html")),
    path("enroll", TemplateView.as_view(template_name="enroll.html")),
    path("enroll/", TemplateView.as_view(template_name="enroll.html")),
    # Vérification des liens mobiles (servis à la racine du domaine).
    path(".well-known/assetlinks.json", fv.assetlinks),
    path(".well-known/apple-app-site-association", fv.aasa),
]
