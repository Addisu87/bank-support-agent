import os
import logfire
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from jinja2 import Environment, FileSystemLoader, select_autoescape
from app.core.config import settings

def get_email_config():
    return ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_STARTTLS=settings.MAIL_STARTTLS,
        MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
        USE_CREDENTIALS=settings.USE_CREDENTIALS,
        VALIDATE_CERTS=settings.VALIDATE_CERTS
    )

# Setup Jinja2 environment
template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape(['html', 'xml'])
)

# Template configuration
TEMPLATE_CONFIG = {
    "user_welcome": {
        "template": "email/user_welcome.html",
        "subject": "Welcome to Our Bank - Account Created Successfully"
    },
    "account_created": {
        "template": "email/account_created.html",
        "subject": "New Account Created - {account_number}"
    },
    "transaction_alert": {
        "template": "email/transaction_alert.html",
        "subject": "Transaction Alert - ${amount} {transaction_type}"
    },
    "card_created": {
        "template": "email/card_created.html",
        "subject": "New {card_type} Card Issued"
    },
    "custom": {
        "template": "email/custom.html",
        "subject": "{subject}"
    }
}

async def send_email(to_email: str, template_type: str, template_data: dict):
    """Send email using Jinja2 template - always called as background task"""
    with logfire.span("send_email", 
                     email=to_email, 
                     template_type=template_type,
                     email_domain=to_email.split('@')[-1]) as span:
        try:
            # Log configuration details (without password)
            logfire.info(
                "Email configuration details",
                mail_server=settings.MAIL_SERVER,
                mail_port=settings.MAIL_PORT,
                mail_from=settings.MAIL_FROM,
                mail_username=settings.MAIL_USERNAME,
                use_starttls=settings.MAIL_STARTTLS,
                use_ssl_tls=settings.MAIL_SSL_TLS,
                _tags=["email", "config", "debug"]
            )
            
            # Add template data context
            safe_template_data = {
                k: v for k, v in template_data.items() 
                if not any(sensitive in k.lower() for sensitive in ['password', 'token', 'secret'])
            }
            span.set_attribute("template_data", safe_template_data)
            
            conf = get_email_config()
            fm = FastMail(conf)
            
            # Get template configuration
            config = TEMPLATE_CONFIG.get(template_type, TEMPLATE_CONFIG["custom"])
            
            # Render subject
            subject = config["subject"].format(**template_data)
            
            # Render HTML content using Jinja2
            template = env.get_template(config["template"])
            html_content = template.render(**template_data)
            
            message = MessageSchema(
                subject=subject,
                recipients=[to_email],
                body=html_content,
                subtype="html"
            )
            
            logfire.info("Attempting to send email message...")
            await fm.send_message(message)
            
            # Log successful email sending
            logfire.info(
                "Email sent successfully!",
                to_email=to_email,
                template_type=template_type,
                subject=subject,
                _tags=["email", "notification", "success"]
            )
            
            return True
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            
            # Log detailed error information
            logfire.error(
                "Failed to send email - SMTP Connection Error",
                to_email=to_email,
                template_type=template_type,
                error_message=str(e),
                error_type=type(e).__name__,
                mail_server=settings.MAIL_SERVER,
                mail_port=settings.MAIL_PORT,
                full_traceback=error_traceback,
                _tags=["email", "error", "failure", "smtp"]
            )
            
            return False