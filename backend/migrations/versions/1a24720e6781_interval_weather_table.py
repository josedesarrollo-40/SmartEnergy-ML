"""interval_weather table

Revision ID: 1a24720e6781
Revises: c5d2502fb8e3
Create Date: 2026-11-07 23:48:07.605236

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a24720e6781'
down_revision: Union[str, None] = 'c5d2502fb8e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('interval_weather',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('start_reading_id', sa.Integer(), nullable=False),
    sa.Column('end_reading_id', sa.Integer(), nullable=False),
    sa.Column('temp_avg_c', sa.Numeric(precision=5, scale=1), nullable=True),
    sa.Column('temp_max_c', sa.Numeric(precision=5, scale=1), nullable=True),
    sa.Column('temp_min_c', sa.Numeric(precision=5, scale=1), nullable=True),
    sa.Column('humidity_avg_pct', sa.Numeric(precision=5, scale=1), nullable=True),
    sa.Column('observation_count', sa.Integer(), server_default='0', nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('source', sa.String(length=32), nullable=False),
    sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint("status in ('pending', 'available', 'failed')", name='ck_interval_weather_status'),
    sa.CheckConstraint('observation_count >= 0', name='ck_interval_weather_obs_non_negative'),
    sa.ForeignKeyConstraint(['end_reading_id'], ['meter_readings.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['start_reading_id'], ['meter_readings.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('start_reading_id', 'end_reading_id', name='uq_interval_weather_pair')
    )
    with op.batch_alter_table('interval_weather', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_interval_weather_end_reading_id'), ['end_reading_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interval_weather_start_reading_id'), ['start_reading_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('interval_weather', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_interval_weather_start_reading_id'))
        batch_op.drop_index(batch_op.f('ix_interval_weather_end_reading_id'))

    op.drop_table('interval_weather')
