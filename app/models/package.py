

import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class StatusEnum(str, enum.Enum):
    draft = "draft"
    published = "published"


class PackageTypeEnum(str, enum.Enum):
    pilgrimage = "pilgrimage"
    mountains_adventure = "mountains_adventure"
    romantic = "romantic"
    international = "international"
    beach = "beach"
    family = "family"
    wildlife_nature = "wildlife_nature"


class Package(Base):
    __tablename__ = "packages"

    # ---------------------------------------------------------
    # Basic package information
    # ---------------------------------------------------------

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    title = Column(
        String(200),
        nullable=False,
    )

    slug = Column(
        String(220),
        unique=True,
        index=True,
        nullable=False,
    )

    # ---------------------------------------------------------
    # Destination
    # ---------------------------------------------------------
    #
    # A package belongs to EXACTLY ONE:
    #
    # 1. Normal destination
    #       destination_id -> most_visited.id
    #
    # OR
    #
    # 2. Seasonal destination
    #       seasoned_destination_id -> seasoned_destinations.id
    #
    # The service layer enforces this XOR rule.
    #
    # `destination` is retained for backward compatibility and
    # display/filtering. It is NULL for seasonal packages.
    # ---------------------------------------------------------

    destination = Column(
        String(150),
        nullable=True,
        index=True,
    )

    destination_id = Column(
        Integer,
        ForeignKey(
            "most_visited.id",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    seasoned_destination_id = Column(
        Integer,
        ForeignKey(
            "seasoned_destinations.id",
            ondelete="SET NULL",
            onupdate="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    # ---------------------------------------------------------
    # Package classification
    # ---------------------------------------------------------

    package_type = Column(
        Enum(PackageTypeEnum),
        nullable=False,
        index=True,
        default=PackageTypeEnum.family,
    )

    # ---------------------------------------------------------
    # Display ordering
    # ---------------------------------------------------------

    display_order = Column(
        Integer,
        nullable=False,
        default=0,
        index=True,
    )

    # ---------------------------------------------------------
    # Package discovery / collection flags
    # ---------------------------------------------------------

    is_popular = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    is_recommended = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    is_trending = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    is_featured = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    is_new = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    is_most_visited = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    # ---------------------------------------------------------
    # Pricing & duration
    # ---------------------------------------------------------

    price = Column(
        Numeric(10, 2),
        nullable=False,
    )

    duration_days = Column(
        Integer,
        nullable=False,
    )

    duration_nights = Column(
        Integer,
        nullable=False,
    )

    # ---------------------------------------------------------
    # Description
    # ---------------------------------------------------------

    description = Column(
        Text,
        nullable=True,
    )

    # ---------------------------------------------------------
    # Images
    # ---------------------------------------------------------

    images = Column(
        JSON,
        nullable=True,
    )

    # ---------------------------------------------------------
    # Itinerary
    # ---------------------------------------------------------

    itinerary = Column(
        JSON,
        nullable=True,
    )

    # ---------------------------------------------------------
    # Facilities
    # ---------------------------------------------------------

    facilities = Column(
        JSON,
        nullable=False,
        default=list,
    )

    # ---------------------------------------------------------
    # Inclusions
    # ---------------------------------------------------------

    inclusions = Column(
        JSON,
        nullable=False,
        default=list,
    )

    # ---------------------------------------------------------
    # Exclusions
    # ---------------------------------------------------------

    exclusions = Column(
        JSON,
        nullable=False,
        default=list,
    )

    # ---------------------------------------------------------
    # Terms & Conditions
    # ---------------------------------------------------------

    terms_and_conditions = Column(
        Text,
        nullable=True,
    )

    # ---------------------------------------------------------
    # Cancellation Policy
    # ---------------------------------------------------------

    cancellation_policy = Column(
        Text,
        nullable=True,
    )

    # ---------------------------------------------------------
    # Publishing status
    # ---------------------------------------------------------

    status = Column(
        Enum(StatusEnum),
        default=StatusEnum.draft,
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # Creator
    # ---------------------------------------------------------

    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
    )

    # ---------------------------------------------------------
    # Timestamps
    # ---------------------------------------------------------

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
    )

    # ---------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------

    creator = relationship(
        "User",
    )

    # ---------------------------------------------------------
    # Relationship to normal destination
    # ---------------------------------------------------------

    destination_obj = relationship(
        "MostVisited",
        back_populates="packages",
        foreign_keys=[destination_id],
    )

    # ---------------------------------------------------------
    # Relationship to seasonal destination
    # ---------------------------------------------------------

    seasoned_destination_obj = relationship(
        "SeasonedDestination",
        back_populates="packages",
        foreign_keys=[seasoned_destination_id],
    )

    # ---------------------------------------------------------
    # Relationship to package batches
    # ---------------------------------------------------------

    batches = relationship(
        "PackageBatch",
        back_populates="package",
        cascade="all, delete-orphan",
    )













































# import enum

# from sqlalchemy import (
#     Column,
#     Integer,
#     String,
#     Text,
#     Numeric,
#     Enum,
#     DateTime,
#     ForeignKey,
#     JSON,
#     Boolean,
# )
# from sqlalchemy.sql import func
# from sqlalchemy.orm import relationship
# from app.db.database import Base


# class StatusEnum(str, enum.Enum):
#     draft = "draft"
#     published = "published"


# class PackageTypeEnum(str, enum.Enum):
#     pilgrimage = "pilgrimage"
#     mountains_adventure = "mountains_adventure"
#     romantic = "romantic"
#     international = "international"
#     beach = "beach"
#     family = "family"
#     wildlife_nature = "wildlife_nature"


# class Package(Base):
#     __tablename__ = "packages"

#     # ---------------------------------------------------------
#     # Basic package information
#     # ---------------------------------------------------------

#     id = Column(
#         Integer,
#         primary_key=True,
#         index=True,
#     )

#     title = Column(
#         String(200),
#         nullable=False,
#     )

#     slug = Column(
#         String(220),
#         unique=True,
#         index=True,
#         nullable=False,
#     )

#     # ---------------------------------------------------------
#     # Destination
#     # ---------------------------------------------------------

#     # Existing destination name.
#     # Keep this for backward compatibility and display/filtering.
#     destination = Column(
#         String(150),
#         nullable=False,
#         index=True,
#     )

#     # New proper relationship to most_visited.id
#     destination_id = Column(
#         Integer,
#         ForeignKey("most_visited.id"),
#         nullable=True,
#         index=True,
#     )

#     seasoned_destination_id = Column(
#      Integer,
#     ForeignKey("seasoned_destinations.id"),
#     nullable=True,
#     index=True,
# )

#     # ---------------------------------------------------------
#     # Package classification
#     # ---------------------------------------------------------

#     package_type = Column(
#         Enum(PackageTypeEnum),
#         nullable=False,
#         index=True,
#         default=PackageTypeEnum.family,
#     )

#     # ---------------------------------------------------------
#     # Display ordering
#     # ---------------------------------------------------------

#     display_order = Column(
#         Integer,
#         nullable=False,
#         default=0,
#         index=True,
#     )

#     # ---------------------------------------------------------
#     # Package discovery / collection flags
#     # ---------------------------------------------------------

#     is_popular = Column(
#         Boolean,
#         nullable=False,
#         default=False,
#         index=True,
#     )

#     is_recommended = Column(
#         Boolean,
#         nullable=False,
#         default=False,
#         index=True,
#     )

#     is_trending = Column(
#         Boolean,
#         nullable=False,
#         default=False,
#         index=True,
#     )

#     is_featured = Column(
#         Boolean,
#         nullable=False,
#         default=False,
#         index=True,
#     )

#     is_new = Column(
#         Boolean,
#         nullable=False,
#         default=False,
#         index=True,
#     )

#     is_most_visited = Column(
#         Boolean,
#         nullable=False,
#         default=False,
#         index=True,
#     )

#     # ---------------------------------------------------------
#     # Pricing & duration
#     # ---------------------------------------------------------

#     price = Column(
#         Numeric(10, 2),
#         nullable=False,
#     )

#     duration_days = Column(
#         Integer,
#         nullable=False,
#     )

#     duration_nights = Column(
#         Integer,
#         nullable=False,
#     )

#     # ---------------------------------------------------------
#     # Description
#     # ---------------------------------------------------------

#     description = Column(
#         Text,
#     )

#     # ---------------------------------------------------------
#     # Images
#     # ---------------------------------------------------------

#     images = Column(
#         JSON,
#     )

#     # ---------------------------------------------------------
#     # Itinerary
#     # ---------------------------------------------------------

#     itinerary = Column(
#         JSON,
#     )

#     # ---------------------------------------------------------
#     # Facilities
#     # ---------------------------------------------------------

#     facilities = Column(
#         JSON,
#         nullable=False,
#         default=list,
#     )

#     # ---------------------------------------------------------
#     # Inclusions
#     # ---------------------------------------------------------

#     inclusions = Column(
#         JSON,
#         nullable=False,
#         default=list,
#     )

#     # ---------------------------------------------------------
#     # Exclusions
#     # ---------------------------------------------------------

#     exclusions = Column(
#         JSON,
#         nullable=False,
#         default=list,
#     )

#     # ---------------------------------------------------------
#     # Terms & Conditions
#     # ---------------------------------------------------------

#     terms_and_conditions = Column(
#         Text,
#         nullable=True,
#     )

#     # ---------------------------------------------------------
#     # Cancellation Policy
#     # ---------------------------------------------------------

#     cancellation_policy = Column(
#         Text,
#         nullable=True,
#     )

#     # ---------------------------------------------------------
#     # Publishing status
#     # ---------------------------------------------------------

#     status = Column(
#         Enum(StatusEnum),
#         default=StatusEnum.draft,
#         nullable=False,
#         index=True,
#     )

#     # ---------------------------------------------------------
#     # Creator
#     # ---------------------------------------------------------

#     created_by = Column(
#         Integer,
#         ForeignKey("users.id"),
#     )

#     # ---------------------------------------------------------
#     # Timestamps
#     # ---------------------------------------------------------

#     created_at = Column(
#         DateTime(timezone=True),
#         server_default=func.now(),
#     )

#     updated_at = Column(
#         DateTime(timezone=True),
#         onupdate=func.now(),
#     )

#     # ---------------------------------------------------------
#     # Relationships
#     # ---------------------------------------------------------

#     creator = relationship(
#         "User",
#     )

#     # Relationship to MostVisited
#     destination_obj = relationship(
#         "MostVisited",
#         back_populates="packages",
#     )

#     # Relationship to SeasonalDestination
#     seasoned_destination_obj = relationship(
#         "SeasonedDestination",
#         back_populates="packages",
#     )

#     batches = relationship(
#         "PackageBatch",
#         back_populates="package",
#         cascade="all, delete-orphan",
#     )
