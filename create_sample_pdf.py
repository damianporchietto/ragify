#!/usr/bin/env python3
"""
Script to generate a sample PDF document about data security best practices
for use with the Ragify framework.
"""

try:
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
    from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
    from reportlab.lib import colors
except ImportError:
    print("ReportLab not installed. Please install it with: pip install reportlab")
    exit(1)

import os
from pathlib import Path

# Ensure the TECH directory exists
docs_dir = Path(__file__).resolve().parent / 'docs' / 'TECH'
docs_dir.mkdir(exist_ok=True)

# Define the output PDF file
pdf_file = docs_dir / 'data_security_best_practices.pdf'

def create_pdf():
    """Create a sample PDF file about data security best practices."""
    doc = SimpleDocTemplate(
        str(pdf_file),
        pagesize=LETTER,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Create styles
    styles = getSampleStyleSheet()
    
    # Modify existing styles instead of adding new ones with the same name
    styles['Title'].alignment = TA_CENTER
    styles['Title'].textColor = colors.darkblue
    styles['Title'].fontSize = 20
    styles['Title'].leading = 24
    styles['Title'].spaceBefore = 10
    styles['Title'].spaceAfter = 20
    
    # Add custom styles
    styles.add(ParagraphStyle(
        name='CustomJustify',
        parent=styles['Normal'],
        alignment=TA_JUSTIFY,
        fontSize=10,
        leading=12,
        spaceBefore=0,
        spaceAfter=10
    ))
    
    styles.add(ParagraphStyle(
        name='CustomHeading1',
        parent=styles['Heading1'],
        alignment=TA_JUSTIFY,
        fontSize=14,
        leading=18,
        spaceBefore=12,
        spaceAfter=6,
        textColor=colors.darkblue
    ))
    
    # Content for the PDF
    content = []
    
    # Title
    content.append(Paragraph("Data Security Best Practices", styles['Title']))
    content.append(Spacer(1, 0.2 * inch))
    
    # Introduction
    content.append(Paragraph(
        "This document outlines essential best practices for maintaining data security in organizations. "
        "Implementing these recommendations can help protect sensitive information and prevent data breaches.",
        styles['CustomJustify']
    ))
    content.append(Spacer(1, 0.2 * inch))
    
    # Section 1: Password Security
    content.append(Paragraph("1. Password Security", styles['CustomHeading1']))
    
    password_practices = [
        "Use strong, unique passwords for each account (minimum 12 characters with a mix of uppercase, lowercase, numbers, and symbols)",
        "Implement multi-factor authentication (MFA) wherever possible",
        "Use a password manager to generate and store complex passwords",
        "Change default passwords immediately on new systems or devices",
        "Implement a password rotation policy for critical systems"
    ]
    
    password_items = [ListItem(Paragraph(item, styles['CustomJustify'])) for item in password_practices]
    content.append(ListFlowable(password_items, bulletType='bullet', start='•'))
    content.append(Spacer(1, 0.2 * inch))
    
    # Section 2: Data Encryption
    content.append(Paragraph("2. Data Encryption", styles['CustomHeading1']))
    
    encryption_practices = [
        "Encrypt sensitive data both at rest and in transit",
        "Use strong encryption algorithms (AES-256, RSA-2048 or higher)",
        "Implement SSL/TLS for all web applications and services",
        "Use VPN for remote access to company resources",
        "Encrypt backup data and storage media"
    ]
    
    encryption_items = [ListItem(Paragraph(item, styles['CustomJustify'])) for item in encryption_practices]
    content.append(ListFlowable(encryption_items, bulletType='bullet', start='•'))
    content.append(Spacer(1, 0.2 * inch))
    
    # Section 3: Access Control
    content.append(Paragraph("3. Access Control", styles['CustomHeading1']))
    
    access_practices = [
        "Implement the principle of least privilege (users should only have access to what they need)",
        "Regularly audit user access rights and permissions",
        "Revoke access immediately when employees leave the organization",
        "Implement role-based access control (RBAC)",
        "Use network segmentation to limit access to sensitive data"
    ]
    
    access_items = [ListItem(Paragraph(item, styles['CustomJustify'])) for item in access_practices]
    content.append(ListFlowable(access_items, bulletType='bullet', start='•'))
    content.append(Spacer(1, 0.2 * inch))
    
    # Section 4: Software and Systems
    content.append(Paragraph("4. Software and Systems", styles['CustomHeading1']))
    
    software_practices = [
        "Keep all software, operating systems, and firmware up-to-date with security patches",
        "Use antivirus/anti-malware software and keep definitions updated",
        "Disable unnecessary services and ports",
        "Implement a secure software development lifecycle (SDLC)",
        "Conduct regular vulnerability assessments and penetration testing"
    ]
    
    software_items = [ListItem(Paragraph(item, styles['CustomJustify'])) for item in software_practices]
    content.append(ListFlowable(software_items, bulletType='bullet', start='•'))
    content.append(Spacer(1, 0.2 * inch))
    
    # Section 5: Employee Training
    content.append(Paragraph("5. Employee Training", styles['CustomHeading1']))
    
    training_practices = [
        "Conduct regular security awareness training for all employees",
        "Train employees to recognize phishing and social engineering attempts",
        "Create a culture of security consciousness",
        "Establish clear procedures for reporting security incidents",
        "Provide specialized training for IT and security staff"
    ]
    
    training_items = [ListItem(Paragraph(item, styles['CustomJustify'])) for item in training_practices]
    content.append(ListFlowable(training_items, bulletType='bullet', start='•'))
    
    # Build the PDF
    doc.build(content)
    
    print(f"Sample PDF created: {pdf_file}")

if __name__ == "__main__":
    create_pdf() 