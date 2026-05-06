"""
Two-Factor Authentication (2FA) Manager for Vehicle Detection App
TOTP-based 2FA implementation using pyotp
"""
import os
import base64
import hashlib
import hmac
import struct
import time
from typing import Optional, Tuple


class TwoFactorAuthManager:
    """
    Manager for TOTP-based Two-Factor Authentication
    """
    
    def __init__(self, secret: Optional[str] = None):
        """
        Initialize 2FA manager
        
        Args:
            secret: Base32-encoded secret key (generated if None)
        """
        if secret is None:
            self.secret = self.generate_secret()
        else:
            self.secret = secret
    
    @staticmethod
    def generate_secret() -> str:
        """
        Generate a new random TOTP secret key
        
        Returns:
            Base32-encoded secret key
        """
        # Generate 20 random bytes and encode as base32
        random_bytes = os.urandom(20)
        return base64.b32encode(random_bytes).decode('utf-8')
    
    def generate_totp(self, timestamp: Optional[int] = None) -> str:
        """
        Generate a TOTP code
        
        Args:
            timestamp: Unix timestamp (current time if None)
            
        Returns:
            6-digit TOTP code as string
        """
        if timestamp is None:
            timestamp = int(time.time())
        
        # TOTP uses 30-second time steps
        time_step = timestamp // 30
        
        # Decode secret
        key = base64.b32decode(self.secret, casefold=True)
        
        # Convert time step to bytes
        time_bytes = struct.pack('>Q', time_step)
        
        # HMAC-SHA1
        hmac_hash = hmac.new(key, time_bytes, hashlib.sha1).digest()
        
        # Dynamic truncation
        offset = hmac_hash[-1] & 0x0F
        code = struct.unpack('>I', hmac_hash[offset:offset + 4])[0]
        code = code & 0x7FFFFFFF
        
        # Get 6 digits
        totp_code = str(code % 1000000).zfill(6)
        
        return totp_code
    
    def verify_code(self, code: str, timestamp: Optional[int] = None, 
                    valid_window: int = 1) -> bool:
        """
        Verify a TOTP code
        
        Args:
            code: The code to verify
            timestamp: Unix timestamp (current time if None)
            valid_window: Number of time steps to check before/after (default 1)
            
        Returns:
            True if code is valid, False otherwise
        """
        if timestamp is None:
            timestamp = int(time.time())
        
        # Check current and adjacent time steps
        for offset in range(-valid_window, valid_window + 1):
            check_time = timestamp + (offset * 30)
            expected_code = self.generate_totp(check_time)
            if hmac.compare_digest(code, expected_code):
                return True
        
        return False
    
    def get_uri(self, username: str, issuer: str = 'Vehicle Detection App') -> str:
        """
        Get the otpauth URI for QR code generation
        
        Args:
            username: User's username
            issuer: Application name
            
        Returns:
            otpauth:// URI string
        """
        import urllib.parse
        label = urllib.parse.quote(f"{issuer}:{username}")
        params = urllib.parse.urlencode({
            'secret': self.secret,
            'issuer': issuer,
            'algorithm': 'SHA1',
            'digits': 6,
            'period': 30
        })
        return f"otpauth://totp/{label}?{params}"
    
    @staticmethod
    def is_valid_secret(secret: str) -> bool:
        """
        Validate a base32-encoded secret
        
        Args:
            secret: Secret key to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not secret or len(secret) < 8:
            return False
        try:
            decoded = base64.b32decode(secret, casefold=True)
            return len(decoded) >= 10  # Minimum 10 bytes for security
        except Exception:
            return False
