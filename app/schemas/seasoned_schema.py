

from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# =========================================================
# PACKAGE SUMMARY
# =========================================================

class SeasonedDestinationPackageResponse(BaseModel):
    """
    Lightweight package information used when returning
    packages belonging to a seasoned destination.
    """

    id: int
    title: str
    slug: str
    destination: Optional[str]

    price: Decimal
    duration_days: int
    duration_nights: int

    images: Optional[Any] = None

    package_type: str

    status: str

    is_popular: bool
    is_recommended: bool
    is_trending: bool
    is_featured: bool
    is_new: bool
    is_most_visited: bool

    display_order: int

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# BASE
# =========================================================

class SeasonedDestinationBase(BaseModel):
    place_name: str = Field(
        ...,
        min_length=1,
        max_length=150,
    )

    slug: str = Field(
        ...,
        min_length=1,
        max_length=180,
    )

    image: Any

    description: Optional[str] = None

    season_label: Optional[str] = Field(
        default=None,
        max_length=150,
    )

    season_start_date: Optional[date] = None

    season_end_date: Optional[date] = None

    best_time_to_visit: Optional[str] = Field(
        default=None,
        max_length=255,
    )

    starting_from: Optional[Decimal] = None

    display_order: int = 0

    status: str = "published"


# =========================================================
# CREATE
# =========================================================

class SeasonedDestinationCreate(SeasonedDestinationBase):
    """
    Schema used when creating a new seasoned destination.
    """

    created_by: Optional[int] = None


# =========================================================
# UPDATE
# =========================================================

class SeasonedDestinationUpdate(BaseModel):
    """
    All fields are optional so the admin can update
    only the fields that have changed.
    """

    place_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    slug: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=180,
    )

    image: Optional[Any] = None

    description: Optional[str] = None

    season_label: Optional[str] = Field(
        default=None,
        max_length=150,
    )

    season_start_date: Optional[date] = None

    season_end_date: Optional[date] = None

    best_time_to_visit: Optional[str] = Field(
        default=None,
        max_length=255,
    )

    starting_from: Optional[Decimal] = None

    display_order: Optional[int] = None

    status: Optional[str] = None


# =========================================================
# RESPONSE
# =========================================================

class SeasonedDestinationResponse(SeasonedDestinationBase):
    """
    Complete seasoned destination response.
    """

    id: int

    created_by: Optional[int] = None

    created_at: datetime

    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# DETAIL RESPONSE WITH PACKAGES
# =========================================================

class SeasonedDestinationDetailResponse(SeasonedDestinationResponse):
    """
    Detailed seasoned destination response including
    all packages associated with this destination.
    """

    packages: List[SeasonedDestinationPackageResponse] = []

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# LIST RESPONSE
# =========================================================

class SeasonedDestinationListResponse(BaseModel):
    """
    Response used for the seasoned destination listing.
    """

    id: int

    place_name: str

    slug: str

    image: Any

    description: Optional[str] = None

    season_label: Optional[str] = None

    season_start_date: Optional[date] = None

    season_end_date: Optional[date] = None

    best_time_to_visit: Optional[str] = None

    starting_from: Optional[Decimal] = None

    display_order: int

    status: str

    model_config = ConfigDict(from_attributes=True)

