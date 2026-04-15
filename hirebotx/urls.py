from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from user.customViews.passwordReset import (
    CustomPasswordResetView, 
    CustomPasswordResetDoneView, 
    CustomPasswordResetConfirmView, 
    CustomPasswordResetCompleteView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include("user.urls")),
    path("password_reset/", CustomPasswordResetView.as_view(), name="password_reset"),
    path("password_reset/done/", CustomPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", CustomPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", CustomPasswordResetCompleteView.as_view(), name="password_reset_complete"),
    path('jobs/', include('jobs.urls')),
    path('applications/', include('applications.urls')),
    path('ats-checker/', include('ats_checker.urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)