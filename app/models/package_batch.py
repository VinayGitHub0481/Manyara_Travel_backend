

import enum

from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    Enum,
    Date,
    DateTime,
    ForeignKey,
    JSON,
    String,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


# =========================================================
# Batch Status
# =========================================================
class BatchStatusEnum(str, enum.Enum):
    draft = "draft"
    published = "published"


# =========================================================
# Duration Mode
# =========================================================
# default = use Package duration_days / duration_nights
# custom  = use this batch's days / nights
# =========================================================
class BatchDurationModeEnum(str, enum.Enum):
    default = "default"
    custom = "custom"


# =========================================================
# Price Mode
# =========================================================
# default = use Package price
# custom  = use batch price_per_person
# =========================================================
class BatchPriceModeEnum(str, enum.Enum):
    default = "default"
    custom = "custom"


# =========================================================
# Itinerary Mode
# =========================================================
# default = use Package itinerary
# custom  = use custom_itinerary
# =========================================================
class BatchItineraryModeEnum(str, enum.Enum):
    default = "default"
    custom = "custom"


# =========================================================
# Inclusions Mode
# =========================================================
# default = use Package inclusions
# custom  = use custom_inclusions
# =========================================================
class BatchInclusionsModeEnum(str, enum.Enum):
    default = "default"
    custom = "custom"


# =========================================================
# Exclusions Mode
# =========================================================
# default = use Package exclusions
# custom  = use custom_exclusions
# =========================================================
class BatchExclusionsModeEnum(str, enum.Enum):
    default = "default"
    custom = "custom"


# =========================================================
# Terms & Conditions Mode
# =========================================================
# default = use Package terms_and_conditions
# custom  = use custom_terms_and_conditions
# =========================================================
class BatchTermsModeEnum(str, enum.Enum):
    default = "default"
    custom = "custom"


# =========================================================
# Cancellation Policy Mode
# =========================================================
# default = use Package cancellation_policy
# custom  = use custom_cancellation_policy
# =========================================================
class BatchCancellationModeEnum(str, enum.Enum):
    default = "default"
    custom = "custom"


