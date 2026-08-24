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

    def _generate_viva_defense_qa(self, project_title: str, category: str) -> List[Dict[str, str]]:
        """
        Generates tailored IEEE-compliant viva defense questions and model answers for academic reviews.
        """
        common_qa = [
            {
                "question": f"What was the primary architectural motivation behind selecting Python Flask for '{project_title}'?",
                "answer": "Flask provides a lightweight WSGI micro-framework model with absolute structural flexibility, allowing rapid routing, modular blueprint configuration, and clean integration with PyMongo without heavy overhead."
            },
            {
                "question": "How does the application manage database persistence and connection safety?",
                "answer": "We utilize PyMongo connection clients bound with Flask's application teardown context ('app.teardown_appcontext'), ensuring database sockets close correctly after request handling to prevent connection leaks."
            },
            {
                "question": "How are user passwords and sensitive credentials secured within the system?",
                "answer": "Passwords are never stored in plain text. We use Werkzeug security hashing ('generate_password_hash' and 'check_password_hash') using secure salt algorithms."
            }
        ]

        if "Data Science" in category or "ML" in category or "Machine Learning" in project_title:
            common_qa.append({
                "question": "How is the machine learning model integrated with the backend web pipeline?",
                "answer": "Trained predictive artifacts (.pkl or joblib files) are loaded into memory during app initialization, exposing a clean inference route that accepts form parameters and returns real-time predictions to Jinja templates."
            })
        else:
            common_qa.append({
                "question": "How does role-based access control (RBAC) restrict unauthorized endpoint access?",
                "answer": "We use custom decorator wrappers (e.g., '@login_required' and '@role_required') that inspect session tokens before executing route logic, returning 403 authorization rejections if privilege levels mismatch."
            })

        return common_qa

    def generate_scope(self, project_title: str, category: str, requirements_text: str) -> Dict[str, Any]:
        """
        Generates a comprehensive scope document with architecture recommendations,
        timeline estimates, pricing options, and IEEE academic viva defense Q&A.
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
        viva_qa = self._generate_viva_defense_qa(project_title, category)

        return {
            "project_title": project_title,
            "category": category,
            "estimated_delivery_days": total_days,
            "estimated_cost_inr": base_price,
            "recommended_stack": recommended_stack,
            "scope_modules": recommended_modules,
            "database_collections_suggested": ["users", "projects", "inquiries", "activity_logs"],
            "academic_viva_defense": viva_qa,
            "summary": f"Estimated delivery in {total_days} days with {len(recommended_modules)} primary modules and complete IEEE viva prep."
        }


def generate_scope_estimate(project_title: str, category: str, requirements_text: str) -> Dict[str, Any]:
    """
    Public entry point helper for generating scope estimates.
    """
    generator = ScopeGenerator()
    return generator.generate_scope(project_title, category, requirements_text)