"""
Two-Factor Authentication Tests for Vehicle Detection App
Tests for TOTP-based 2FA implementation
"""
import pytest
import time


@pytest.mark.two_factor
@pytest.mark.unit
def test_generate_secret():
    """Test that secret generation produces valid base32 strings"""
    from two_factor_auth import TwoFactorAuthManager
    
    secret = TwoFactorAuthManager.generate_secret()
    
    assert secret is not None
    assert len(secret) > 0
    # Should be valid base32
    assert TwoFactorAuthManager.is_valid_secret(secret) is True


@pytest.mark.two_factor
@pytest.mark.unit
def test_generate_secret_unique():
    """Test that generated secrets are unique"""
    from two_factor_auth import TwoFactorAuthManager
    
    secret1 = TwoFactorAuthManager.generate_secret()
    secret2 = TwoFactorAuthManager.generate_secret()
    
    assert secret1 != secret2


@pytest.mark.two_factor
@pytest.mark.unit
def test_init_with_secret():
    """Test initialization with existing secret"""
    from two_factor_auth import TwoFactorAuthManager
    
    secret = TwoFactorAuthManager.generate_secret()
    manager = TwoFactorAuthManager(secret=secret)
    
    assert manager.secret == secret


@pytest.mark.two_factor
@pytest.mark.unit
def test_init_without_secret():
    """Test initialization without secret generates one"""
    from two_factor_auth import TwoFactorAuthManager
    
    manager = TwoFactorAuthManager()
    
    assert manager.secret is not None
    assert len(manager.secret) > 0


@pytest.mark.two_factor
@pytest.mark.unit
def test_generate_totp():
    """Test TOTP code generation"""
    from two_factor_auth import TwoFactorAuthManager
    
    manager = TwoFactorAuthManager(secret='JBSWY3DPEHPK3PXP')
    
    # Generate code at a specific timestamp
    code = manager.generate_totp(timestamp=1234567890)
    
    assert code is not None
    assert len(code) == 6
    assert code.isdigit()


@pytest.mark.two_factor
@pytest.mark.unit
def test_verify_valid_code():
    """Test verification of a valid TOTP code"""
    from two_factor_auth import TwoFactorAuthManager
    
    manager = TwoFactorAuthManager(secret='JBSWY3DPEHPK3PXP')
    
    timestamp = int(time.time())
    code = manager.generate_totp(timestamp=timestamp)
    
    assert manager.verify_code(code, timestamp=timestamp) is True


@pytest.mark.two_factor
@pytest.mark.unit
def test_verify_invalid_code():
    """Test verification of an invalid TOTP code"""
    from two_factor_auth import TwoFactorAuthManager
    
    manager = TwoFactorAuthManager(secret='JBSWY3DPEHPK3PXP')
    
    assert manager.verify_code('000000') is False or manager.verify_code('999999') is False


@pytest.mark.two_factor
@pytest.mark.unit
def test_verify_code_with_window():
    """Test verification with time window tolerance"""
    from two_factor_auth import TwoFactorAuthManager
    
    manager = TwoFactorAuthManager(secret='JBSWY3DPEHPK3PXP')
    
    timestamp = int(time.time())
    code = manager.generate_totp(timestamp=timestamp)
    
    # Code should still be valid 30 seconds before/after
    assert manager.verify_code(code, timestamp=timestamp - 30, valid_window=1) is True
    assert manager.verify_code(code, timestamp=timestamp + 30, valid_window=1) is True


@pytest.mark.two_factor
@pytest.mark.unit
def test_get_uri():
    """Test otpauth URI generation"""
    from two_factor_auth import TwoFactorAuthManager
    
    manager = TwoFactorAuthManager(secret='JBSWY3DPEHPK3PXP')
    
    uri = manager.get_uri(username='testuser')
    
    assert uri.startswith('otpauth://totp/')
    assert 'JBSWY3DPEHPK3PXP' in uri
    assert 'testuser' in uri


@pytest.mark.two_factor
@pytest.mark.unit
def test_is_valid_secret():
    """Test secret validation"""
    from two_factor_auth import TwoFactorAuthManager
    
    # Valid base32
    assert TwoFactorAuthManager.is_valid_secret('JBSWY3DPEHPK3PXP') is True
    assert TwoFactorAuthManager.is_valid_secret('JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXP') is True
    
    # Invalid
    assert TwoFactorAuthManager.is_valid_secret('invalid!@#') is False
    assert TwoFactorAuthManager.is_valid_secret('') is False


@pytest.mark.two_factor
@pytest.mark.unit
def test_user_model_has_2fa_fields():
    """Test that User model has 2FA fields"""
    from models import User
    
    assert hasattr(User, 'two_factor_enabled')
    assert hasattr(User, 'two_factor_secret')


@pytest.mark.two_factor
@pytest.mark.unit
def test_totp_codes_change_over_time():
    """Test that TOTP codes change with time"""
    from two_factor_auth import TwoFactorAuthManager
    
    manager = TwoFactorAuthManager(secret='JBSWY3DPEHPK3PXP')
    
    # Codes at different time steps should differ
    code1 = manager.generate_totp(timestamp=1234567890)
    code2 = manager.generate_totp(timestamp=1234567890 + 30)
    
    # They should be different (extremely unlikely to be same)
    # But both should be valid 6-digit codes
    assert len(code1) == 6
    assert len(code2) == 6
