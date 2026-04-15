from django.urls import path
from . import views

urlpatterns = [
    # Resume URLs
    path('resumes/', views.ResumeListView.as_view(), name='resume-list'),
    path('resumes/create/', views.ResumeCreateView.as_view(), name='resume-create'),
    path('resumes/<int:pk>/update/', views.ResumeUpdateView.as_view(), name='resume-update'),
    path('resumes/<int:pk>/delete/', views.ResumeDeleteView.as_view(), name='resume-delete'),
    
    # Education URLs
    path('education/', views.EducationListView.as_view(), name='education-list'),
    path('education/create/', views.EducationCreateView.as_view(), name='education-create'),
    path('education/<int:pk>/update/', views.EducationUpdateView.as_view(), name='education-update'),
    path('education/<int:pk>/delete/', views.EducationDeleteView.as_view(), name='education-delete'),
    
    # Experience URLs
    path('experience/', views.ExperienceListView.as_view(), name='experience-list'),
    path('experience/create/', views.ExperienceCreateView.as_view(), name='experience-create'),
    path('experience/<int:pk>/update/', views.ExperienceUpdateView.as_view(), name='experience-update'),
    path('experience/<int:pk>/delete/', views.ExperienceDeleteView.as_view(), name='experience-delete'),
    
    # Skill URLs
    path('skills/', views.SkillListView.as_view(), name='skill-list'),
    path('skills/create/', views.SkillCreateView.as_view(), name='skill-create'),
    path('skills/<int:pk>/update/', views.SkillUpdateView.as_view(), name='skill-update'),
    path('skills/<int:pk>/delete/', views.SkillDeleteView.as_view(), name='skill-delete'),
    
    # Award URLs
    path('awards/', views.AwardAchievementListView.as_view(), name='award-list'),
    path('awards/create/', views.AwardAchievementCreateView.as_view(), name='award-create'),
    path('awards/<int:pk>/update/', views.AwardAchievementUpdateView.as_view(), name='award-update'),
    path('awards/<int:pk>/delete/', views.AwardAchievementDeleteView.as_view(), name='award-delete'),
    
    # Summary URLs
    path('summary/create/', views.ProfessionalSummaryCreateView.as_view(), name='summary-create'),
    path('summary/<int:pk>/update/', views.ProfessionalSummaryUpdateView.as_view(), name='summary-update'),
    path('summary/<int:pk>/delete/', views.ProfessionalSummaryDeleteView.as_view(), name='summary-delete'),
    
    # Link URLs
    path('links/', views.LinkListView.as_view(), name='link-list'),
    path('links/create/', views.LinkCreateView.as_view(), name='link-create'),
    path('links/<int:pk>/update/', views.LinkUpdateView.as_view(), name='link-update'),
    path('links/<int:pk>/delete/', views.LinkDeleteView.as_view(), name='link-delete'),
    
    # Certification URLs
    path('certifications/', views.CertificationListView.as_view(), name='certification-list'),
    path('certifications/create/', views.CertificationCreateView.as_view(), name='certification-create'),
    path('certifications/<int:pk>/update/', views.CertificationUpdateView.as_view(), name='certification-update'),
    path('certifications/<int:pk>/delete/', views.CertificationDeleteView.as_view(), name='certification-delete'),
    
    # Project URLs
    path('projects/', views.ProjectListView.as_view(), name='project-list'),
    path('projects/create/', views.ProjectCreateView.as_view(), name='project-create'),
    path('projects/<int:pk>/update/', views.ProjectUpdateView.as_view(), name='project-update'),
    path('projects/<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project-delete'),
    
    # Job Application URLs
    path('applications/', views.JobApplicationListView.as_view(), name='job-application-list'),
    path('applications/create/', views.JobApplicationCreateView.as_view(), name='job-application-create'),
    path('applications/<int:pk>/update/', views.JobApplicationUpdateView.as_view(), name='job-application-update'),
    path('applications/<int:pk>/delete/', views.JobApplicationDeleteView.as_view(), name='job-application-delete'),
    path('recruiter/job/<int:job_id>/applications/', 
         views.RecruiterApplicationsListView.as_view(), 
         name='recruiter_applications'),
]