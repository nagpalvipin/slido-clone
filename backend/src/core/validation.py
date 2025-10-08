"""
Validation utilities for slido-clone.

Provides validation functions for user input, codes, and data formats.
"""

import re
from typing import Optional

# Simplified host code pattern: 3-30 alphanumeric characters (case-insensitive)
# Backend will auto-prefix with 'host_' if not present
HOST_CODE_PATTERN = re.compile(r'^[a-z0-9_-]{3,30}$', re.IGNORECASE)


def validate_host_code(code: str) -> bool:
    """
    Validate host code format (simplified).

    Host codes must:
    - Be 3-30 characters long
    - Contain only alphanumeric characters, hyphens, or underscores
    - Backend will automatically prefix with 'host_' if not present

    Args:
        code: The host code to validate

    Returns:
        True if the code is valid, False otherwise

    Examples:
        >>> validate_host_code('myteam')
        True
        >>> validate_host_code('my-team-2025')
        True
        >>> validate_host_code('ab')  # too short
        False
        >>> validate_host_code('a' * 31)  # too long
        False
    """
    if not code or not isinstance(code, str):
        return False

    cleaned = code.strip()
    if not cleaned:
        return False
        
    # Remove 'host_' prefix if present for validation
    if cleaned.lower().startswith('host_'):
        cleaned = cleaned[5:]
    
    return bool(HOST_CODE_PATTERN.match(cleaned))


def validate_question_text(text: str) -> tuple[bool, Optional[str]]:
    """
    Validate question text content.

    Requirements:
    - Must be between 1 and 1000 characters (after trimming)
    - Cannot be empty or whitespace-only
    - Supports Unicode characters

    Args:
        text: The question text to validate

    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if valid
        - (False, error_message) if invalid

    Examples:
        >>> validate_question_text('How does this work?')
        (True, None)
        >>> validate_question_text('')
        (False, 'Question text must be between 1 and 1000 characters')
        >>> validate_question_text('   ')
        (False, 'Question text must be between 1 and 1000 characters')
        >>> validate_question_text('a' * 1001)
        (False, 'Question text must be between 1 and 1000 characters')
    """
    if not text or not isinstance(text, str):
        return False, "Question text must be between 1 and 1000 characters"

    trimmed = text.strip()

    if not trimmed:
        return False, "Question text must be between 1 and 1000 characters"

    if len(trimmed) < 1 or len(trimmed) > 1000:
        return False, "Question text must be between 1 and 1000 characters"

    return True, None


def sanitize_host_code(code: str) -> str:
    """
    Sanitize host code for database storage.

    - Strips whitespace
    - Converts to lowercase
    - Auto-prefixes with 'host_' if not present

    Args:
        code: The host code to sanitize

    Returns:
        Sanitized host code with 'host_' prefix

    Examples:
        >>> sanitize_host_code('  myteam  ')
        'host_myteam'
        >>> sanitize_host_code('MyTeam2025')
        'host_myteam2025'
        >>> sanitize_host_code('host_existing')
        'host_existing'
    """
    if not code:
        return ""
    
    cleaned = code.strip().lower()
    
    # Add 'host_' prefix if not present
    if not cleaned.startswith('host_'):
        cleaned = f'host_{cleaned}'
    
    return cleaned
