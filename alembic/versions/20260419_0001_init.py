"""init

Revision ID: 20260419_0001
Revises:
Create Date: 2026-04-19
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260419_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ✅ CREATE ENUM SAFELY
    op.execute("""
    DO $$ BEGIN
        CREATE TYPE execution_status AS ENUM ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """)

    # ✅ USE RAW TYPE (NO SQLAlchemy ENUM)
    op.create_table(
        "executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_name", sa.String(255), nullable=False),
        sa.Column("user", sa.String(255), nullable=False),
        sa.Column("status", postgresql.ENUM(
            'PENDING', 'RUNNING', 'COMPLETED', 'FAILED',
            name='execution_status',
            create_type=False
        ), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("duration_seconds", sa.Float()),
        sa.Column("inputs", postgresql.JSONB),
        sa.Column("outputs", postgresql.JSONB),
        sa.Column("error_details", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_index("ix_executions_job_name", "executions", ["job_name"])
    op.create_index("ix_executions_status", "executions", ["status"])
    op.create_index("ix_executions_user", "executions", ["user"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("execution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("metadata", postgresql.JSONB),
        sa.Column("previous_hash", sa.String(64)),
        sa.Column("current_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["execution_id"], ["executions.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("executions")
