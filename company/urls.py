from django.urls import path
from . import views


urlpatterns = [
    # Company registration
    path('register/', views.CompanyRegistrationView.as_view(), name='register_company'),
    path('register/success/', views.CompanyRegistrationSuccessView.as_view(), name='registration_success'),
    
    # Company selection (for users with multiple companies)
    path('select/', views.CompanySelectionView.as_view(), name='company_selection'),
    path('switch/<int:company_id>/', views.SwitchCompanyView.as_view(), name='switch_company'),
    
    # Company dashboard (with company_id)
    path('dashboard/<int:company_id>/', views.CompanyDashboardView.as_view(), name='company_dashboard'),
    path('dashboard/', views.CompanyDashboardView.as_view(), name='company_dashboard_default'),
    
    # Company management (admin only)
    path('list/', views.CompanyListView.as_view(), name='company_list'),
    path('<int:pk>/', views.CompanyDetailView.as_view(), name='company_detail'),
    path('<int:pk>/verify/', views.CompanyVerifyView.as_view(), name='company_verify'),
    
    # Employee management (with company_id)
    path('<int:company_id>/invite/', views.InviteEmployeeView.as_view(), name='invite_employee'),
        path('<int:company_id>/employees/', views.EmployeeListView.as_view(), name='employee_list'),
    path('<int:company_id>/remove-employee/<int:employee_id>/', views.RemoveEmployeeView.as_view(), name='remove_employee'),
    
    # Invitation
    path('invite/accept/<str:token>/', views.AcceptInvitationView.as_view(), name='accept_invitation'),
    path('admin/company-approvals/', views.CompanyApprovalListView.as_view(), name='company_approval_list'),
    path('company/approve/', views.CompanyApproveView.as_view(), name='company_approve'),
    path('company/reject/', views.CompanyRejectView.as_view(), name='company_reject'),
    path('<int:company_id>/preview/', views.CompanyPreviewView.as_view(), name='company_preview'),
]