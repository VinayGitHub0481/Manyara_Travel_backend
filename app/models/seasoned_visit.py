
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Numeric,
    JSON,
    Enum,
    ForeignKey,
    Date,
    DateTime,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class SeasonedDestination(Base):
    __tablename__ = "seasoned_destinations"

    id = Column(Integer, primary_key=True, index=True)

    # --------------------------------------------------
    # DESTINATION
    # --------------------------------------------------

    place_name = Column(
        String(150),
        nullable=False,
    )

    slug = Column(
        String(180),
        unique=True,
        nullable=False,
        index=True,
    )

    image = Column(
        JSON,
        nullable=False,
    )

    description = Column(
        Text,
        nullable=True,
    )

    # --------------------------------------------------
    # SEASON
    # --------------------------------------------------

    season_label = Column(
        String(150),
        nullable=True,
    )

    season_start_date = Column(
        Date,
        nullable=True,
    )

    season_end_date = Column(
        Date,
        nullable=True,
    )

    # --------------------------------------------------
    # TRAVEL DETAILS
    # --------------------------------------------------

    best_time_to_visit = Column(
        String(255),
        nullable=True,
    )

    starting_from = Column(
        Numeric(10, 2),
        nullable=True,
    )

    # --------------------------------------------------
    # DISPLAY
    # --------------------------------------------------

    display_order = Column(
        Integer,
        nullable=False,
        default=0,
        index=True,
    )

    status = Column(
        Enum("draft", "published"),
        nullable=False,
        default="published",
    )

    # --------------------------------------------------
    # AUDIT
    # --------------------------------------------------

    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        nullable=True,
        onupdate=func.now(),
    )

    # --------------------------------------------------
    # PACKAGES
    # --------------------------------------------------

    packages = relationship(
        "Package",
        back_populates="seasoned_destination_obj",
    )