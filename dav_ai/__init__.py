"""
DAV Cloud Solutions - Private Internal AI Core (dav_ai)
Founder: Akhil V & Core Engineering Team

This module houses automated background agents for:
1. Lead Analysis (Web3Forms inquiry scoring)
2. Scope & Cost Generation (Flask/MongoDB project estimates)
3. Code Audit & Security Inspection
4. Automated Client Communication
"""

from .lead_analyzer import analyze_inquiry
from .scope_generator import generate_scope_estimate
from .code_auditor import audit_codebase
from .comms_assistant import generate_client_response

__all__ = [
    'analyze_inquiry',
    'generate_scope_estimate',
    'audit_codebase',
    'generate_client_response'
]