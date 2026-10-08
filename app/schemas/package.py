

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# =========================================================
# ENUMS
# =========================================================


class StatusEnum(str, Enum):
    draft = "draft"
    published = "published"


class PackageTypeEnum(str, Enum):
    pilgrimage = "pilgrimage"
    mountains_adventure = "mountains_adventure"
    romantic = "romantic"
    international = "international"
    beach = "beach"
    family = "family"
    wildlife_nature = "wildlife_nature"


# =========================================================
# NESTED SCHEMAS
# =========================================================


class ItineraryItem(BaseModel):
    day: int = Field(
        gt=0,
    )

    title: str = Field(
        min_length=1,
    )

    description: str = Field(
        min_length=1,
    )

    image: Optional[str] = None


class ImageObject(BaseModel):
    """
    Matches the object returned by /uploads/image
    and the object stored by ImageUploadField.jsx.
    """

    url: str = Field(
        min_length=1,
    )

    public_id: Optional[str] = None


# =========================================================
# PACKAGE CREATE
# =========================================================


class PackageCreate(BaseModel):
    # ---------------------------------------------------------
    # Basic package information
    # ---------------------------------------------------------

    title: str = Field(
        min_length=3,
        max_length=200,
    )

    # Kept for backward compatibility / display.
    # Backend should derive this from destination_id.
    destination:Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    # Authoritative relationship to most_visited.id
    destination_id: Optional[int] = Field(
        gt=0,
    )

    # Optional relationship to seasoned_destinations.id
    seasoned_destination_id: Optional[int] = Field(
        default=None,
        gt=0,
    )

    # ---------------------------------------------------------
    # Package classification
    # ---------------------------------------------------------

    package_type: PackageTypeEnum = PackageTypeEnum.family

    # ---------------------------------------------------------
    # Display ordering
    # ---------------------------------------------------------

    display_order: int = Field(
        default=0,
        ge=0,
    )

    # ---------------------------------------------------------
    # Package discovery / collection flags
    # ---------------------------------------------------------

    is_popular: bool = False

    is_recommended: bool = False

    is_trending: bool = False

    is_featured: bool = False

    is_new: bool = False

    is_most_visited: bool = False

    # ---------------------------------------------------------
    # Pricing & duration
    # ---------------------------------------------------------

    price: Decimal = Field(
        gt=0,
    )

    duration_days: int = Field(
        gt=0,
    )

    duration_nights: int = Field(
        default=0,
        ge=0,
    )

    # ---------------------------------------------------------
    # Description
    # ---------------------------------------------------------

    description: Optional[str] = None

    # ---------------------------------------------------------
    # Images
    # ---------------------------------------------------------

    images: list[ImageObject] = Field(
        default_factory=list,
    )

    # ---------------------------------------------------------
    # Itinerary
    # ---------------------------------------------------------

    itinerary: list[ItineraryItem] = Field(
        default_factory=list,
    )

    # ---------------------------------------------------------
    # Facilities
    # ---------------------------------------------------------

    facilities: list[str] = Field(
        default_factory=list,
    )

    # ---------------------------------------------------------
    # Inclusions
    # ---------------------------------------------------------

    inclusions: list[str] = Field(
        default_factory=list,
    )

    # ---------------------------------------------------------
    # Exclusions
    # ---------------------------------------------------------

    exclusions: list[str] = Field(
        default_factory=list,
    )

    # ---------------------------------------------------------
    # Terms & Conditions
    # ---------------------------------------------------------

    terms_and_conditions: Optional[str] = None

    # ---------------------------------------------------------
    # Cancellation Policy
    # ---------------------------------------------------------

    cancellation_policy: Optional[str] = None

    # ---------------------------------------------------------
    # Publishing status
    # ---------------------------------------------------------

    status: StatusEnum = StatusEnum.draft


# =========================================================
# PACKAGE UPDATE
# =========================================================


