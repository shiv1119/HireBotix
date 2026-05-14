# company/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Company, EmployeeRole


@receiver(post_save, sender=Company)
def create_default_roles(sender, instance, created, **kwargs):

    if created:

        default_roles = [
            {
                'name': 'company_admin',
                'can_post_jobs': True,
                'can_edit_jobs': True,
                'can_view_applications': True,
                'can_manage_team': True,
            },
            {
                'name': 'recruiter',
                'can_post_jobs': True,
                'can_edit_jobs': True,
                'can_view_applications': True,
                'can_manage_team': False,
            },
            {
                'name': 'hr_manager',
                'can_post_jobs': True,
                'can_edit_jobs': True,
                'can_view_applications': True,
                'can_manage_team': True,
            },
            {
                'name': 'hiring_manager',
                'can_post_jobs': False,
                'can_edit_jobs': False,
                'can_view_applications': True,
                'can_manage_team': False,
            },
        ]

        for role_data in default_roles:
            EmployeeRole.objects.get_or_create(
                company=instance,
                name=role_data['name'],
                defaults=role_data
            )