# =========================================================
# Package Batch
# =========================================================
class PackageBatch(Base):
    __tablename__ = "package_batches"

    # ---------------------------------------------------------
    # Primary Key
    # ---------------------------------------------------------
    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    slug = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # Related Package
    # ---------------------------------------------------------
    #
    # Every batch belongs to one existing package.
    #
    # Example:
    #
    # Package:
    #     Kerala Holiday
    #
    # Batch:
    #     Kerala Holiday - 28 Sep 2026
    #
    # ---------------------------------------------------------
    package_id = Column(
        Integer,
        ForeignKey("packages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # Display order
    # ---------------------------------------------------------
    #
    # Position INSIDE the package (1, 2, 3, ...).
    # Lower numbers appear first. Kept unique and sequential per
    # package by package_batch_service._place_in_order.
    #
    # ---------------------------------------------------------
    display_order = Column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        index=True,
    )

    # ---------------------------------------------------------
    # Batch Dates
    # ---------------------------------------------------------
    departure_date = Column(
        Date,
        nullable=False,
        index=True,
    )

    return_date = Column(
        Date,
        nullable=False,
    )

    # =========================================================
    # Duration
    # =========================================================
    #
    # default:
    #     Use package.duration_days / duration_nights
    #
    # custom:
    #     Use batch.days / nights
    #
    # =========================================================

    duration_mode = Column(
        Enum(BatchDurationModeEnum),
        nullable=False,
        default=BatchDurationModeEnum.default,
    )

    days = Column(
        Integer,
        nullable=True,
    )

    nights = Column(
        Integer,
        nullable=True,
    )

    # =========================================================
    # Price
    # =========================================================
    #
    # default:
    #     Use package.price
    #
    # custom:
    #     Use batch.price_per_person
    #
    # =========================================================

    price_mode = Column(
        Enum(BatchPriceModeEnum),
        nullable=False,
        default=BatchPriceModeEnum.default,
    )

    price_per_person = Column(
        Numeric(10, 2),
        nullable=True,
    )

    # =========================================================
    # Itinerary
    # =========================================================
    #
    # default:
    #     Use package.itinerary
    #
    # custom:
    #     Use custom_itinerary
    #
    # Example custom itinerary:
    #
    # [
    #     {
    #         "day": 1,
    #         "title": "Arrival",
    #         "description": "...",
    #         "image": "..."
    #     },
    #     {
    #         "day": 2,
    #         "title": "Sightseeing",
    #         "description": "...",
    #         "image": "..."
    #     }
    # ]
    #
    # =========================================================

    itinerary_mode = Column(
        Enum(BatchItineraryModeEnum),
        nullable=False,
        default=BatchItineraryModeEnum.default,
    )

    custom_itinerary = Column(
        JSON,
        nullable=True,
    )

    # =========================================================
    # Inclusions
    # =========================================================
    #
    # default:
    #     Use package.inclusions
    #
    # custom:
    #     Use custom_inclusions
    #
    # Example:
    #
    # [
    #     "Breakfast",
    #     "Airport pickup",
    #     "Private transportation"
    # ]
    #
    # =========================================================

    inclusions_mode = Column(
        Enum(BatchInclusionsModeEnum),
        nullable=False,
        default=BatchInclusionsModeEnum.default,
    )

    custom_inclusions = Column(
        JSON,
        nullable=True,
    )

    # =========================================================
    # Exclusions
    # =========================================================
    #
    # default:
    #     Use package.exclusions
    #
    # custom:
    #     Use custom_exclusions
    #
    # Example:
    #
    # [
    #     "Personal expenses",
    #     "Travel insurance",
    #     "Lunch"
    # ]
    #
    # =========================================================

    exclusions_mode = Column(
        Enum(BatchExclusionsModeEnum),
        nullable=False,
        default=BatchExclusionsModeEnum.default,
    )

    custom_exclusions = Column(
        JSON,
        nullable=True,
    )

    # =========================================================
    # Terms & Conditions
    # =========================================================
    #
    # default:
    #     Use package.terms_and_conditions
    #
    # custom:
    #     Use custom_terms_and_conditions
    #
    # JSON allows multiple terms to be stored as a list.
    #
    # Example:
    #
    # [
    #     "Valid government ID is required.",
    #     "Check-in time is 12 PM."
    # ]
    #
    # =========================================================

    terms_mode = Column(
        Enum(BatchTermsModeEnum),
        nullable=False,
        default=BatchTermsModeEnum.default,
    )

    custom_terms_and_conditions = Column(
        JSON,
        nullable=True,
    )

    # =========================================================
    # Cancellation Policy
    # =========================================================
    #
    # default:
    #     Use package.cancellation_policy
    #
    # custom:
    #     Use custom_cancellation_policy
    #
    # JSON allows multiple cancellation rules.
    #
    # Example:
    #
    # [
    #     "30+ days before departure: Full refund.",
    #     "15-29 days before departure: 50% refund.",
    #     "Less than 15 days: No refund."
    # ]
    #
    # =========================================================

    cancellation_mode = Column(
        Enum(BatchCancellationModeEnum),
        nullable=False,
        default=BatchCancellationModeEnum.default,
    )

    custom_cancellation_policy = Column(
        JSON,
        nullable=True,
    )

    # =========================================================
    # Availability
    # =========================================================
    #
    # This is manually controlled by admin because the website
    # currently uses enquiries rather than online booking.
    #
    # Examples:
    #     open
    #     limited
    #     almost_full
    #     full
    #     closed
    #
    # =========================================================

    availability = Column(
        String(50),
        nullable=True,
    )

    # =========================================================
    # Publishing Status
    # =========================================================

    status = Column(
        Enum(BatchStatusEnum),
        default=BatchStatusEnum.draft,
        nullable=False,
        index=True,
    )

    # =========================================================
    # Timestamps
    # =========================================================

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
    )

    # =========================================================
    # Relationships
    # =========================================================

    package = relationship(
        "Package",
        back_populates="batches",
    )



