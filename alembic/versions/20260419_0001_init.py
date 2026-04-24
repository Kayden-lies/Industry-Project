"""init

Revision ID: 20260419_0001
Revises:
Create Date: 2026-04-19
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "20260419_0001"
down_revision = None
branch_labels = None
depends_on = None


# ✅ ENUM defined but NOT created (important fix)
execution_status_enum = sa.Enum(
    'PENDING', 'RUNNING', 'COMPLETED', 'FAILED',
    name='execution_status',
    create_type=False
)


def upgrade() -> None:
    # ❌ REMOVED: execution_status_enum.create(...)

    op.create_table(
        "executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("job_name", sa.String(length=255), nullable=False),
        sa.Column("user", sa.String(length=255), nullable=False),
        sa.Column("status", execution_status_enum, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("inputs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("outputs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_index("ix_executions_job_name", "executions", ["job_name"])
    op.create_index("ix_executions_status", "executions", ["status"])
    op.create_index("ix_executions_user", "executions", ["user"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("execution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("actor", sa.String(length=255), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("previous_hash", sa.String(length=64), nullable=True),
        sa.Column("current_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["execution_id"], ["executions.id"], ondelete="CASCADE"),
    )

    op.create_index("ix_audit_logs_execution_id", "audit_logs", ["execution_id"])
    op.create_index("ix_audit_logs_current_hash", "audit_logs", ["current_hash"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_current_hash", table_name="audit_logs")
    op.drop_index("ix_audit_logs_execution_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_executions_user", table_name="executions")
    op.drop_index("ix_executions_status", table_name="executions")
    op.drop_index("ix_executions_job_name", table_name="executions")
    op.drop_table("executions")

    # Optional: keep or remove enum drop (safe either way)
    execution_status_enum.drop(op.get_bind(), checkfirst=True)
```
