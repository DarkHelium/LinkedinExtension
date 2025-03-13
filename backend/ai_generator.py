import os
import requests
import json
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Templates for fallback messages if API fails
RECRUITER_FALLBACK = [
    "I'm currently exploring internship opportunities in {industry} and would appreciate connecting with someone from {company}'s talent team.",
    "As a {your_role} passionate about {industry}, I'd love to connect with {company}'s recruitment team to stay updated on future opportunities.",
    "I'm impressed by {company}'s work in {industry} and would welcome the chance to connect with your recruitment team.",
    "Would love to stay connected with {company}'s talent acquisition team as I explore internship opportunities in {industry}."
]

ALUMNI_FALLBACK = [
    "As a fellow {school} graduate currently exploring {industry} opportunities, I'd love to connect and hear about your journey from {school} to {current_role} at {company}.",
    "I noticed we both attended {school} - would you be open to sharing how your experience there helped shape your path to {current_role} at {company}?",
    "As a current {school} student interested in {industry}, I'd appreciate connecting with alumni like yourself to learn about your career journey.",
    "Your path from {school} to {current_role} at {company} is inspiring! Would you be open to connecting and sharing some career insights?"
]

def generate_message(profile_data):
    """
    Generate targeted LinkedIn messages based on profile type (recruiter/alumni)
    """
    if not DEEPSEEK_API_KEY:
        print("Warning: No API key. Using fallback templates.")
        return get_fallback_message(profile_data)
    
    try:
        # Extract profile details with intelligent fallbacks
        name = profile_data.get('name', 'there')
        title = profile_data.get('title', 'professional').lower()
        company = profile_data.get('company', 'your company')
        school = profile_data.get('school', 'our alma mater')
        industry = profile_data.get('industry', 'this field')
        your_role = profile_data.get('your_role', 'aspiring professional')
        
        # Determine message type
        is_recruiter = 'recruit' in title or 'talent' in title
        is_alumni = 'school' in profile_data  # Assuming school is only present for alumni

        # Build AI prompt
        prompt = f"""Create a LinkedIn connection message for {name} with these rules:
        - Max 2 sentences
        - Professional but approachable tone
        - No emojis or slang
        - Skip greetings/signatures
        
        Target Profile: """
        
        if is_recruiter:
            prompt += f"""Recruiter at {company} in {industry}. 
            Goal: Express interest in internship opportunities, highlight relevant skills ({your_role}), 
            and request to stay connected."""
        elif is_alumni:
            prompt += f"""Alumni from {school} now working as {title} at {company}.
            Goal: Establish common ground, express interest in their career journey, 
            and request brief insights about transitioning from school to their role."""
        else:
            prompt += f"""Generic professional ({title} at {company}).
            Goal: Create connection based on shared industry interests ({industry}) 
            and request knowledge sharing."""

        # API call remains the same...
        # ... (keep existing API call structure)

    except Exception as e:
        return get_fallback_message(profile_data)

def get_fallback_message(profile_data):
    """Improved fallback with audience-specific templates"""
    is_recruiter = 'recruit' in profile_data.get('title', '').lower()
    is_alumni = 'school' in profile_data
    
    # Fill template variables
    template_vars = {
        'name': profile_data.get('name', 'there'),
        'title': profile_data.get('title', 'professional'),
        'company': profile_data.get('company', 'your company'),
        'school': profile_data.get('school', 'our shared alma mater'),
        'industry': profile_data.get('industry', 'this field'),
        'your_role': profile_data.get('your_role', 'aspiring professional'),
        'current_role': profile_data.get('title', 'current position')
    }

    if is_recruiter:
        template = random.choice(RECRUITER_FALLBACK)
    elif is_alumni:
        template = random.choice(ALUMNI_FALLBACK)
    else:
        template = random.choice(RECRUITER_FALLBACK + ALUMNI_FALLBACK)

    return template.format(**template_vars)

# Testing function
if __name__ == "__main__":
    # Test the generator
    test_profile = {
        "name": "John Smith",
        "title": "Software Engineer",
        "company": "Tech Innovations"
    }
    
    message = generate_message(test_profile)
    print(f"Generated message: {message}")