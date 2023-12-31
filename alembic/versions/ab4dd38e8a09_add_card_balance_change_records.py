"""Add card_balance_change_records

Revision ID: ab4dd38e8a09
Revises: 4028c8c002f0
Create Date: 2023-10-30 15:34:30.708677

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ab4dd38e8a09'
down_revision = '4028c8c002f0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('card_balance_change_records',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('card', sa.String(), nullable=False),
    sa.Column('card_template_str', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('card_balance_change_records_idx_card_created_at', 'card_balance_change_records', ['card', 'created_at'], unique=False)
    op.create_index(op.f('ix_card_balance_change_records_created_at'), 'card_balance_change_records', ['created_at'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_card_balance_change_records_created_at'), table_name='card_balance_change_records')
    op.drop_index('card_balance_change_records_idx_card_created_at', table_name='card_balance_change_records')
    op.drop_table('card_balance_change_records')
    # ### end Alembic commands ###
