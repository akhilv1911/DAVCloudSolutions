"""
DAV Cloud Solutions - Private Internal AI Core (dav_ai)
Module: scope_generator.py
Founder: Akhil V & Core Engineering Team

Automated scope generator for estimating timelines, system architecture,
database schema requirements, and costs for Flask/Django + MongoDB/SQLite projects.
"""

from typing import Dict, List, Any


class ScopeGenerator:
    """
    Automated System Architecture & Cost Estimator for DAV Cloud Solutions.
    """

    def __init__(self):
        # Base pricing and timeline rates (in INR / USD reference)
        self.category_defaults = {
            "Student Academic Project": {
                "base_days": 4,
                "base_price_inr": 3500,
                "default_stack": ["Python", "Flask/Django", "SQLite/MongoDB", "HTML5/CSS3/JS"],
                "modules": ["User Authentication", "Role Dashboard", "CRUD Operations", "PDF/Report Generator"]
            },
            "Small Business Web Portal": {
                "base_days": 8,
                "base_price_inr": 12000,
                "default_stack": ["Python", "Flask", "MongoDB Atlas", "Jinja2 Templates", "CSS Glassmorphism"],
                "modules": ["Catalog Directory", "Inquiry Forms", "Admin Panel", "Role-based Access"]
            },
            "Startup MVP Architecture": {
                "base_days": 14,
                "base_price_inr": 25000,
                "default_stack": ["Python", "Flask/Django", "MongoDB", "REST APIs", "Staging Deployment"],
                "modules": ["Multi-tenant Auth", "API Suite", "Staging Preview Sandbox", "Database Indexing", "NDA Protection"]
            }
        }

    def generate_scope(self, project_title: str, category: str, requirements_text: str) -> Dict[str, Any]:
        """
        Generates a comprehensive scope document with architecture recommendations,
        timeline estimates, and pricing options.
        """
        text_lower = requirements_text.lower()
        
        # Match category config or fall back to Small Business
        config = self.category_defaults.get(category, self.category_defaults["Small Business Web Portal"])

        base_days = config["base_days"]
        base_price = config["base_price_inr"]
        recommended_modules = list(config["modules"])
        recommended_stack = list(config["default_stack"])

        # Detect Complexity Multipliers
        complexity_additions = 0

        if any(term in text_lower for term in ["payment", "razorpay", "stripe", "billing"]):
            recommended_modules.append("Payment Gateway Integration")
            complexity_additions += 2
            base_price += 4000

        if any(term in text_lower for term in ["ml", "machine learning", "prediction", "ai"]):
            recommended_modules.append("Machine Learning Model API")
            complexity_additions += 3
            base_price += 6000

        if any(term in text_lower for term in ["otp", "sms", "email notification", "verification"]):
            recommended_modules.append("Automated Mailer & OTP Verification")
            complexity_additions += 1
            base_price += 2000

        total_days = base_days + complexity_additions

        return {
            "project_title": project_title,
            "category": category,
            "estimated_delivery_days": total_days,
            "estimated_cost_inr": base_price,
            "recommended_stack": recommended_stack,
            "scope_modules": recommended_modules,
            "database_collections_suggested": ["users", "projects", "inquiries", "activity_logs"],
            "summary": f"Estimated delivery in {total_days} days with {len(recommended_modules)} primary modules."
        }


def generate_scope_estimate(project_title: str, category: str, requirements_text: str) -> Dict[str, Any]:
    """
    Public entry point helper for generating scope estimates.
    """
    generator = ScopeGenerator()
    return generator.generate_scope(project_title, category, requirements_text)