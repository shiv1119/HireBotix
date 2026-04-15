# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.ATSDashboardView.as_view(), name='dashboard'),
    path('score/<int:pk>/', views.ScoreDetailView.as_view(), name='score_detail'),
]