class PackageUpdate(BaseModel):
    # ---------------------------------------------------------
    # Basic package information
    # ---------------------------------------------------------

    title: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=200,
    )

    # Kept for backward compatibility / display.
    destination: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    # Authoritative relationship to most_visited.id
    destination_id: Optional[int] = Field(
        default=None,
        gt=0,
    )

    # Optional relationship to seasoned_destinations.id
    seasoned_destination_id: Optional[int] = Field(
        default=None,
        gt=0,
    )

    # ---------------------------------------------------------
    # Package classification
    # ---------------------------------------------------------

    package_type: Optional[PackageTypeEnum] = None

    # ---------------------------------------------------------
    # Display ordering
    # ---------------------------------------------------------

    display_order: Optional[int] = Field(
        default=None,
        ge=0,
    )

    # ---------------------------------------------------------
    # Package discovery / collection flags
    # ---------------------------------------------------------

    is_popular: Optional[bool] = None

    is_recommended: Optional[bool] = None

    is_trending: Optional[bool] = None

    is_featured: Optional[bool] = None

    is_new: Optional[bool] = None

    is_most_visited: Optional[bool] = None

    # ---------------------------------------------------------
    # Pricing & duration
    # ---------------------------------------------------------

    price: Optional[Decimal] = Field(
        default=None,
        gt=0,
    )

    duration_days: Optional[int] = Field(
        default=None,
        gt=0,
    )

    duration_nights: Optional[int] = Field(
        default=None,
        ge=0,
    )

    # ---------------------------------------------------------
    # Description
    # ---------------------------------------------------------

    description: Optional[str] = None

    # ---------------------------------------------------------
    # Images
    # ---------------------------------------------------------

    images: Optional[list[ImageObject]] = None

    # ---------------------------------------------------------
    # Itinerary
    # ---------------------------------------------------------

    itinerary: Optional[list[ItineraryItem]] = None

    # ---------------------------------------------------------
    # Facilities
    # ---------------------------------------------------------

    facilities: Optional[list[str]] = None

    # ---------------------------------------------------------
    # Inclusions
    # ---------------------------------------------------------

    inclusions: Optional[list[str]] = None

    # ---------------------------------------------------------
    # Exclusions
    # ---------------------------------------------------------

    exclusions: Optional[list[str]] = None

    # ---------------------------------------------------------
    # Terms & Conditions
    # ---------------------------------------------------------

    terms_and_conditions: Optional[str] = None

    # ---------------------------------------------------------
    # Cancellation Policy
    # ---------------------------------------------------------

    cancellation_policy: Optional[str] = None

    # ---------------------------------------------------------
    # Publishing status
    # ---------------------------------------------------------

    status: Optional[StatusEnum] = None


# =========================================================
# PACKAGE OUTPUT
# =========================================================


class PackageOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    # ---------------------------------------------------------
    # Basic package information
    # ---------------------------------------------------------

    id: int

    title: str

    slug: str

    # Existing display / compatibility field
    destination: Optional[str]

    # Authoritative relationship to most_visited.id
    destination_id: Optional[int]

    # Optional relationship to seasoned_destinations.id
    seasoned_destination_id: Optional[int] = None

    # ---------------------------------------------------------
    # Package classification
    # ---------------------------------------------------------

    package_type: PackageTypeEnum

    # ---------------------------------------------------------
    # Display ordering
    # ---------------------------------------------------------

    display_order: int

    # ---------------------------------------------------------
    # Package discovery / collection flags
    # ---------------------------------------------------------

    is_popular: bool

    is_recommended: bool

    is_trending: bool

    is_featured: bool

    is_new: bool

    is_most_visited: bool

    # ---------------------------------------------------------
    # Pricing & duration
    # ---------------------------------------------------------

    price: Decimal

    duration_days: int

    duration_nights: int

    # ---------------------------------------------------------
    # Description
    # ---------------------------------------------------------

    description: Optional[str] = None

    # ---------------------------------------------------------
    # Images
    # ---------------------------------------------------------

    images: list[ImageObject] = Field(
        default_factory=list,
    )

    # ---------------------------------------------------------
    # Itinerary
    # ---------------------------------------------------------

    itinerary: list[ItineraryItem] = Field(
        default_factory=list,
    )

    # ---------------------------------------------------------
    # Facilities
    # ---------------------------------------------------------

    facilities: list[str] = Field(
        default_factory=list,
    )

    # ---------------------------------------------------------
    # Inclusions
    # ---------------------------------------------------------

    inclusions: list[str] = Field(
        default_factory=list,
    )

    # ---------------------------------------------------------
    # Exclusions
    # ---------------------------------------------------------

    exclusions: list[str] = Field(
        default_factory=list,
    )

    # ---------------------------------------------------------
    # Terms & Conditions
    # ---------------------------------------------------------

    terms_and_conditions: Optional[str] = None

    # ---------------------------------------------------------
    # Cancellation Policy
    # ---------------------------------------------------------

    cancellation_policy: Optional[str] = None

    # ---------------------------------------------------------
    # Publishing status
    # ---------------------------------------------------------

    status: StatusEnum

    # ---------------------------------------------------------
    # Metadata
    # ---------------------------------------------------------

    created_by: Optional[int] = None

    created_at: datetime

    updated_at: Optional[datetime] = None
















