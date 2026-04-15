# user/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import NotificationPreferences
import requests
import re
from django.contrib.sites.models import Site
import user_agents
from django.utils.timezone import now
from django.contrib.sessions.models import Session
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from .models import *
from django.core.mail import send_mail, EmailMultiAlternatives
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.urls import reverse
import logging
from django.conf import settings

# Import the async email function
from .email_utils import send_email_async

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    if created:
        NotificationPreferences.objects.create(user=instance, in_app_notification=True)

def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip

def get_location(ip):
    try:
        response = requests.get(f"https://ipwho.is/{ip}", timeout=5)
        data = response.json()
        if data.get("success"):
            return {
                "city": data.get("city", "Unknown"),
                "region": data.get("region", "Unknown"),
                "country": data.get("country", "Unknown"),
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
            }
    except requests.RequestException as e:
        logger.error(f"Location fetch failed for IP {ip}: {str(e)}")
        pass 
    return None

def extract_device_name(user_agent, user_agent_string):
    if user_agent.is_mobile:
        return detect_mobile_model(user_agent, user_agent_string)
    elif user_agent.is_tablet:
        return detect_tablet_model(user_agent, user_agent_string)
    elif user_agent.is_pc:
        return detect_pc_brand(user_agent_string)
    return "Unknown Device"

def detect_mobile_model(user_agent, user_agent_string):
    model = user_agent.device.family
    if not model or model == "Generic Smartphone":
        model = extract_model_from_ua(user_agent_string)
    return f"{model} (Mobile)" if model else "Unknown Mobile"

def detect_tablet_model(user_agent, user_agent_string):
    model = user_agent.device.family
    if not model or model == "Generic Tablet":
        model = extract_model_from_ua(user_agent_string)
    return f"{model} (Tablet)" if model else "Unknown Tablet"

def detect_pc_brand(user_agent_string):
    device_patterns = [
        (r"MSI", "MSI"), (r"Dell", "Dell"), (r"HP", "HP"),
        (r"Asus", "Asus"), (r"Lenovo", "Lenovo"), (r"Acer", "Acer"),
        (r"Macintosh", "Apple Mac"), (r"Mac OS X", "Apple Mac"),
    ]
    for pattern, brand in device_patterns:
        if re.search(pattern, user_agent_string, re.IGNORECASE):
            return brand
    return "PC"

def extract_model_from_ua(user_agent_string):
    device_patterns = [
        (r"iPhone\s([\d\w]+)", "iPhone {}"),
        (r"iPad; CPU OS ([\d_]+)", "iPad (iOS {})"),
        (r"SM-(\w+)", "Samsung Galaxy {}"),
        (r"GT-(\w+)", "Samsung Galaxy {}"),
        (r"Pixel\s([\d\w]+)", "Google Pixel {}"),
        (r"Redmi\s([\d\w]+)", "Xiaomi Redmi {}"),
        (r"Mi\s([\d\w]+)", "Xiaomi Mi {}"),
        (r"OnePlus\s([\d\w]+)", "OnePlus {}"),
        (r"Huawei\s([\d\w]+)", "Huawei {}"),
        (r"Fire\s([\d\w]+)", "Amazon Fire {}"),
    ]
    for pattern, format_str in device_patterns:
        match = re.search(pattern, user_agent_string, re.IGNORECASE)
        if match:
            return format_str.format(match.group(1))
    return None

@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    try:
        ip = get_client_ip(request)
        user_agent_str = request.META.get("HTTP_USER_AGENT", "")
        user_agent = user_agents.parse(user_agent_str)
        os = f"{user_agent.os.family} {user_agent.os.version_string}" or "Unknown OS"
        device = extract_device_name(user_agent, user_agent_str)
        location = get_location(ip)

        session_key = request.session.session_key
        request.session["device"] = device
        request.session["operating_system"] = os
        request.session["last_activity"] = now().isoformat()
        request.session.modified = True

        existing_record = LoginHistory.objects.filter(user=user, ip_address=ip, device=device).first()

        if existing_record:
            existing_record.timestamp = now()
            existing_record.session_key = session_key
            existing_record.city = location["city"] if location else "Unknown"
            existing_record.region = location["region"] if location else "Unknown"
            existing_record.country = location["country"] if location else "Unknown"
            existing_record.latitude = location["latitude"] if location else None
            existing_record.longitude = location["longitude"] if location else None
            existing_record.save()
        else:
            LoginHistory.objects.create(
                user=user, ip_address=ip, user_agent=user_agent_str,
                device=device, operating_system=os, session_key=session_key,
                city=location["city"] if location else "Unknown",
                region=location["region"] if location else "Unknown",
                country=location["country"] if location else "Unknown",
                latitude=location["latitude"] if location else None,
                longitude=location["longitude"] if location else None,
            )
    except Exception as e:
        logger.error(f"Error in log_login signal for user {user.username}: {str(e)}")

from .helpers import create_notification 

@receiver(post_save, sender=ContactUs)
def send_contact_email_and_notification(sender, instance, created, **kwargs):
    if not created:
        return
    
    try:
        site_url = f"{settings.SITE_URL}"
        admin_link = f"{site_url}{reverse('admin:user_contactus_change', args=[instance.id])}"

        admin_emails = list(User.objects.filter(is_staff=True).values_list('email', flat=True))

        if admin_emails:
            email_html_content = render_to_string("user/email/contact_email.html", {
                "name": instance.name,
                "email": instance.email,
                "phone": instance.phone if instance.phone else "Not provided",
                "subject": instance.subject,
                "message": instance.message,
                "admin_link": admin_link
            })
            
            # Send email asynchronously - NO BLOCKING
            send_email_async(
                subject=f"New Contact Us Message: {instance.subject}",
                html_message=email_html_content,
                recipient_list=admin_emails
            )
        
        admins = User.objects.filter(is_staff=True)
        for admin in admins:
            create_notification(
                user=admin,
                notification_type="contact",
                message=f"New Contact Us message from {instance.name}: {instance.subject}",
                related_object=instance
            )
    except Exception as e:
        logger.error(f"Error in send_contact_email_and_notification: {str(e)}")

