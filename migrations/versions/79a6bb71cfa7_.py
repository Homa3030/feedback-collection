"""empty message

Revision ID: 79a6bb71cfa7
Revises: a6b614e43240
Create Date: 2020-11-10 23:34:40.738557

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '79a6bb71cfa7'
down_revision = 'a6b614e43240'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('form_result_fkey', 'form', type_='foreignkey')
    op.create_foreign_key(None, 'form', 'result', ['result'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'form', type_='foreignkey')
    op.create_foreign_key('form_result_fkey', 'form', 'form_template', ['result'], ['id'])
    # ### end Alembic commands ###
