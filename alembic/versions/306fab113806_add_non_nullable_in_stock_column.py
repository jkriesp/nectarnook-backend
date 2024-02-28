"""Add non-nullable in_stock column

Revision ID: 306fab113806
Revises: 
Create Date: 2024-02-27 20:54:07.054889

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '306fab113806'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Add the column as nullable
    op.add_column('products', sa.Column('in_stock', sa.Boolean(), nullable=True))
    
    # Step 2: Update the column to set a default value for existing rows
    op.execute('UPDATE products SET in_stock = True')  # or False, depending on your business logic
    
    # Step 3: Alter the column to set it as non-nullable
    op.alter_column('products', 'in_stock', nullable=False)

def downgrade() -> None:
    # To downgrade, simply drop the column (if you're okay losing this data)
    op.drop_column('products', 'in_stock')