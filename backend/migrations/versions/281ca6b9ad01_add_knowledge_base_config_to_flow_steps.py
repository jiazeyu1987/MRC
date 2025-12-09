"""Add knowledge base config to flow_steps

Revision ID: 281ca6b9ad01
Revises: 281ca6b9ad00
Create Date: 2025-12-09 12:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '281ca6b9ad01'
down_revision = '281ca6b9ad00'
branch_labels = None
depends_on = None


def upgrade():
    # Add _knowledge_base_config field to flow_steps table
    op.add_column('flow_steps', sa.Column('_knowledge_base_config', sa.Text(), nullable=True))

    # Add index for better query performance
    op.create_index('idx_flow_steps_knowledge_base_config', 'flow_steps', ['_knowledge_base_config'])


def downgrade():
    # Remove index first
    try:
        op.drop_index('idx_flow_steps_knowledge_base_config', table_name='flow_steps')
    except:
        pass  # Index might not exist

    # Remove _knowledge_base_config field
    op.drop_column('flow_steps', '_knowledge_base_config')