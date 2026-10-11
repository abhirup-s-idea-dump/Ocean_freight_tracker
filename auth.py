"""
Authentication & Authorization Module (Basic Security Requirement)
Supports:
- Hashed passwords with cryptographic salt (PBKDF2-HMAC-SHA256, 100,000 iterations)
- Role-Based Access Control (Admin vs User)
- Stateless signed session tokens (JWT-like HMAC token)
"""

import os
import hmac
import hashlib
import base64
import json
import time
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os.environ.get("SECRET_KEY", "ocean-freight-sustainability-scholarship-key-2026")
security_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with 100k iterations and a unique salt."""
    if not salt:
        salt = base64.b64encode(os.urandom(16)).decode('utf-8')
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    key_hex = key.hex()
    return f"{salt}${key_hex}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored salt$hash."""
    try:
        salt, key_hex = hashed_password.split('$', 1)
        test_key = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return hmac.compare_digest(test_key.hex(), key_hex)
    except Exception:
        return False


def create_access_token(data: Dict[str, Any], expires_in_seconds: int = 86400 * 7) -> str:
    """Create signed HMAC-SHA256 token containing payload and expiration."""
    payload = data.copy()
    payload['exp'] = int(time.time()) + expires_in_seconds
    payload_json = json.dumps(payload, separators=(',', ':'))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode('utf-8')).decode('utf-8').rstrip('=')

    sig = hmac.new(
        SECRET_KEY.encode('utf-8'),
        payload_b64.encode('utf-8'),
        hashlib.sha256
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode('utf-8').rstrip('=')

    return f"{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify HMAC token."""
    try:
        parts = token.split('.')
        if len(parts) != 2:
            return None
        payload_b64, sig_b64 = parts

        # Verify signature
        expected_sig = hmac.new(
            SECRET_KEY.encode('utf-8'),
            payload_b64.encode('utf-8'),
            hashlib.sha256
        ).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode('utf-8').rstrip('=')

        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            return None

        # Add back padding
        pad = len(payload_b64) % 4
        if pad:
            payload_b64 += '=' * (4 - pad)
        payload_json = base64.urlsafe_b64decode(payload_b64.encode('utf-8')).decode('utf-8')
        payload = json.loads(payload_json)

        # Check expiration
        if payload.get('exp', 0) < time.time():
            return None

        return payload
    except Exception:
        return None


def get_current_user_from_request(request: Request) -> Optional[Dict[str, Any]]:
    """Extract and verify user from Bearer header or cookie."""
    auth_header = request.headers.get('Authorization')
    token = None
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1]
    elif 'token' in request.cookies:
        token = request.cookies['token']

    if not token:
        return None

    return decode_access_token(token)


def require_auth(request: Request) -> Dict[str, Any]:
    """Dependency ensuring user is authenticated."""
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in."
        )
    return user


def require_admin(request: Request) -> Dict[str, Any]:
    """Dependency ensuring user has Admin role."""
    user = require_auth(request)
    if user.get('role') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for this action."
        )
    return user
