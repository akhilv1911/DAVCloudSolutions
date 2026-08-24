"""
DAV Cloud Solutions - Private Internal AI Core (dav_ai)
Module: code_auditor.py
Founder: Akhil V & Core Engineering Team

Automated code auditor for scanning Python Flask routes, MongoDB queries,
and frontend JavaScript scripts for security, performance, and best practices.
"""

import re
import ast
from typing import Dict, List, Any


class CodeAuditor:
    """
    Automated Code Quality & Security Inspector for DAV Cloud Solutions.
    """

    def __init__(self):
        # Known security vulnerability patterns with automated remediation hints
        self.security_patterns = [
            {
                "id": "SEC001",
                "name": "Hardcoded Secret / API Key",
                "pattern": r"(?i)(secret_key|api_key|password|auth_token)\s*=\s*['\"](?!.*(?:os\.environ|config))[^'\"]{8,}['\"]",
                "severity": "HIGH",
                "recommendation": "Move secrets into environment variables (.env) or App Config using os.environ.get()."
            },
            {
                "id": "SEC002",
                "name": "Potential MongoDB / NoSQL Injection",
                "pattern": r"\.find\(\s*\{\s*['\"][^'\"]+['\"]\s*:\s*request\.(args|form|json)",
                "severity": "HIGH",
                "recommendation": "Sanitize and cast request parameters (e.g. str(), int()) before querying PyMongo collections."
            },
            {
                "id": "SEC003",
                "name": "Debug Mode Enabled in Code",
                "pattern": r"app\.run\([^)]*debug\s*=\s*True",
                "severity": "MEDIUM",
                "recommendation": "Ensure debug=False or use environment config in production deployments."
            },
            {
                "id": "SEC004",
                "name": "Insecure Evaluation (eval/exec)",
                "pattern": r"\b(eval|exec)\s*\(",
                "severity": "CRITICAL",
                "recommendation": "Avoid using eval() or exec() as it allows arbitrary remote code execution."
            },
            {
                "id": "SEC005",
                "name": "Plain Text Password Comparison",
                "pattern": r"user\['password'\]\s*==\s*request\.",
                "severity": "CRITICAL",
                "recommendation": "Use Werkzeug generate_password_hash() and check_password_hash() for secure credentials."
            }
        ]

    def audit_python_code(self, code_contents: str) -> Dict[str, Any]:
        """
        Scans a Python source code string for syntax errors, security flaws, and best practices.
        """
        findings: List[Dict[str, str]] = []
        syntax_valid = True
        syntax_error = None

        # 1. AST Syntax Tree Validation
        try:
            ast.parse(code_contents)
        except SyntaxError as se:
            syntax_valid = False
            syntax_error = f"Line {se.lineno}: {se.msg}"
            findings.append({
                "id": "SYN001",
                "name": "Python Syntax Error",
                "severity": "CRITICAL",
                "details": syntax_error,
                "recommendation": "Fix syntax error before deploying or running."
            })

        # 2. Pattern Matching Security Audit
        lines = code_contents.splitlines()
        for idx, line in enumerate(lines, 1):
            for sp in self.security_patterns:
                if re.search(sp["pattern"], line):
                    findings.append({
                        "id": sp["id"],
                        "name": sp["name"],
                        "severity": sp["severity"],
                        "details": f"Line {idx}: {line.strip()}",
                        "recommendation": sp["recommendation"]
                    })

        # 3. Best Practice & Best Standards Check
        if "teardown_appcontext" not in code_contents and "close_db_connection" in code_contents:
            findings.append({
                "id": "PERF001",
                "name": "Unregistered DB Teardown",
                "severity": "LOW",
                "details": "Database connection function exists but may not be registered in teardown_appcontext.",
                "recommendation": "Register app.teardown_appcontext(close_db_connection) in app.py."
            })

        # Score Calculation (100 Base)
        penalty = sum(
            30 if f["severity"] == "CRITICAL" else
            20 if f["severity"] == "HIGH" else
            10 if f["severity"] == "MEDIUM" else 5
            for f in findings
        )
        quality_score = max(0, 100 - penalty)

        return {
            "syntax_valid": syntax_valid,
            "quality_score": quality_score,
            "status": "APPROVED" if quality_score >= 80 and syntax_valid else "NEEDS_REVISION",
            "findings_count": len(findings),
            "findings": findings
        }


def audit_codebase(code_contents: str) -> Dict[str, Any]:
    """
    Public entry point helper for auditing code snippets or file strings.
    """
    auditor = CodeAuditor()
    return auditor.audit_python_code(code_contents)