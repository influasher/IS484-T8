"""merge active learning with shap

Revision ID: 2c6b630a093f
Revises: e517a70ef520, e9a8c7d5f341
Create Date: 2025-11-07 23:47:52.118964

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2c6b630a093f'
down_revision = ('e517a70ef520', 'e9a8c7d5f341')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
