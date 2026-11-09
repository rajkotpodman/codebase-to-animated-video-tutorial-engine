"""Initial database revision for Users, Jobs, and Credit Ledger tables.

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-11-06 12:12:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Users, Jobs, and Credit Ledger tables with indexes."""
    # 1. Users Table
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("credits", sa.Integer(), nullable=False, server_default="120"),
        sa.Column("stripe_customer_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_users_id"), ["id"], unique=False)
        batch_op.create_index(batch_op.f("ix_users_email"), ["email"], unique=True)
        batch_op.create_index(batch_op.f("ix_users_stripe_customer_id"), ["stripe_customer_id"], unique=False)

    # 2. Jobs Table
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=True),
        sa.Column("repo_url", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("step", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("step_name", sa.String(length=128), nullable=False, server_default="Queued"),
        sa.Column("voice", sa.String(length=64), nullable=False, server_default="en-US-ChristopherNeural"),
        sa.Column("resolution", sa.String(length=16), nullable=False, server_default="1080p"),
        sa.Column("theme", sa.String(length=32), nullable=False, server_default="midnight"),
        sa.Column("video_path", sa.String(length=512), nullable=True),
        sa.Column("download_url", sa.String(length=1024), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_jobs_id"), ["id"], unique=False)
        batch_op.create_index(batch_op.f("ix_jobs_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_jobs_user_id"), ["user_id"], unique=False)

    # 3. Credit Ledger / Transactions Table
    op.create_table(
        "credit_transactions",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("credits_added", sa.Integer(), nullable=False),
        sa.Column("amount_paid_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="usd"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="completed"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("credit_transactions", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_credit_transactions_id"), ["id"], unique=False)
        batch_op.create_index(batch_op.f("ix_credit_transactions_user_id"), ["user_id"], unique=False)


def downgrade() -> None:
    """Drop Credit Ledger, Jobs, and Users tables."""
    with op.batch_alter_table("credit_transactions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_credit_transactions_user_id"))
        batch_op.drop_index(batch_op.f("ix_credit_transactions_id"))
    op.drop_table("credit_transactions")

    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_jobs_user_id"))
        batch_op.drop_index(batch_op.f("ix_jobs_status"))
        batch_op.drop_index(batch_op.f("ix_jobs_id"))
    op.drop_table("jobs")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_users_stripe_customer_id"))
        batch_op.drop_index(batch_op.f("ix_users_email"))
        batch_op.drop_index(batch_op.f("ix_users_id"))
    op.drop_table("users")
