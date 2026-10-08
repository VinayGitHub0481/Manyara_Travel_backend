


from sqlalchemy import Column, Integer, String, JSON, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.db.database import Base


class SiteSettings(Base):
    """Singleton table - always exactly one row (id=1)."""

    __tablename__ = "site_settings"

    id = Column(Integer, primary_key=True, index=True)

    # ============================================================
    # Website / marketing settings
    # ============================================================

    offer_banner_text = Column(String(300), nullable=True)

    homepage_headline = Column(String(200), nullable=True)

    trust_line = Column(String(200), nullable=True)

    # ============================================================
    # Top Info Bar
    # ============================================================

    # Controls whether the Top Info Bar is displayed
    # on the public website.
    top_bar_enabled = Column(
        Boolean,
        default=True,
        nullable=False,
        server_default="1",
    )

    # First location shown in the Top Info Bar
    # Example: Hyderabad
    top_bar_location_1 = Column(
        String(80),
        nullable=True,
    )

    # Second location shown in the Top Info Bar
    # Example: Bengaluru
    top_bar_location_2 = Column(
        String(80),
        nullable=True,
    )

    top_bar_social_3_name = Column(String(80), nullable=True)
    top_bar_social_3_url  = Column(String(500), nullable=True)
    top_bar_social_4_name = Column(String(80), nullable=True)
    top_bar_social_4_url  = Column(String(500), nullable=True)

    # Trust / traveller metric
    # Example: 5000+ successful travelers
    top_bar_traveller_text = Column(
        String(100),
        nullable=True,
    )

    # First social media link
    # Example:
    # name = Instagram
    # url = https://instagram.com/onatripholidays
    top_bar_social_1_name = Column(
        String(30),
        nullable=True,
    )

    top_bar_social_1_url = Column(
        String(500),
        nullable=True,
    )

    # Second social media link
    # Example:
    # name = YouTube
    # url = https://youtube.com/...
    top_bar_social_2_name = Column(
        String(30),
        nullable=True,
    )

    top_bar_social_2_url = Column(
        String(500),
        nullable=True,
    )

    # ============================================================
    # Contact information
    # ============================================================

    phone_number = Column(
        String(30),
        nullable=True,
    )

    whatsapp_number = Column(
        String(30),
        nullable=True,
    )

    company_address = Column(
        Text,
        nullable=True,
    )

    address_url = Column(
        String(500),
        nullable=True,
    )

    # ============================================================
    # Homepage featured collections
    # ============================================================

    featured_international = Column(
        JSON,
        nullable=True,
    )  # list[str]

    featured_national = Column(
        JSON,
        nullable=True,
    )  # list[str]

    # ============================================================
    # Last updated timestamp
    # ============================================================

    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        server_default=func.now(),
    )

