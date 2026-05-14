from django.urls import path
from .views import (
    JobCreateView, 
    JobListView, 
    JobDetailView, 
    UserJobsListView,
    JobUpdateView,
    CompanyJobsListView,
    JobApprovalListView,
    JobApproveView
)

urlpatterns = [
    # Public URLs
    path('', JobListView.as_view(), name='job_list'),
    path('<int:job_id>/', JobDetailView.as_view(), name='job_detail'),
    
    # Recruiter URLs
    path('create/', JobCreateView.as_view(), name='create_job'),
    path('<int:job_id>/edit/', JobUpdateView.as_view(), name='edit_job'),
    path('user/<int:user_id>/', UserJobsListView.as_view(), name='user_jobs'),
    path('company/jobs/', CompanyJobsListView.as_view(), name='company_jobs'),
    
    # Admin URLs
    path('admin/approvals/', JobApprovalListView.as_view(), name='job_approval_list'),
    path('admin/<int:job_id>/approve/', JobApproveView.as_view(), name='job_approve'),
]