from django.utils.html import strip_tags

@receiver(post_save, sender=LoginHistory)
def login_notification(sender, instance, created, **kwargs):
    if not created:
        return
    
    try:
        user = instance.user
        try:
            preferences = user.notification_preferences
        except NotificationPreferences.DoesNotExist:
            return
        
        last_login = LoginHistory.objects.filter(user=user).exclude(id=instance.id).order_by("-timestamp").first()

        if last_login:
            is_new_device = instance.device != last_login.device
            is_new_location = instance.city != last_login.city or instance.country != last_login.country

            if is_new_device or is_new_location:
                message = f"New login detected on {instance.device} ({instance.operating_system}) from {instance.city}, {instance.country}."

                create_notification(
                    user=user,
                    notification_type="new_login",
                    message=message,
                    related_object=instance
                )
                
                if preferences.email_notifications:
                    try:
                        password_reset_url = f"{settings.SITE_URL}{reverse('password_reset')}"
                        contact_support_url = f"{settings.SITE_URL}{reverse('contact-us')}"

                        email_context = {
                            "user": user,
                            "city": instance.city or "Unknown",
                            "country": instance.country or "Unknown",
                            "device": instance.device or "Unknown Device",
                            "os": instance.operating_system or "Unknown OS",
                            "timestamp": instance.timestamp,
                            "reset_password_url": password_reset_url,
                            "support_url": contact_support_url,
                        }

                        html_message = render_to_string("user/email/new_login_alert.html", email_context)
                        
                        # Send email asynchronously - NO BLOCKING
                        send_email_async(
                            subject="New Login Alert",
                            html_message=html_message,
                            recipient_list=[user.email]
                        )
                    except Exception as e:
                        logger.error(f"Failed to send login alert email to {user.email}: {str(e)}")
    except Exception as e:
        logger.error(f"Error in login_notification signal: {str(e)}")

from django.contrib.auth import get_user_model
User = get_user_model()

@receiver(post_save, sender=UserProfile)
def user_profile_updated(sender, instance, created, **kwargs):
    if created:
        return
    
    try:
        user = instance.user
        create_notification(
            user=user,
            notification_type="user_update",
            message="Your profile has been updated!",
            related_object=instance
        )
    except Exception as e:
        logger.error(f"Error in user_profile_updated signal: {str(e)}")

from django.db.models.signals import pre_delete

@receiver(pre_delete, sender=User)
def send_account_deletion_email(sender, instance, **kwargs):
    try:
        try:
            preferences = instance.notification_preferences
            if not preferences.email_notifications:
                return
        except NotificationPreferences.DoesNotExist:
            return
        
        support_url = f"{settings.SITE_URL}{reverse('contact-us')}"

        context = {
            "user": instance,
            "support_url": support_url,
        }
        
        html_message = render_to_string("user/email/account_delete.html", context)
        
        # Send email asynchronously - NO BLOCKING
        send_email_async(
            subject="Your Account Has Been Deleted",
            html_message=html_message,
            recipient_list=[instance.email]
        )
    except Exception as e:
        logger.error(f"Error in send_account_deletion_email: {str(e)}")

@receiver(post_save, sender=Subscriber)
def send_subscription_notification(sender, instance, created, **kwargs):
    if not created:
        return
    
    try:
        email = instance.email
        user = User.objects.filter(email=email).first()  
        unsubscribe_link = f"{settings.SITE_URL}{reverse('unsubscribe', args=[instance.unsubscribe_token])}"

        html_message = render_to_string("user/email/subscription_email.html", {
            "unsubscribe_link": unsubscribe_link
        })
        
        # Send email asynchronously - NO BLOCKING
        send_email_async(
            subject="Newsletter Subscription Confirmation",
            html_message=html_message,
            recipient_list=[email],
            from_email=settings.EMAIL_HOST_USER
        )

        if user:
            create_notification(user, "subscription", "Thank you for subscribing to our newsletter!")

        instance.notified = True
        instance.save(update_fields=['notified'])
    except Exception as e:
        logger.error(f"Error in send_subscription_notification for {instance.email}: {str(e)}")

from django.db.models.signals import post_delete

@receiver(post_delete, sender=Subscriber)
def send_unsubscription_notification(sender, instance, **kwargs):
    try:
        email = instance.email
        user = User.objects.filter(email=email).first()  

        html_message = render_to_string("user/email/unsubscribe_confirmation.html", {"url_home": settings.SITE_URL})
        
        # Send email asynchronously - NO BLOCKING
        send_email_async(
            subject="Unsubscription Confirmation",
            html_message=html_message,
            recipient_list=[email],
            from_email=settings.EMAIL_HOST_USER
        )

        if user:
            try:
                preferences = user.notification_preferences
                if preferences and preferences.email_notifications:
                    create_notification(user, "unsubscription", "You have unsubscribed from our newsletter.")
            except NotificationPreferences.DoesNotExist:
                pass
    except Exception as e:
        logger.error(f"Error in send_unsubscription_notification: {str(e)}")