
import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    JSON,
    Enum,
    ForeignKey,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.models.package import PackageTypeEnum

# ============================================================
# HERO PACKAGE TYPE
# Reuses the same categories as Package.package_type
# ============================================================



class HeroSlide(Base):
    __tablename__ = "hero_slides"

    # ============================================================
    # PRIMARY KEY
    # ============================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # ============================================================
    # HERO IMAGES
    # ============================================================

  
    image = Column(
        JSON,
        nullable=False,
    )

  

    image_mobile = Column(
        JSON,
        nullable=True,
    )


    image_position = Column(
        String(30),
        nullable=True,
        default="center",
        server_default="center",
    )

    content_position = Column(
        String(20),
        nullable=False,
        default="middle-left",
        server_default="middle-left",
    )


    overlay_strength = Column(
        String(10),
        nullable=False,
        default="medium",
        server_default="medium",
    )

    # ============================================================
    # HERO CONTENT
    # ============================================================

    # Small text above headline
    #
    # Example:
    # "Summer Escape"

    badge = Column(
        String(150),
        nullable=True,
    )

    # Main hero heading

    headline = Column(
        String(250),
        nullable=False,
    )

    # Supporting text

    subtext = Column(
        String(1000),
        nullable=True,
    )

    # ============================================================
    # PACKAGE CATEGORY
    # ============================================================

    # Determines the main package section promoted by the hero.
    #
    # Example:
    # family
    #
    # Frontend can generate:
    #
    # "Explore Family Packages"
    #
    # and route to:
    #
    # /packages?type=family

    package_type = Column(
        Enum(PackageTypeEnum),
        nullable=True,
        index=True,
    )

    # ============================================================
    # OPTIONAL SPECIFIC PACKAGE
    # ============================================================

    # Optional specific package selected by admin.
    #
    # The admin UI should only show packages belonging to
    # the selected package_type.
    #
    # Example:
    #
    # package_type = beach
    #
    # package_id = 17
    #
    # Package #17:
    # "Goa Beach Escape"
    #
    # Frontend can then generate:
    #
    # "Explore Goa Beach Escape"
    #
    # and route using the Package.slug:
    #
    # /packages/goa-beach-escape

    package_id = Column(
        Integer,
        ForeignKey("packages.id"),
        nullable=True,
        index=True,
    )

    # SQLAlchemy relationship to Package

    package = relationship(
        "Package",
        foreign_keys=[package_id],
    )

    # ============================================================
    # PROMOTIONAL TEXT
    # ============================================================

    # Optional promotional text specific to this hero.
    #
    # Examples:
    #
    # "Save up to ₹5,000"
    # "Early Bird Offer"
    # "Starting from ₹18,999"

    offer_text = Column(
        String(250),
        nullable=True,
    )

    # ============================================================
    # HOMEPAGE CAROUSEL ORDER
    # ============================================================

    # 1, 2, 3, ...

    display_order = Column(
        Integer,
        nullable=False,
        default=0,
        index=True,
    )

    # ============================================================
    # VISIBILITY
    # ============================================================

    # Manual admin-controlled visibility.
    #
    # True  = eligible to appear
    # False = hidden

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    # ============================================================
    # SCHEDULING
    # ============================================================

    # Optional campaign start.
    #
    # NULL = no start restriction.

    starts_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Optional campaign end.
    #
    # NULL = no end restriction.

    ends_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ============================================================
    # TIMESTAMPS
    # ============================================================

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        server_default=func.now(),
    )





