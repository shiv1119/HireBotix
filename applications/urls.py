from django.urls import path
from . import views
urlpatterns = [
    # ==================== RESUME URLs ====================
    path('resumes/', views.ResumeListView.as_view(), name='resume-list'),
    path('resumes/create/', views.ResumeCreateView.as_view(), name='resume-create'),
    path('resumes/<int:pk>/update/', views.ResumeUpdateView.as_view(), name='resume-update'),
    path('resumes/<int:pk>/delete/', views.ResumeDeleteView.as_view(), name='resume-delete'),
    
    # Resume Management (New)
    path('resumes/manage/', views.ResumeManageView.as_view(), name='resume-manage'),
    path('resumes/upload/', views.ResumeUploadView.as_view(), name='resume-upload'),
    path('resumes/<int:pk>/set-default/', views.SetDefaultResumeView.as_view(), name='resume-set-default'),
    
    # ==================== EDUCATION URLs ====================
    path('education/', views.EducationListView.as_view(), name='education-list'),
    path('education/create/', views.EducationCreateView.as_view(), name='education-create'),
    path('education/<int:pk>/update/', views.EducationUpdateView.as_view(), name='education-update'),
    path('education/<int:pk>/delete/', views.EducationDeleteView.as_view(), name='education-delete'),
    
    # ==================== EXPERIENCE URLs ====================
    path('experience/', views.ExperienceListView.as_view(), name='experience-list'),
    path('experience/create/', views.ExperienceCreateView.as_view(), name='experience-create'),
    path('experience/<int:pk>/update/', views.ExperienceUpdateView.as_view(), name='experience-update'),
    path('experience/<int:pk>/delete/', views.ExperienceDeleteView.as_view(), name='experience-delete'),
    
    # ==================== SKILL URLs ====================
    path('skills/', views.SkillListView.as_view(), name='skill-list'),
    path('skills/create/', views.SkillCreateView.as_view(), name='skill-create'),
    path('skills/<int:pk>/update/', views.SkillUpdateView.as_view(), name='skill-update'),
    path('skills/<int:pk>/delete/', views.SkillDeleteView.as_view(), name='skill-delete'),
    
    # ==================== PROFESSIONAL SUMMARY URLs ====================
    path('summary/create/', views.ProfessionalSummaryCreateView.as_view(), name='summary-create'),
    path('summary/<int:pk>/update/', views.ProfessionalSummaryUpdateView.as_view(), name='summary-update'),
    path('summary/<int:pk>/delete/', views.ProfessionalSummaryDeleteView.as_view(), name='summary-delete'),
    
    # ==================== LINK URLs ====================
    path('links/', views.LinkListView.as_view(), name='link-list'),
    path('links/create/', views.LinkCreateView.as_view(), name='link-create'),
    path('links/<int:pk>/update/', views.LinkUpdateView.as_view(), name='link-update'),
    path('links/<int:pk>/delete/', views.LinkDeleteView.as_view(), name='link-delete'),
    
    # ==================== CERTIFICATION URLs ====================
    path('certifications/', views.CertificationListView.as_view(), name='certification-list'),
    path('certifications/create/', views.CertificationCreateView.as_view(), name='certification-create'),
    path('certifications/<int:pk>/update/', views.CertificationUpdateView.as_view(), name='certification-update'),
    path('certifications/<int:pk>/delete/', views.CertificationDeleteView.as_view(), name='certification-delete'),
    
    # ==================== PROJECT URLs ====================
    path('projects/', views.ProjectListView.as_view(), name='project-list'),
    path('projects/create/', views.ProjectCreateView.as_view(), name='project-create'),
    path('projects/<int:pk>/update/', views.ProjectUpdateView.as_view(), name='project-update'),
    path('projects/<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project-delete'),
    
    # ==================== JOB APPLICATION URLs ====================
    # Apply for a job (Direct apply page)
    path('job/<int:pk>/apply/', views.ApplyJobView.as_view(), name='apply'),
    
    # View my applications
    path('my-applications/', views.MyApplicationsView.as_view(), name='my-applications'),
    path('my-applications/<int:pk>/', views.ApplicationDetailView.as_view(), name='application-detail'),
    path('my-applications/<int:pk>/withdraw/', views.WithdrawApplicationView.as_view(), name='withdraw-application'),
    
    # ==================== RECRUITER URLs ====================
    path('recruiter/job/<int:job_id>/applications/', 
         views.RecruiterApplicationsListView.as_view(), 
         name='recruiter-applications'),
    path('resume/upload-from-apply/<int:job_id>/', 
         views.ResumeUploadFromApplyView.as_view(), 
         name='resume-upload-from-apply'),

     path('<int:pk>/delete/', views.JobApplicationDeleteView.as_view(), name='job-application-delete'),
     path('user/<int:user_id>/github-stats/', views.UserGitHubStatsView.as_view(), name='user_github_stats'),
     path('<int:application_id>/update-status/', views.UpdateApplicationStatusView.as_view(), name='update_application_status'),
     path('<int:application_id>/add-note/', views.AddApplicationNoteView.as_view(), name='add_application_note'),
]