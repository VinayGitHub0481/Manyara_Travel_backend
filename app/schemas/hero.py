


from datetime import datetime
from typing import Optional,Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.package import PackageTypeEnum


# ============================================================
# IMAGE
# ============================================================
ContentPosition = Literal[
    "top-left", "top-center", "top-right",
    "middle-left", "middle-center", "middle-right",
    "bottom-left", "bottom-center", "bottom-right",
]
OverlayStrength = Literal["none", "soft", "medium", "strong"]


class HeroImage(BaseModel):
    url: str = Field(
        min_length=1,
    )
    public_id: Optional[str] = None


# ============================================================
# BASE
# ============================================================


class HeroSlideBase(BaseModel):
    image_position: Optional[str] = Field(
        default="center",
        max_length=30,
    )

    content_position: ContentPosition = "middle-left"
    overlay_strength: OverlayStrength = "medium"

    badge: Optional[str] = Field(
        default=None,
        max_length=150,
    )

    headline: str = Field(
        min_length=1,
        max_length=250,
    )

    subtext: Optional[str] = Field(
        default=None,
        max_length=1000,
    )


    package_type: Optional[PackageTypeEnum]= None 

    # ========================================================
    # OPTIONAL SPECIFIC PACKAGE
    # ========================================================
    # Optional package selected from the selected package_type.
    #
    # Example:
    #
    # package_type = beach
    # package_id = 17
    #
    # The frontend can use the selected Package.slug to create:
    #
    # "Explore Goa Beach Escape"
    #
    package_id: Optional[int] = Field(
        default=None,
        gt=0,
    )

    # ========================================================
    # PROMOTIONAL TEXT
    # ========================================================

    offer_text: Optional[str] = Field(
        default=None,
        max_length=250,
    )

    # ========================================================
    # DISPLAY ORDER
    # ========================================================

    display_order: int = Field(
        default=0,
        ge=0,
    )

    # ========================================================
    # VISIBILITY
    # ========================================================

    is_active: bool = True

    # ========================================================
    # SCHEDULING
    # ========================================================

    starts_at: Optional[datetime] = None

    ends_at: Optional[datetime] = None


# ============================================================
# CREATE
# ============================================================


class HeroSlideCreate(HeroSlideBase):
    # Required desktop hero image
    image: HeroImage

    # Optional mobile-specific hero image
    image_mobile: Optional[HeroImage] = None


# ============================================================
# UPDATE
# ============================================================


class HeroSlideUpdate(BaseModel):
    # ========================================================
    # HERO IMAGES
    # ========================================================

    image: Optional[HeroImage] = None

    image_mobile: Optional[HeroImage] = None

    # ========================================================
    # HERO CONTENT
    # ========================================================

    image_position: Optional[str] = Field(
        default=None,
        max_length=30,
    )

    content_position: Optional[ContentPosition] = None
    overlay_strength: Optional[OverlayStrength] = None


    badge: Optional[str] = Field(
        default=None,
        max_length=150,
    )

    headline: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=250,
    )

    subtext: Optional[str] = Field(
        default=None,
        max_length=1000,
    )

    # ========================================================
    # PACKAGE CATEGORY
    # ========================================================

    package_type: Optional[PackageTypeEnum] = None

    # ========================================================
    # OPTIONAL SPECIFIC PACKAGE
    # ========================================================

    package_id: Optional[int] = Field(
        default=None,
        gt=0,
    )

    # ========================================================
    # PROMOTIONAL TEXT
    # ========================================================

    offer_text: Optional[str] = Field(
        default=None,
        max_length=250,
    )

    # ========================================================
    # DISPLAY ORDER
    # ========================================================

    display_order: Optional[int] = Field(
        default=None,
        ge=0,
    )

    # ========================================================
    # VISIBILITY
    # ========================================================

    is_active: Optional[bool] = None

    # ========================================================
    # SCHEDULING
    # ========================================================

    starts_at: Optional[datetime] = None

    ends_at: Optional[datetime] = None


# ============================================================
# RESPONSE
# ============================================================


class HeroSlideOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    # ========================================================
    # HERO IMAGES
    # ========================================================

    image: HeroImage

    image_mobile: Optional[HeroImage] = None

    image_position: Optional[str] = None

    content_position: ContentPosition = "middle-left"

    overlay_strength: OverlayStrength = "medium"



    # ========================================================
    # HERO CONTENT
    # ========================================================

    badge: Optional[str] = None

    headline: str

    subtext: Optional[str] = None

    # ========================================================
    # PACKAGE INFORMATION
    # ========================================================

    package_type: Optional[PackageTypeEnum] = None 

    package_id: Optional[int] = None

    # ========================================================
    # PROMOTIONAL TEXT
    # ========================================================

    offer_text: Optional[str] = None

    # ========================================================
    # DISPLAY / VISIBILITY
    # ========================================================

    display_order: int

    is_active: bool

    # ========================================================
    # SCHEDULING
    # ========================================================

    starts_at: Optional[datetime] = None

    ends_at: Optional[datetime] = None

    # ========================================================
    # TIMESTAMPS
    # ========================================================

    created_at: Optional[datetime] = None

    updated_at: Optional[datetime] = None

