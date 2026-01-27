import re
from typing import Optional
from datetime import datetime


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength
    Returns: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    return True, None


def validate_file_extension(filename: str, allowed_extensions: list[str]) -> bool:
    """Validate file extension"""
    if '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in allowed_extensions


def validate_file_size(file_size: int, max_size: int) -> bool:
    """Validate file size in bytes"""
    return file_size <= max_size


def validate_date_range(start_date: datetime, end_date: datetime) -> tuple[bool, Optional[str]]:
    """Validate date range"""
    if start_date > end_date:
        return False, "Start date must be before end date"
    
    if end_date > datetime.now():
        return False, "End date cannot be in the future"
    
    return True, None


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal"""
    # Remove any path components
    filename = filename.split('/')[-1].split('\\')[-1]
    
    # Remove any non-alphanumeric characters except dots, hyphens, and underscores
    filename = re.sub(r'[^\w\-.]', '_', filename)
    
    return filename
