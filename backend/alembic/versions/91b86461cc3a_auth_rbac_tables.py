"""auth_rbac_tables

Revision ID: 91b86461cc3a
Revises: 617446e281c1
Create Date: 2026-09-30 12:36:03.888257

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91b86461cc3a'
down_revision: Union[str, Sequence[str], None] = '617446e281c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.execute('''
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email_or_phone TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    full_name TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_login_at TEXT
);
    ''')
    op.execute('''
CREATE TABLE IF NOT EXISTS roles (
    id TEXT PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL
);
    ''')
    op.execute('''
CREATE TABLE IF NOT EXISTS user_roles (
    user_id TEXT NOT NULL,
    role_id TEXT NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);
    ''')
    op.execute('''
CREATE TABLE IF NOT EXISTS user_scopes (
    user_id TEXT PRIMARY KEY,
    district_id TEXT,
    block_id TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
    ''')
    op.execute('''
CREATE TABLE IF NOT EXISTS sessions_or_refresh_tokens (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token_hash TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
    ''')
    op.execute('''
DROP TABLE IF EXISTS audit_events;
    ''')
    op.execute('''
CREATE TABLE audit_events (
    id TEXT PRIMARY KEY,
    actor_user_id TEXT,
    actor_id TEXT,
    actor_name TEXT,
    actor_role TEXT,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    before_json TEXT,
    after_json TEXT,
    old_values TEXT,
    new_values TEXT,
    metadata TEXT,
    request_id TEXT,
    timestamp TEXT,
    created_at TEXT,
    FOREIGN KEY (actor_user_id) REFERENCES users(id) ON DELETE SET NULL
);
    ''')



def downgrade() -> None:
    """Downgrade schema."""
    pass
