"""
Security utilities for authentication and validation.

Handles host code validation and session management.
"""

import re
from typing import Optional
from fastapi import HTTPException, status


class SecurityUtils:
    """Security utilities for authentication and validation."""
    
    @staticmethod
    def validate_host_code(host_code: str) -> bool:
        """Validate host code format."""
        if not host_code:
            return False
        
        # Host code should start with 'host_' and be at least 17 characters total
        pattern = r'^host_[a-z0-9]{12}$'
        return bool(re.match(pattern, host_code))
    
    @staticmethod
    def validate_slug(slug: str) -> bool:
        """Validate event slug format."""
        if not slug:
            return False
        
        # Slug: 3-50 chars, alphanumeric + hyphens only
        if len(slug) < 3 or len(slug) > 50:
            return False
        
        pattern = r'^[a-z0-9-]+$'
        return bool(re.match(pattern, slug))
    
    @staticmethod
    def validate_title(title: str) -> bool:
        """Validate event title."""
        if not title:
            return False
        
        # Title: 1-200 characters
        return 1 <= len(title.strip()) <= 200
    
    @staticmethod
    def validate_description(description: Optional[str]) -> bool:
        """Validate event description."""
        if description is None:
            return True
        
        # Description: max 1000 characters
        return len(description) <= 1000
    
    @staticmethod
    def extract_host_code_from_header(authorization: str) -> str:
        """Extract host code from Authorization header."""
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required"
            )
        
        # Expected format: "Host host_xxxxxxxxxxxxx"
        parts = authorization.split(" ")
        if len(parts) != 2 or parts[0] != "Host":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization format. Expected: 'Host <code>'"
            )
        
        host_code = parts[1]
        if not SecurityUtils.validate_host_code(host_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid host code format"
            )
        
        return host_code