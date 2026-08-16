"""
DAV Cloud Solutions - DAV AI Internal Intelligence Engine
Founder: V Akhil
"""

import os
from google import genai

# Initialize GenAI Client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))

MODEL_NAME = "gemini-2.5-flash"


def analyze_inquiry_lead(inquiry_data: dict) -> str:
    """Live AI Agent that scores leads, evaluates tech feasibility, and suggests pricing."""
    prompt = f"""
    You are the Senior Technical Architect at DAV Cloud Solutions assisting Founder V Akhil.
    Analyze the following incoming client/student project inquiry:

    Client Name: {inquiry_data.get('name', 'N/A')}
    Category: {inquiry_data.get('user_category', 'General')}
    Project Name: {inquiry_data.get('project_name', 'N/A')}
    Message/Scope: {inquiry_data.get('message', 'N/A')}

    Provide a concise technical assessment in Markdown format with:
    1. **Lead Score & Feasibility**: (High / Medium / Low) with brief reasoning.
    2. **Recommended Tech Stack**: (e.g., Flask, MongoDB, Scikit-Learn, React, etc.)
    3. **Estimated Delivery Timeline**: (e.g., 3-5 days, 1-2 weeks)
    4. **Suggested Budget / Price Quote (₹)**: (e.g., ₹3,500 - ₹6,000)
    5. **Next Action for Founder**: Exactly what to message the client on WhatsApp/Email.
    """
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        return response.text if response.text else "DAV AI Error: Empty response"
    except Exception as e:
        return f"DAV AI Error: {str(e)}"


def generate_project_scope(title: str, category: str, requirements: str) -> str:
    """Live AI Agent that generates project SRS outline, database schema suggestions, and viva defense topics."""
    prompt = f"""
    You are the Lead Systems Architect at DAV Cloud Solutions.
    Generate a professional technical project scope and delivery blueprint for:

    - Project Title: {title}
    - Domain Track: {category}
    - Client Requirements: {requirements}

    Provide a structured blueprint including:
    1. **System Architecture Overview** (Frontend, Backend, Database layer)
    2. **Core Functional Modules** (List 4-6 key features)
    3. **Suggested MongoDB Collections & Schema**
    4. **Top 3 Viva Defense / Seminar Questions** that professors will ask the student.
    """
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        return response.text if response.text else "DAV AI Error: Empty response"
    except Exception as e:
        return f"DAV AI Error: {str(e)}"


def audit_code_snippet(code_or_requirements: str) -> str:
    """Live AI Agent that audits Python/Flask/ML code or architecture for vulnerabilities and optimizations."""
    prompt = f"""
    You are the Lead Code Reviewer at DAV Cloud Solutions.
    Perform an automated security, efficiency, and cleanliness audit on the following code or system logic:

    ```python
    {code_or_requirements}
    ```

    Evaluate and return:
    1. **Security Vulnerabilities** (SQL/NoSQL injection, auth checks, secret leaks)
    2. **Performance Bottlenecks** (redundant queries, unindexed lookups)
    3. **Production Recommendations** (cleaner Flask routes, error handling)
    """
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        return response.text if response.text else "DAV AI Error: Empty response"
    except Exception as e:
        return f"DAV AI Error: {str(e)}"