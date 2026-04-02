"""Initial schema: wines, wine_pricing, analysis_log

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID

from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── wines ────────────────────────────────────────────────────────────────
    op.create_table(
        "wines",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("producer", sa.String(255), nullable=False),
        sa.Column("region", sa.String(255)),
        sa.Column("country", sa.String(100)),
        sa.Column("appellation", sa.String(255)),
        sa.Column("varietal", sa.String(255)),
        sa.Column("wine_type", sa.String(50), nullable=False),
        sa.Column("avg_retail_price", sa.Numeric(10, 2)),
        sa.Column("price_tier", sa.String(20)),
        sa.Column("aliases", JSON),
        sa.Column("description", sa.Text),
        sa.Column("normalized_name", sa.String(500)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # ── wine_pricing ─────────────────────────────────────────────────────────
    op.create_table(
        "wine_pricing",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("wine_id", sa.String(100), sa.ForeignKey("wines.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vintage", sa.Integer),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("min_price", sa.Numeric(10, 2)),
        sa.Column("max_price", sa.Numeric(10, 2)),
        sa.Column("avg_price", sa.Numeric(10, 2)),
        sa.Column("median_price", sa.Numeric(10, 2)),
        sa.Column("num_listings", sa.Integer),
        sa.Column("currency", sa.String(10), server_default="USD"),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("raw_data", JSON),
    )
    op.create_index("ix_wine_pricing_wine_id", "wine_pricing", ["wine_id"])
    op.create_index("ix_wine_pricing_vintage", "wine_pricing", ["wine_id", "vintage"])

    # ── analysis_log ─────────────────────────────────────────────────────────
    op.create_table(
        "analysis_log",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("menu_text", sa.Text, nullable=False),
        sa.Column("menu_price", sa.Numeric(10, 2)),
        sa.Column("identified_wine_id", sa.String(100)),
        sa.Column("confidence_score", sa.Numeric(5, 4)),
        sa.Column("fairness_score", sa.Integer),
        sa.Column("verdict", sa.String(50)),
        sa.Column("venue_id", sa.String(255)),
        sa.Column(
            "analyzed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_analysis_log_wine_id", "analysis_log", ["identified_wine_id"])
    op.create_index("ix_analysis_log_venue_id", "analysis_log", ["venue_id"])
    op.create_index("ix_analysis_log_analyzed_at", "analysis_log", ["analyzed_at"])


def downgrade() -> None:
    op.drop_table("analysis_log")
    op.drop_table("wine_pricing")
    op.drop_table("wines")
