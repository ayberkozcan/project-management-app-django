from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .views import AccountLoginView, SignUpView

urlpatterns = [
    path("login/", AccountLoginView.as_view(), name="login"),
    path("signup/", SignUpView.as_view(), name="signup"),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
