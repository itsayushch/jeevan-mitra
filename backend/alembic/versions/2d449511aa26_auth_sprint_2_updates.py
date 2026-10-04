"""auth_sprint_2_updates

Revision ID: 2d449511aa26
Revises: 91b86461cc3a
Create Date: 2026-09-30 12:56:39.333087

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2d449511aa26'
down_revision: Union[str, Sequence[str], None] = '91b86461cc3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop previous tables
    op.execute("DROP TABLE IF EXISTS sessions_or_refresh_tokens;")
    op.execute("DROP TABLE IF EXISTS refresh_tokens;")
    op.execute("DROP TABLE IF EXISTS user_scopes;")
    op.execute("DROP TABLE IF EXISTS user_roles;")
    op.execute("DROP TABLE IF EXISTS roles;")
    op.execute("DROP TABLE IF EXISTS users;")

    # Recreate Users
    op.execute('''
    CREATE TABLE users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE,
        phone TEXT UNIQUE,
        password_hash TEXT,
        display_name TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1,
        is_superuser INTEGER NOT NULL DEFAULT 0,
        failed_login_count INTEGER NOT NULL DEFAULT 0,
        locked_until TEXT,
        last_login_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        CHECK (email IS NOT NULL OR phone IS NOT NULL)
    );
    ''')
    op.execute("CREATE INDEX idx_users_email ON users(email) WHERE email IS NOT NULL;")
    op.execute("CREATE INDEX idx_users_phone ON users(phone) WHERE phone IS NOT NULL;")
    op.execute("CREATE INDEX idx_users_is_active ON users(is_active);")

    # Recreate Roles
    op.execute('''
    CREATE TABLE roles (
        id TEXT PRIMARY KEY,
        key TEXT UNIQUE NOT NULL,
        display_name TEXT NOT NULL,
        description TEXT,
        created_at TEXT NOT NULL
    );
    ''')

    # Seed fixed roles
    now = "2026-09-30T00:00:00Z"
    for role in [
        ("role_beneficiary", "beneficiary", "Beneficiary", "End user"),
        ("role_field_worker", "field_worker", "Field Worker", "Local district worker"),
        ("role_district_admin", "district_admin", "District Admin", "District level administrator"),
        ("role_catalogue_manager", "catalogue_manager", "Catalogue Manager", "Manages courses and skills"),
        ("role_super_admin", "super_admin", "Super Admin", "Full system access"),
        ("role_auditor", "auditor", "Auditor", "Read-only audit access")
    ]:
        op.execute(f"INSERT INTO roles (id, key, display_name, description, created_at) VALUES ('{role[0]}', '{role[1]}', '{role[2]}', '{role[3]}', '{now}');")

    # Recreate User Roles
    op.execute('''
    CREATE TABLE user_roles (
        user_id TEXT NOT NULL,
        role_id TEXT NOT NULL,
        assigned_by TEXT,
        assigned_at TEXT NOT NULL,
        revoked_at TEXT,
        PRIMARY KEY (user_id, role_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
        FOREIGN KEY (assigned_by) REFERENCES users(id) ON DELETE SET NULL
    );
    ''')

    # Recreate User Scopes
    op.execute('''
    CREATE TABLE user_scopes (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        district_id TEXT,
        block_id TEXT,
        scope_type TEXT NOT NULL,
        assigned_by TEXT,
        assigned_at TEXT NOT NULL,
        revoked_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (assigned_by) REFERENCES users(id) ON DELETE SET NULL
    );
    ''')

    # Recreate Refresh Tokens
    op.execute('''
    CREATE TABLE refresh_tokens (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        token_hash TEXT UNIQUE NOT NULL,
        issued_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        rotated_from_id TEXT,
        revoked_at TEXT,
        revoked_reason TEXT,
        last_used_at TEXT,
        user_agent_hash TEXT,
        ip_hash TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    ''')
    op.execute("CREATE INDEX idx_refresh_tokens_token_hash ON refresh_tokens(token_hash);")
    op.execute("CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);")

    # Recreate Audit Events matching Sprint 2 exactly
    op.execute("DROP TABLE IF EXISTS audit_events;")
    op.execute('''
    CREATE TABLE audit_events (
        id TEXT PRIMARY KEY,
        actor_user_id TEXT,
        action TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id TEXT,
        request_id TEXT,
        outcome TEXT,
        metadata_json TEXT,
        before_json TEXT,
        after_json TEXT,
        created_at TEXT NOT NULL
    );
    ''')
    op.execute("CREATE INDEX idx_audit_events_actor ON audit_events(actor_user_id);")
    op.execute("CREATE INDEX idx_audit_events_action ON audit_events(action);")

def downgrade() -> None:
    pass
