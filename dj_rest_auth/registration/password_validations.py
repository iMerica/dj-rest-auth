import re
from typing import Union, List
from dataclasses import dataclass
from enum import Enum

class PasswordStrength(Enum):
    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"

@dataclass
class PasswordValidationResult:
    is_valid: bool
    errors: List[str]
    strength: PasswordStrength

class PasswordValidator:
    def __init__(self, 
                 min_length: int = 8,
                 require_uppercase: bool = True,
                 require_lowercase: bool = True,
                 require_digits: bool = True,
                 require_special_chars: bool = True):
        
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_special_chars = require_special_chars
      
    def validate_password(self, password1, password2) -> PasswordValidationResult:
        errors = []

        # Basic validation
        if not password1 or not password2:
            errors.append("Password fields cannot be empty")
            return PasswordValidationResult(False, errors, PasswordStrength.WEAK)

        # Check if passwords match
        if password1 != password2:
            errors.append("Passwords do not match")
            return PasswordValidationResult(False, errors, PasswordStrength.WEAK)

        # Length check
        if len(password1) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")

        # Uppercase check
        if self.require_uppercase and not any(c.isupper() for c in password1):
            errors.append("Password must contain at least one uppercase letter")

        # Lowercase check
        if self.require_lowercase and not any(c.islower() for c in password1):
            errors.append("Password must contain at least one lowercase letter")

        # Digit check
        if self.require_digits and not any(c.isdigit() for c in password1):
            errors.append("Password must contain at least one number")

        # Special character check
        if self.require_special_chars:
            special_chars = re.compile(r'[!@#$%^&*(),.?":{}|<>]')
            if not special_chars.search(password1):
                errors.append("Password must contain at least one special character")


        # Sequential characters check
        if self._has_sequential_chars(password1):
            errors.append("Password contains sequential characters")

        # Determine password strength
        strength = self._calculate_strength(password1)

        return PasswordValidationResult

    def _has_sequential_chars(self, password: str) -> bool:
        """Check for sequential characters (e.g., 'abc', '123')"""
        sequences = ('abcdefghijklmnopqrstuvwxyz', '0123456789')
        lowercase_pass = password.lower()
        
        for seq in sequences:
            for i in range(len(seq) - 2):
                if seq[i:i+3] in lowercase_pass:
                    return True
        return False

    def _calculate_strength(self, password: str) -> PasswordStrength:
        """Calculate password strength based on various factors"""
        score = 0
        
        # Length points (up to 5)
        score += min(5, len(password) // 2)
        
        # Character variety points
        if any(c.isupper() for c in password):
            score += 2
        if any(c.islower() for c in password):
            score += 2
        if any(c.isdigit() for c in password):
            score += 2
        if any(not c.isalnum() for c in password):
            score += 3
            
        # Unique character points
        score += min(3, len(set(password)) // 3)
        
        match score:
            case s if s >= 10:
                return PasswordStrength.STRONG
            case s if s >= 6:
                return PasswordStrength.MEDIUM
            case _:
                return PasswordStrength.WEAK

# Example usage:
def validate_password(password1: str, password2: str) -> Union[str, List[str]]:
    validator = PasswordValidator()
    result = validator.validate_password(password1, password2)
    
    if not result.is_valid:
        return result.errors
    
    return f"Password is valid (Strength: {result.strength.value})"

