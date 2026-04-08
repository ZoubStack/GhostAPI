"""Tests for OAuth, Audit Logs, and Token Blacklist features."""

import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path

from ghostapi.auth.oauth import (
    OAuthProvider,
    OAuthConfig,
    OAuthUser,
    OAuthState,
    get_oauth_config,
    set_oauth_config,
    OAUTH_URLS
)

from ghostapi.auth.audit import (
    AuditLogger,
    AuditEntry,
    AuditAction,
    AuditLevel,
    get_audit_logger,
    set_audit_logger
)

from ghostapi.auth.token_blacklist import (
    TokenBlacklist,
    get_token_blacklist,
    set_token_blacklist,
    check_token_not_revoked,
    revoke_current_token
)


# ====== OAuth Tests ======

class TestOAuthConfig:
    """Tests for OAuth configuration."""
    
    def test_config_from_env(self):
        """Test creating config from environment variables."""
        config = OAuthConfig.from_env()
        assert config is not None
    
    def test_is_enabled_google(self):
        """Test checking if Google is enabled."""
        config = OAuthConfig(
            google_client_id="test-id",
            google_client_secret="test-secret"
        )
        assert config.is_enabled(OAuthProvider.GOOGLE) is True
    
    def test_is_enabled_google_disabled(self):
        """Test Google disabled when no credentials."""
        config = OAuthConfig()
        assert config.is_enabled(OAuthProvider.GOOGLE) is False
    
    def test_get_client_id(self):
        """Test getting client ID for provider."""
        config = OAuthConfig(
            google_client_id="google-id",
            github_client_id="github-id"
        )
        assert config.get_client_id(OAuthProvider.GOOGLE) == "google-id"
        assert config.get_client_id(OAuthProvider.GITHUB) == "github-id"


class TestOAuthState:
    """Tests for OAuth state management."""
    
    def test_create_state(self):
        """Test creating OAuth state."""
        state = OAuthState()
        state_str = state.create(OAuthProvider.GOOGLE, "/redirect")
        
        assert state_str is not None
        assert len(state_str) > 0
    
    def test_validate_state(self):
        """Test validating OAuth state."""
        state = OAuthState()
        state_str = state.create(OAuthProvider.GITHUB, "/callback")
        
        result = state.validate(state_str)
        assert result is not None
        assert result["provider"] == "github"
    
    def test_validate_invalid_state(self):
        """Test validating invalid state."""
        state = OAuthState()
        result = state.validate("invalid-state")
        
        assert result is None


# ====== Audit Tests ======

class TestAuditLogger:
    """Tests for audit logging."""
    
    def test_initialization(self):
        """Test audit logger initialization."""
        logger = AuditLogger(max_entries=1000)
        assert logger.max_entries == 1000
        assert len(logger._entries) == 0
    
    def test_log_event(self):
        """Test logging an event."""
        logger = AuditLogger()
        
        entry = logger.log_event(
            action=AuditAction.LOGIN,
            level=AuditLevel.INFO,
            user_id="user-123",
            user_email="test@example.com",
            ip_address="192.168.1.1"
        )
        
        assert entry is not None
        assert entry.action == AuditAction.LOGIN
        assert entry.user_id == "user-123"
        assert entry.user_email == "test@example.com"
    
    def test_get_entries(self):
        """Test querying audit entries."""
        logger = AuditLogger()
        
        # Log some events
        logger.log_event(
            action=AuditAction.LOGIN,
            user_id="user-1"
        )
        logger.log_event(
            action=AuditAction.DATA_READ,
            user_id="user-1"
        )
        logger.log_event(
            action=AuditAction.LOGIN,
            user_id="user-2"
        )
        
        # Query
        entries = logger.get_entries(user_id="user-1")
        assert len(entries) == 2
    
    def test_get_entries_by_action(self):
        """Test querying by action."""
        logger = AuditLogger()
        
        logger.log_event(action=AuditAction.LOGIN)
        logger.log_event(action=AuditAction.LOGIN)
        logger.log_event(action=AuditAction.LOGOUT)
        
        login_entries = logger.get_entries(action=AuditAction.LOGIN)
        assert len(login_entries) == 2
    
    def test_get_user_activity(self):
        """Test getting user activity summary."""
        logger = AuditLogger()
        
        logger.log_event(
            action=AuditAction.LOGIN,
            user_id="user-123"
        )
        logger.log_event(
            action=AuditAction.DATA_READ,
            user_id="user-123"
        )
        
        activity = logger.get_user_activity("user-123")
        
        assert activity["user_id"] == "user-123"
        assert activity["total_actions"] == 2
        assert "login" in activity["actions_by_type"]
    
    def test_export_logs_json(self):
        """Test exporting logs as JSON."""
        logger = AuditLogger()
        
        logger.log_event(action=AuditAction.LOGIN)
        
        export = logger.export_logs(format="json")
        data = json.loads(export)
        
        assert len(data) > 0
        assert data[0]["action"] == "login"
    
    def test_clear_old_logs(self):
        """Test clearing old logs."""
        logger = AuditLogger()
        
        logger.log_event(action=AuditAction.LOGIN)
        
        deleted = logger.clear_old_logs(days=0)
        
        assert deleted >= 0


