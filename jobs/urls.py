# jobs/urls.py

from django.urls import path
from .views import JobCreateView, JobListView, JobDetailView,UserJobsListView

urlpatterns = [
    path('', JobListView.as_view(), name='job_list'),
    path('create/', JobCreateView.as_view(), name='create_job'),
    path('jobs/<int:job_id>/', JobDetailView.as_view(), name='job_detail'),
    path('jobs/user/<int:user_id>/', UserJobsListView.as_view(), name='user_jobs'),
]