"""
DAV Cloud Solutions - Private Internal AI Core (dav_ai)
Module: comms_assistant.py
Founder: Akhil V & Core Engineering Team

Automated communication assistant for generating tailored email drafts,
project status updates, deliverable delivery notices, and lead follow-ups.
"""

from typing import Dict, Any, Optional


class CommsAssistant:
    """
    Client Communication & Response Generator for DAV Cloud Solutions.
    """

    def __init__(self, founder_name: str = "Akhil V", company_name: str = "DAV Cloud Solutions"):
        self.founder_name = founder_name
        self.company_name = company_name

    def generate_lead_response(self, client_name: str, inquiry_type: str, estimated_timeframe: str = "3–5 business days") -> Dict[str, str]:
        """
        Generates an introductory email response draft for incoming client inquiries.
        """
        subject = f"Response to Your {inquiry_type} Inquiry | {self.company_name}"
        
        body = f"""Dear {client_name},

Thank you for reaching out to {self.company_name} regarding your {inquiry_type.lower()} request.

We have received your message and conducted an initial review of your requirements. Based on our stack capabilities (Python Flask, MongoDB, custom web portals, and MVP builds), we are confident in delivering a robust solution tailored to your operational goals.

Our technical lead will finish assessing your project scope within {estimated_timeframe}. In the meantime, feel free to log in to your portal or review our verified client directory to see similar deployment benchmarks.

Best regards,

{self.founder_name}
Founder & Lead Architect
{self.company_name}
contact@davcloudsolutions.com
"""
        return {"subject": subject, "body": body}

    def generate_deliverable_notice(self, client_name: str, project_title: str, deliverable_url: str) -> Dict[str, str]:
        """
        Generates a delivery notice email draft when a staging URL or deliverable link is updated.
        """
        subject = f"Deliverable Ready: {project_title} | {self.company_name}"

        body = f"""Hello {client_name},

Great news! The latest milestone build for "{project_title}" is ready for your review.

You can access your live staging sandbox and deliverables directly via the link below:
{deliverable_url}

Please test the feature workflows and database connections. If you have any feedback or requested modifications, submit a priority ticket via your client dashboard.

Best regards,

{self.founder_name}
{self.company_name}
"""
        return {"subject": subject, "body": body}


def generate_client_response(
    template_type: str,
    client_name: str,
    project_or_inquiry: str,
    extra_link: Optional[str] = None
) -> Dict[str, str]:
    """
    Public entry point helper for generating communication drafts.
    """
    assistant = CommsAssistant()

    if template_type.lower() in ["deliverable", "notice", "staging"]:
        return assistant.generate_deliverable_notice(
            client_name=client_name,
            project_title=project_or_inquiry,
            deliverable_url=extra_link or "https://davcloudsolutions.com/dashboard"
        )
    else:
        return assistant.generate_lead_response(
            client_name=client_name,
            inquiry_type=project_or_inquiry
        )