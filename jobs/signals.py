# jobs/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Job
from user.models import UserProfile

@receiver(post_save, sender=Job)
def make_user_recruiter(sender, instance, created, **kwargs):
    if created:
        profile = instance.recruiter.profile

        if profile.role == 'user':
            profile.role = 'recruiter'
            profile.save(update_fields=['role']) 