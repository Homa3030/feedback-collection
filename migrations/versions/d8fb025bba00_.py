"""empty message

Revision ID: d8fb025bba00
Revises: e6dd49515a04
Create Date: 2020-11-10 22:10:36.314268

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd8fb025bba00'
down_revision = 'e6dd49515a04'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('form', sa.Column('result', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'form', 'form_template', ['result'], ['id'])
    op.add_column('question', sa.Column('question_order', sa.Integer(), nullable=True))
    op.add_column('result', sa.Column('form_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'result', 'form', ['form_id'], ['id'])
    op.drop_column('result', 'average_grade')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('result', sa.Column('average_grade', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'result', type_='foreignkey')
    op.drop_column('result', 'form_id')
    op.drop_column('question', 'question_order')
    op.drop_constraint(None, 'form', type_='foreignkey')
    op.drop_column('form', 'result')
    # ### end Alembic commands ###