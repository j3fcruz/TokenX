"""
Validation utilities for TokenX TOTP Manager.
"""
import re
import os


class Validators:
    """Collection of validation functions."""
    
    @staticmethod
    def validate_profile_name(name):
        """
        Validate profile name.
        
        Args:
            name (str): Profile name to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not name or not isinstance(name, str):
            return False, "Profile name cannot be empty"
        
        if len(name) > 255:
            return False, "Profile name too long (max 255 characters)"
        
        # Check for valid characters (alphanumeric, dots, hyphens, underscores, @)
        if not re.match(r'^[\w.@-]+


MIGRATION GUIDE:
================
1. Copy the existing totp_crypto.py and TokenX.py to project root
2. Copy resources_rc.py (Qt resources)
3. Run: pip install -r requirements.txt
4. Run: python main.py

BENEFITS OF MODULAR STRUCTURE:
==============================
✓ Single Responsibility - each module has one purpose
✓ Easier Testing - services can be tested independently
✓ Better Maintainability - related code grouped together
✓ Scalability - easy to add new features
✓ Code Reusability - services can be used in other projects
✓ Clear Dependencies - explicit imports show relationships, name):
            return False, "Profile name contains invalid characters"
        
        return True, ""
    
    @staticmethod
    def validate_master_password(password):
        """
        Validate master password strength.
        
        Args:
            password (str): Password to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not password or not isinstance(password, str):
            return False, "Password cannot be empty"
        
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
        
        if len(password) > 255:
            return False, "Password too long"
        
        return True, ""
    
    @staticmethod
    def validate_totp_secret(secret):
        """
        Validate TOTP secret format.
        
        Args:
            secret (str): Base32-encoded TOTP secret
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not secret or not isinstance(secret, str):
            return False, "Secret cannot be empty"
        
        # TOTP secrets should be base32 encoded
        if not re.match(r'^[A-Z2-7]+={0,2}


MIGRATION GUIDE:
================
1. Copy the existing totp_crypto.py and TokenX.py to project root
2. Copy resources_rc.py (Qt resources)
3. Run: pip install -r requirements.txt
4. Run: python main.py

BENEFITS OF MODULAR STRUCTURE:
==============================
✓ Single Responsibility - each module has one purpose
✓ Easier Testing - services can be tested independently
✓ Better Maintainability - related code grouped together
✓ Scalability - easy to add new features
✓ Code Reusability - services can be used in other projects
✓ Clear Dependencies - explicit imports show relationships, secret.upper()):
            return False, "Invalid secret format (must be base32-encoded)"
        
        return True, ""
    
    @staticmethod
    def validate_file_path(file_path):
        """
        Validate file path.
        
        Args:
            file_path (str): File path to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not file_path or not isinstance(file_path, str):
            return False, "File path cannot be empty"
        
        if len(file_path) > 260:  # Windows MAX_PATH
            return False, "File path too long"
        
        return True, ""
    
    @staticmethod
    def validate_otpauth_uri(uri):
        """
        Validate otpauth:// URI format.
        
        Args:
            uri (str): URI to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not uri or not isinstance(uri, str):
            return False, "URI cannot be empty"
        
        if not uri.startswith("otpauth://"):
            return False, "Invalid URI format (must start with otpauth://)"
        
        if not ("totp" in uri or "hotp" in uri):
            return False, "Unsupported OTP type (only TOTP/HOTP supported)"
        
        if "secret=" not in uri:
            return False, "Missing secret parameter in URI"
        
        return True, ""
    
    @staticmethod
    def validate_profile_data(data):
        """
        Validate parsed profile data.
        
        Args:
            data (dict): Profile data to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        required_fields = ['secret', 'label', 'issuer']
        
        if not isinstance(data, dict):
            return False, "Profile data must be a dictionary"
        
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Missing required field: {field}"
        
        # Validate secret
        is_valid, msg = Validators.validate_totp_secret(data['secret'])
        if not is_valid:
            return False, f"Invalid secret: {msg}"
        
        # Validate digits
        digits = data.get('digits', 6)
        if not isinstance(digits, (int, str)) or int(digits) < 4 or int(digits) > 10:
            return False, "Digits must be between 4 and 10"
        
        # Validate period
        period = data.get('period', 30)
        if not isinstance(period, (int, str)) or int(period) < 10:
            return False, "Period must be at least 10 seconds"
        
        # Validate algorithm
        valid_algorithms = ['SHA1', 'SHA256', 'SHA512', 'MD5']
        algorithm = data.get('algorithm', 'SHA1').upper()
        if algorithm not in valid_algorithms:
            return False, f"Invalid algorithm: {algorithm}"
        
        return True, ""
    
    @staticmethod
    def sanitize_filename(filename):
        """
        Sanitize filename for safe file operations.
        
        Args:
            filename (str): Filename to sanitize
            
        Returns:
            str: Sanitized filename
        """
        # Remove invalid characters
        sanitized = re.sub(r'[^\w.@-]', '_', filename)
        
        # Limit length
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:255-len(ext)] + ext
        
        return sanitized
    
    @staticmethod
    def validate_master_key_file(file_path):
        """
        Validate master key file exists and is readable.
        
        Args:
            file_path (str): Path to master key file
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not file_path:
            return False, "File path not specified"
        
        if not os.path.exists(file_path):
            return False, "Master key file not found"
        
        if not os.path.isfile(file_path):
            return False, "Master key path is not a file"
        
        if not os.access(file_path, os.R_OK):
            return False, "Master key file is not readable"
        
        return True, ""