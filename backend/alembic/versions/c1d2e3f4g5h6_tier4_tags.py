"""tier4_tags

Revision ID: c1d2e3f4g5h6
Revises: b1c2d3e4f5a6
Create Date: 2026-10-02 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c1d2e3f4g5h6'
down_revision = 'b1c2d3e4f5a6'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('tags',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('color', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tags_user_id_name_lower', 'tags', ['user_id', sa.text('lower(name)')], unique=True)
    
    op.create_table('todo_tags',
    sa.Column('todo_id', sa.Uuid(), nullable=False),
    sa.Column('tag_id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['todo_id'], ['todos.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('todo_id', 'tag_id')
    )

def downgrade() -> None:
    op.drop_table('todo_tags')
    op.drop_index('ix_tags_user_id_name_lower', table_name='tags')
    op.drop_table('tags')
