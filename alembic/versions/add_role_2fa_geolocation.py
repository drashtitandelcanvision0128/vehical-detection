"""add role and 2fa fields to users, geolocation to detections

Revision ID: add_role_2fa_geolocation
Revises: add_password_reset_fields
Create Date: 2026-04-29 15:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_role_2fa_geolocation'
down_revision: Union[str, Sequence[str], None] = 'add_number_plate_detections'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add role, 2FA fields to users and geolocation to detection tables."""
    conn = op.get_bind()
    
    # Get existing columns for users table
    user_cols = {row[0] for row in conn.execute(sa.text(
        "SELECT column_name FROM information_schema.columns WHERE table_name='users'"
    )).fetchall()}
    
    # Add role column to users
    if 'role' not in user_cols:
        op.add_column('users', sa.Column('role', sa.String(length=20), nullable=True, server_default='user'))
    
    # Add 2FA columns to users
    if 'two_factor_enabled' not in user_cols:
        op.add_column('users', sa.Column('two_factor_enabled', sa.Integer(), nullable=True, server_default='0'))
    
    if 'two_factor_secret' not in user_cols:
        op.add_column('users', sa.Column('two_factor_secret', sa.String(length=255), nullable=True))
    
    # Add geolocation columns to image_detections
    img_cols = {row[0] for row in conn.execute(sa.text(
        "SELECT column_name FROM information_schema.columns WHERE table_name='image_detections'"
    )).fetchall()}
    
    if 'latitude' not in img_cols:
        op.add_column('image_detections', sa.Column('latitude', sa.Float(), nullable=True))
    if 'longitude' not in img_cols:
        op.add_column('image_detections', sa.Column('longitude', sa.Float(), nullable=True))
    
    # Add geolocation columns to video_detections
    vid_cols = {row[0] for row in conn.execute(sa.text(
        "SELECT column_name FROM information_schema.columns WHERE table_name='video_detections'"
    )).fetchall()}
    
    if 'latitude' not in vid_cols:
        op.add_column('video_detections', sa.Column('latitude', sa.Float(), nullable=True))
    if 'longitude' not in vid_cols:
        op.add_column('video_detections', sa.Column('longitude', sa.Float(), nullable=True))
    
    # Add geolocation columns to live_detections
    live_cols = {row[0] for row in conn.execute(sa.text(
        "SELECT column_name FROM information_schema.columns WHERE table_name='live_detections'"
    )).fetchall()}
    
    if 'latitude' not in live_cols:
        op.add_column('live_detections', sa.Column('latitude', sa.Float(), nullable=True))
    if 'longitude' not in live_cols:
        op.add_column('live_detections', sa.Column('longitude', sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema - remove role, 2FA fields and geolocation columns."""
    # Remove from users
    op.drop_column('users', 'two_factor_secret')
    op.drop_column('users', 'two_factor_enabled')
    op.drop_column('users', 'role')
    
    # Remove from detection tables
    op.drop_column('image_detections', 'longitude')
    op.drop_column('image_detections', 'latitude')
    op.drop_column('video_detections', 'longitude')
    op.drop_column('video_detections', 'latitude')
    op.drop_column('live_detections', 'longitude')
    op.drop_column('live_detections', 'latitude')
