"""add number plate detections table

Revision ID: add_number_plate_detections
Revises: add_password_reset_fields
Create Date: 2025-04-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_number_plate_detections'
down_revision = 'add_password_reset_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Create number_plate_detections table
    op.create_table(
        'number_plate_detections',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('report_id', sa.String(50), sa.ForeignKey('detection_history.report_id'), nullable=True),
        sa.Column('plate_number', sa.String(50), nullable=False),
        sa.Column('confidence', sa.Float(), default=0.0),
        sa.Column('bbox_x1', sa.Integer(), nullable=True),
        sa.Column('bbox_y1', sa.Integer(), nullable=True),
        sa.Column('bbox_x2', sa.Integer(), nullable=True),
        sa.Column('bbox_y2', sa.Integer(), nullable=True),
        sa.Column('region', sa.String(10), nullable=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('plate_image', sa.Text(), nullable=True)
    )


def downgrade():
    op.drop_table('number_plate_detections')
