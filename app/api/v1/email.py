import logfire
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import Dict, Any
from app.schemas.email import EmailRequest
from app.services.email_service import send_email
from app.schemas.email import EmailRequest

router = APIRouter(tags=["email"])

@router.post("/")
async def send_email_background(request: EmailRequest, background_tasks: BackgroundTasks):
    """Send email to user - always uses background tasks"""
    with logfire.span("email_api_request",
                     to_email=request.to_email,
                     template_type=request.template_type):
        # Log the API request
        logfire.info(
            "Email API request received",
            to_email=request.to_email,
            template_type=request.template_type,
            _tags=["api", "email", "request"]
        )
        
        # Add to background tasks
        background_tasks.add_task(
            send_email,
            request.to_email,
            request.template_type,
            request.template_data
        )
        
        # Log successful queueing
        logfire.info(
            "Email queued for background processing",
            to_email=request.to_email,
            template_type=request.template_type,
            _tags=["api", "email", "queued"]
        )
        
        return {
            "message": "Email queued for sending",
            "to_email": request.to_email,
            "template_type": request.template_type
        }
        
        
@router.post("/test-send")
async def test_email_send(background_tasks: BackgroundTasks):
    """Test email sending with simple message"""
    background_tasks.add_task(
        send_email,
        "addisu.haile@yahoo.com",  # Send to yourself for testing
        "custom",
        {
            "subject": "Test Email from Bank System",
            "message": "This is a test email to verify the email system is working correctly."
        }
    )
    
    return {"message": "Test email queued for sending"}