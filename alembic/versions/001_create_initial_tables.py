"""create initial tables

Revision ID: 001
Revises:
Create Date: 2026-06-24
"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'metric_snapshots',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        sa.Column('resource_type', sa.String(50), nullable=False, index=True),
        sa.Column('resource_id', sa.String(200), nullable=False),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(50), default=''),
        sa.Column('metadata', sa.JSON(), default=dict),
    )

    op.create_table(
        'alert_history',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', sa.String(200), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('message', sa.Text(), default=''),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        'deployment_history',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        sa.Column('repo', sa.String(100), nullable=False),
        sa.Column('commit_sha', sa.String(40), nullable=False),
        sa.Column('commit_message', sa.String(500), default=''),
        sa.Column('author', sa.String(100), default=''),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('workflow_url', sa.String(500), default=''),
    )


def downgrade():
    op.drop_table('deployment_history')
    op.drop_table('alert_history')
    op.drop_table('metric_snapshots')