class TestAuditEntry:
    """Tests for audit entry."""
    
    def test_to_dict(self):
        """Test converting entry to dictionary."""
        entry = AuditEntry(
            id="test-id",
            timestamp=datetime.utcnow(),
            action=AuditAction.LOGIN,
            level=AuditLevel.INFO,
            user_id="user-123"
        )
        
        data = entry.to_dict()
        
        assert data["id"] == "test-id"
        assert data["action"] == "login"
        assert data["level"] == "info"
        assert data["user_id"] == "user-123"


# ====== Token Blacklist Tests ======

class TestTokenBlacklist:
    """Tests for token blacklist."""
    
    def test_initialization(self):
        """Test blacklist initialization."""
        blacklist = TokenBlacklist()
        assert blacklist is not None
    
    def test_revoke_token(self):
        """Test revoking a token."""
        blacklist = TokenBlacklist()
        
        expires = datetime.utcnow() + timedelta(hours=1)
        
        blacklist.revoke_token(
            jti="token-123",
            user_id="user-456",
            expires_at=expires,
            reason="logout"
        )
        
        assert blacklist.is_revoked("token-123") is True
    
    def test_is_revoked_not_revoked(self):
        """Test checking non-revoked token."""
        blacklist = TokenBlacklist()
        
        assert blacklist.is_revoked("non-existent") is False
    
    def test_revoke_all_user_tokens(self):
        """Test revoking all tokens for a user."""
        blacklist = TokenBlacklist()
        
        expires = datetime.utcnow() + timedelta(hours=1)
        
        # Revoke multiple tokens
        blacklist.revoke_token("token-1", "user-1", expires)
        blacklist.revoke_token("token-2", "user-1", expires)
        blacklist.revoke_token("token-3", "user-2", expires)
        
        count = blacklist.revoke_all_user_tokens("user-1", reason="password_change")
        
        assert count == 2
    
    def test_get_stats(self):
        """Test getting blacklist statistics."""
        blacklist = TokenBlacklist()
        
        expires = datetime.utcnow() + timedelta(hours=1)
        blacklist.revoke_token("token-1", "user-1", expires)
        
        stats = blacklist.get_stats()
        
        assert "total_revoked" in stats
        assert stats["total_revoked"] >= 1
    
    def test_get_user_revoked_tokens(self):
        """Test getting user's revoked tokens."""
        blacklist = TokenBlacklist()
        
        expires = datetime.utcnow() + timedelta(hours=1)
        blacklist.revoke_token("token-1", "user-1", expires, reason="logout")
        
        tokens = blacklist.get_user_revoked_tokens("user-1")
        
        assert len(tokens) >= 1


class TestGlobalInstances:
    """Tests for global instances."""
    
    def test_get_audit_logger(self):
        """Test getting global audit logger."""
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()
        
        assert logger1 is logger2
    
    def test_set_audit_logger(self):
        """Test setting global audit logger."""
        new_logger = AuditLogger()
        set_audit_logger(new_logger)
        
        retrieved = get_audit_logger()
        assert retrieved is new_logger
    
    def test_get_token_blacklist(self):
        """Test getting global token blacklist."""
        blacklist1 = get_token_blacklist()
        blacklist2 = get_token_blacklist()
        
        assert blacklist1 is blacklist2
    
    def test_set_token_blacklist(self):
        """Test setting global token blacklist."""
        new_blacklist = TokenBlacklist()
        set_token_blacklist(new_blacklist)
        
        retrieved = get_token_blacklist()
        assert retrieved is new_blacklist
