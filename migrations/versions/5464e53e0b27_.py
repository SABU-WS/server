"""empty message

Revision ID: 5464e53e0b27
Revises: 5c891010c405
Create Date: 2023-12-09 08:57:30.510128

"""
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "5464e53e0b27"
down_revision = "5c891010c405"
branch_labels = None
depends_on = None


def upgrade():
    return ""
    # ### commands auto generated by Alembic - please adjust! ###
    # with op.batch_alter_table('metrics', schema=None) as batch_op:
    # batch_op.alter_column('timestamp_ht',
    # existing_type=postgresql.TIMESTAMP(timezone=True),
    # nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("metrics", schema=None) as batch_op:
        batch_op.alter_column(
            "timestamp_ht",
            existing_type=postgresql.TIMESTAMP(timezone=True),
            nullable=False,
        )

    # ### end Alembic commands ###