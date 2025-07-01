#!/usr/bin/env python3
"""
Simple script to generate a secure API key for the Rival Agent.
"""

import secrets
import string

def generate_api_key(length=32):
    """Generate a secure random API key."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    api_key = generate_api_key()
    print("Generated secure API key:")
    print(f"RIVAL_API_KEY={api_key}")
    print()
    print("Add this to your .env file or set as an environment variable:")
    print(f"export RIVAL_API_KEY={api_key}")
    print()
    print("To enable authentication, also set:")
    print("export RIVAL_USE_AUTH=true")
