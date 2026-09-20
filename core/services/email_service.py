import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def _send_email(subject, template_name, context, recipient_list):
        try:
            html_content = render_to_string(f'emails/{template_name}.html', context)
            text_content = render_to_string(f'emails/{template_name}.txt', context)
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_list
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            logger.info(f"Email '{subject}' sent to {recipient_list}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email '{subject}' to {recipient_list}: {str(e)}")
            return False

    @staticmethod
    def send_welcome_email(user):
        context = {'user': user}
        return EmailService._send_email(
            subject="Welcome to AEON",
            template_name="welcome",
            context=context,
            recipient_list=[user.email]
        )

    @staticmethod
    def send_order_confirmation_email(order):
        context = {'order': order, 'user': order.user}
        return EmailService._send_email(
            subject=f"Order Confirmation - {order.order_number}",
            template_name="order_confirmation",
            context=context,
            recipient_list=[order.user.email]
        )
