# user/email_utils.py
import threading
import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

logger = logging.getLogger(__name__)

class AsyncEmailThread(threading.Thread):
    """Background thread for sending emails asynchronously"""
    
    def __init__(self, subject, html_message, recipient_list, from_email=None, plain_message=None, **kwargs):
        self.subject = subject
        self.html_message = html_message
        self.recipient_list = recipient_list
        self.from_email = from_email or settings.DEFAULT_FROM_EMAIL
        self.plain_message = plain_message
        self.kwargs = kwargs
        threading.Thread.__init__(self)
        self.daemon = True
    
    def run(self):
        try:
            if not self.recipient_list:
                logger.warning("No recipients provided for email")
                return
            
            # Check if email is configured
            if not settings.EMAIL_HOST or not settings.EMAIL_HOST_USER:
                logger.warning("Email not configured properly. Skipping email send.")
                return
            
            if self.plain_message is None:
                self.plain_message = strip_tags(self.html_message)
            
            # Create and send email
            email = EmailMultiAlternatives(
                subject=self.subject,
                body=self.plain_message,
                from_email=self.from_email,
                to=self.recipient_list,
            )
            email.attach_alternative(self.html_message, "text/html")
            email.send(fail_silently=False)
            
            logger.info(f"Email sent successfully to {', '.join(self.recipient_list)}")
            
        except Exception as e:
            logger.error(f"Failed to send email to {', '.join(self.recipient_list)}: {str(e)}")

def send_email_async(subject, html_message, recipient_list, from_email=None, plain_message=None, **kwargs):
    """Send email asynchronously using background thread"""
    try:
        thread = AsyncEmailThread(subject, html_message, recipient_list, from_email, plain_message, **kwargs)
        thread.start()
        logger.debug(f"Async email queued for {', '.join(recipient_list)}")
        return thread
    except Exception as e:
        logger.error(f"Failed to queue async email: {str(e)}")
        return None