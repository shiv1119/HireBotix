from django.db import models
from django.contrib.auth.models import User

ROLES_CHOICES = (
    ('user', 'User'),
    ('recruiter', 'Recruiter'),
    ('admin', 'Admin'),
)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    date_of_birth = models.DateField()
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
    )
    profile_photo = models.ImageField(upload_to="profile_photos/", blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLES_CHOICES, default="user")
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_type = models.CharField(max_length=20, choices=[
        ('job_seeker', 'Job Seeker'),
        ('company_employee', 'Company Employee'),
        ('company_admin', 'Company Admin'),
    ], default='job_seeker')

    def __str__(self):
        return self.full_name

class Address(models.Model):
    user_profile = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="address"
    )
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.address_line_1}, {self.city}"

class Announcement(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    

class Testimonial(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="testimonials")
    feedback = models.TextField()
    rating = models.IntegerField(default=5) 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.rating}⭐"
    
class ContactUs(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True, null=True)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ("user_update", "User Update"),
        ("system", "System Notification"),
        ("contact", "Contact"),
        ("address_added", "Address Added"),
        ("address_updated", "Address Updated"),
        ("invitation_sent", "Invitation Sent"),
        ("invitation_accepted", "Invitation Accepted"),
        ("job_application", "Job Application"),
 
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    link = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    related_object_id = models.CharField(max_length=36, null=True, blank=True)
    related_model = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        recipient = self.user.username if self.user else "Unknown"
        return f"{recipient} - {self.get_notification_type_display()} - {self.created_at}"

    def mark_as_read(self):
        self.is_read = True
        self.save()

    @staticmethod
    def get_unread_count(user):
        return Notification.objects.filter(user=user, is_read=False).count()

    @staticmethod
    def get_unread_role_notifications(role):
        return Notification.objects.filter(role=role, is_read=False).count()


class NotificationPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    in_app_notification = models.BooleanField(default=True)
    edited_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Preferences"
    
from django.utils.timezone import now, timedelta
from django.contrib.sessions.models import Session

class LoginHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    device = models.CharField(max_length=255, null=True, blank=True)
    operating_system = models.CharField(max_length=255, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    
    timestamp = models.DateTimeField(default=now) 
    last_activity = models.DateTimeField(default=now)  
    is_active_session = models.BooleanField(default=True) 

    city = models.CharField(max_length=100, null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    @property
    def is_active(self):
        return Session.objects.filter(session_key=self.session_key).exists()

    def update_activity(self):
        self.last_activity = now()
        self.save(update_fields=['last_activity'])

    def check_activity(self):
        if now() - self.last_activity > timedelta(minutes=30):
            self.is_active_session = False
            self.save(update_fields=['is_active_session'])

    def __str__(self):
        status = "Active" if self.is_active else "Logged Out"
        return f"{self.user.username} - {self.timestamp} - {self.device} ({self.operating_system}) - {status}"

import uuid
class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False)
    is_subscribed = models.BooleanField(default=True)
    unsubscribe_token = models.UUIDField(default=uuid.uuid4, unique=True) 

    def __str__(self):
        return self.email