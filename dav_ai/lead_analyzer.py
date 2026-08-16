"""
DAV Cloud Solutions - Private Internal AI Core (dav_ai)
Module: lead_analyzer.py
Founder: Akhil V & Core Engineering Team

Automated inquiry analyzer for evaluating Web3Forms guest messages,
scoring lead quality, detecting tech stack signals, and categorizing requirements.
"""

import re
from typing import Dict, List, Any


class LeadAnalyzer:
    """
    Inquiry & Lead Scoring Agent for DAV Cloud Solutions.
    """

    def __init__(self):
        # Keyword triggers for category detection
        self.categories = {
            "Student Academic Project": [
                "academic", "student", "final year", "mini project", "ieee", 
                "college", "university", "seminar", "viva", "diploma", "mca"
            ],
            "Startup MVP Architecture": [
                "mvp", "startup", "prototype", "investor", "saas", 
                "platform", "scale", "funding", "launch"
            ],
            "Small Business Web Portal": [
                "small business", "website", "catalog", "directory", "local", 
                "inventory", "gst", "billing", "shop", "ecommerce"
            ]
        }

        # Recognized technical stack mentions
        self.tech_keywords = [
            "python", "flask", "django", "mongodb", "sqlite", "javascript", 
            "html", "css", "api", "rest", "ml", "machine learning", "bootstrap"
        ]

    def analyze_message(self, name: str, email: str, message_text: str) -> Dict[str, Any]:
        """
        Analyzes raw message text to score lead priority, identify project domain,
        and extract technical requirements.
        """
        text_lower = message_text.lower()
        word_count = len(message_text.split())

        # 1. Category Detection
        detected_category = "General Software Inquiry"
        category_scores = {}

        for category, keywords in self.categories.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > 0:
                category_scores[category] = matches

        if category_scores:
            detected_category = max(category_scores, key=lambda k: category_scores[k])

        # 2. Tech Stack Signal Extraction
        detected_stack = [tech for tech in self.tech_keywords if tech in text_lower]

        # 3. Lead Quality Score Calculation (Base 100)
        score = 40  # Base initial score

        # Detail length signal
        if word_count >= 50:
            score += 25
        elif word_count >= 20:
            score += 15

        # Domain/Tech clarity signal
        if len(detected_stack) >= 2:
            score += 20
        elif len(detected_stack) == 1:
            score += 10

        # High priority indicators (urgency/budget)
        if any(w in text_lower for w in ["urgent", "deadline", "budget", "quote", "hire"]):
            score += 15

        # 4. Lead Priority Classification
        if score >= 75:
            priority = "HIGH"
        elif score >= 50:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        return {
            "client_name": name,
            "client_email": email,
            "detected_category": detected_category,
            "detected_stack": detected_stack if detected_stack else ["Python/Flask (Recommended)"],
            "lead_score": min(100, score),
            "priority": priority,
            "word_count": word_count,
            "summary": f"{priority} priority inquiry for {detected_category} with score {score}/100."
        }


def analyze_inquiry(name: str, email: str, message_text: str) -> Dict[str, Any]:
    """
    Public entry point helper for analyzing Web3Forms inquiry leads.
    """
    analyzer = LeadAnalyzer()
    return analyzer.analyze_message(name, email, message_text)