from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.hero import HeroSlide
from app.models.package import Package, PackageTypeEnum
from app.schemas.hero import (
    HeroSlideCreate,
    HeroSlideUpdate,
)
from app.core.redis_client import (
    cache_get,
    cache_set,
    cache_delete_pattern,
)


CACHE_PREFIX = "hero_slides"


# ============================================================
# SERIALIZATION
# ============================================================


def _serialize(slide: HeroSlide) -> dict:
    """
    Convert HeroSlide SQLAlchemy object into a JSON-safe dictionary.

    package_type uses the shared PackageTypeEnum.

    Example:
        package_type = "family"

    Frontend can generate:
        Explore Family Packages

    and route to:
        /packages?type=family

    If package_id is present, frontend can additionally generate
    a CTA for the specific package.
    """

    return {
        "id": slide.id,

        # ----------------------------------------------------
        # Images
        # ----------------------------------------------------
        "image": slide.image,
        "image_mobile": slide.image_mobile,
        "image_position": slide.image_position,
        "content_position": slide.content_position,
        "overlay_strength": slide.overlay_strength,

        # ----------------------------------------------------
        # Hero content
        # ----------------------------------------------------
        "badge": slide.badge,
        "headline": slide.headline,
        "subtext": slide.subtext,

        # ----------------------------------------------------
        # Package section
        # ----------------------------------------------------
        "package_type": (
            slide.package_type.value
            if slide.package_type is not None
            else None
        ),
        "package_id": slide.package_id,

        # ----------------------------------------------------
        # Promotional content
        # ----------------------------------------------------
        "offer_text": slide.offer_text,

        # ----------------------------------------------------
        # Ordering / visibility
        # ----------------------------------------------------
        "display_order": slide.display_order,
        "is_active": bool(slide.is_active),

        # ----------------------------------------------------
        # Scheduling
        # ----------------------------------------------------
        "starts_at": (
            slide.starts_at.isoformat()
            if slide.starts_at
            else None
        ),
        "ends_at": (
            slide.ends_at.isoformat()
            if slide.ends_at
            else None
        ),

        # ----------------------------------------------------
        # Metadata
        # ----------------------------------------------------
        "created_at": (
            slide.created_at.isoformat()
            if slide.created_at
            else None
        ),
        "updated_at": (
            slide.updated_at.isoformat()
            if slide.updated_at
            else None
        ),
    }


# ============================================================
# PACKAGE VALIDATION
# ============================================================


def _validate_package_selection(
    db: Session,
    package_type: Optional[PackageTypeEnum],
    package_id: Optional[int],
) -> None:
    """
    Validate the optional specific package selection.

    Rules:

    1. package_type can exist without package_id.

       Example:
           package_type = family
           package_id = None

       This means:
           Explore Family Packages

    2. package_id requires package_type.

    3. Selected package must exist.

    4. Selected package must belong to the selected
       package_type.

    Example:

        package_type = beach
        package_id = 17

    Package #17 must also have:

        package_type = beach
    """

    # --------------------------------------------------------
    # No specific package selected
    # --------------------------------------------------------

    if package_id is None:
        return

    # --------------------------------------------------------
    # Specific package requires category
    # --------------------------------------------------------

    if package_type is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "package_type is required when package_id "
                "is selected."
            ),
        )

    # --------------------------------------------------------
    # Find package
    # --------------------------------------------------------

    package = (
        db.query(Package)
        .filter(
            Package.id == package_id
        )
        .first()
    )

    if not package:
        raise HTTPException(
            status_code=404,
            detail="Selected package not found.",
        )

    # --------------------------------------------------------
    # Normalize enum values
    # --------------------------------------------------------

    selected_type = (
        package_type
        if isinstance(package_type, PackageTypeEnum)
        else PackageTypeEnum(package_type)
    )

    actual_type = (
        package.package_type
        if isinstance(
            package.package_type,
            PackageTypeEnum,
        )
        else PackageTypeEnum(package.package_type)
    )

    # --------------------------------------------------------
    # Compare package types
    # --------------------------------------------------------

    if selected_type != actual_type:
        raise HTTPException(
            status_code=400,
            detail=(
                "Selected package does not belong to "
                f"package_type '{selected_type.value}'."
            ),
        )


# ============================================================
# DISPLAY ORDER
# ============================================================


def _place_in_order(
    db: Session,
    slide: HeroSlide,
    new_order: Optional[int],
    exclude_id: Optional[int] = None,
) -> None:
    """
    Insert/reposition a Hero slide at the requested position.

    Rules:

    - Ordering is 1-based.
    - None / 0 -> last position.
    - Position greater than total -> last position.
    - Moving upward pushes affected slides down.
    - Moving downward pulls affected slides up.
    - Final display_order values are always 1..n.
    """

    query = db.query(HeroSlide)

    if exclude_id is not None:
        query = query.filter(
            HeroSlide.id != exclude_id
        )

    slides = (
        query
        .order_by(
            HeroSlide.display_order.asc(),
            HeroSlide.id.asc(),
        )
        .all()
    )

    # Total number of slides after inserting/repositioning.
    total = len(slides) + 1

    # --------------------------------------------------------
    # Determine requested position
    # --------------------------------------------------------

    if not new_order:
        position = total
    else:
        position = max(
            1,
            min(int(new_order), total),
        )

    # --------------------------------------------------------
    # Insert slide into requested position
    # --------------------------------------------------------

    slides.insert(
        position - 1,
        slide,
    )

    # --------------------------------------------------------
    # Renumber all slides
    # --------------------------------------------------------

    for index, item in enumerate(
        slides,
        start=1,
    ):
        if item.display_order != index:
            item.display_order = index


# ============================================================
# NORMALIZE DISPLAY ORDERS
# ============================================================


def _normalize_display_orders(
    db: Session,
) -> None:
    """
    Normalize all Hero slides to:

        1, 2, 3, 4, ...

    Existing display_order is used first, followed by ID
    as the deterministic tie-breaker.
    """

    slides = (
        db.query(HeroSlide)
        .order_by(
            HeroSlide.display_order.asc(),
            HeroSlide.id.asc(),
        )
        .all()
    )

    for index, slide in enumerate(
        slides,
        start=1,
    ):
        if slide.display_order != index:
            slide.display_order = index


# ============================================================
# CACHE
# ============================================================


def _invalidate_cache() -> None:
    """
    Clear every Hero slide cache entry.

    Examples:

        hero_slides:active
        hero_slides:id:1
        hero_slides:id:2
        ...
    """

    cache_delete_pattern(
        f"{CACHE_PREFIX}:*"
    )


# ============================================================
# PUBLIC — GET CURRENTLY LIVE HERO SLIDES
# ============================================================


def get_active_hero_slides(
    db: Session,
) -> list[dict]:
    """
    Public Hero endpoint.

    Returns only slides that are currently eligible to appear.

    A slide is live when:

        is_active = True

    AND:

        starts_at is NULL
        OR
        starts_at <= current UTC time

    AND:

        ends_at is NULL
        OR
        ends_at >= current UTC time

    Therefore:

        inactive slide
            -> hidden

        future slide
            -> hidden

        expired slide
            -> hidden

        active slide without schedule
            -> shown

        active slide inside schedule
            -> shown

    This endpoint intentionally does not cache the result because
    scheduling changes with time.
    """

    now = datetime.now(timezone.utc)

    slides = (
        db.query(HeroSlide)
        .filter(
            HeroSlide.is_active.is_(True),
            (
                HeroSlide.starts_at.is_(None)
                | (HeroSlide.starts_at <= now)
            ),
            (
                HeroSlide.ends_at.is_(None)
                | (HeroSlide.ends_at >= now)
            ),
        )
        .order_by(
            HeroSlide.display_order.asc(),
            HeroSlide.id.asc(),
        )
        .all()
    )

    return [
        _serialize(slide)
        for slide in slides
    ]


# ============================================================
# PUBLIC / ADMIN — GET HERO SLIDE BY ID
# ============================================================


def get_hero_slide_by_id(
    db: Session,
    slide_id: int,
) -> dict:
    """
    Get a Hero slide by ID.

    This intentionally allows:

        - active slides
        - inactive slides
        - future slides
        - expired slides

    because admin routes may need to retrieve and edit them.
    """

    cache_key = (
        f"{CACHE_PREFIX}:id:{slide_id}"
    )

    cached = cache_get(cache_key)

    if cached is not None:
        return cached

    slide = (
        db.query(HeroSlide)
        .filter(
            HeroSlide.id == slide_id
        )
        .first()
    )

    if not slide:
        raise HTTPException(
            status_code=404,
            detail="Hero slide not found",
        )

    data = _serialize(slide)

    cache_set(
        cache_key,
        data,
    )

    return data


# ============================================================
# ADMIN — GET ALL HERO SLIDES
# ============================================================


def get_all_hero_slides_admin(
    db: Session,
) -> list[dict]:
    """
    Admin/creator view.

    Returns every Hero slide:

        - active
        - inactive
        - future scheduled
        - expired scheduled

    This allows the admin panel to manage campaigns.
    """

    slides = (
        db.query(HeroSlide)
        .order_by(
            HeroSlide.display_order.asc(),
            HeroSlide.id.asc(),
        )
        .all()
    )

    return [
        _serialize(slide)
        for slide in slides
    ]


# ============================================================
# CREATE HERO SLIDE
# ============================================================


def create_hero_slide(
    db: Session,
    payload: HeroSlideCreate,
) -> HeroSlide:
    """
    Create a new Hero slide.

    Display order:

        0 / None
            -> last position

        1
            -> first position

        2
            -> second position

        greater than total
            -> last position

    Existing slides are automatically shifted.

    Package selection:

        package_type only
            -> category CTA

        package_type + package_id
            -> specific package CTA
    """

    # --------------------------------------------------------
    # Validate package selection
    # --------------------------------------------------------

    _validate_package_selection(
        db=db,
        package_type=payload.package_type,
        package_id=payload.package_id,
    )

    # --------------------------------------------------------
    # Convert normal fields
    # --------------------------------------------------------

    slide_data = payload.model_dump(
        exclude={
            "image",
            "image_mobile",
        }
    )

    # --------------------------------------------------------
    # Requested display order
    # --------------------------------------------------------

    requested_order = slide_data.pop(
        "display_order",
        None,
    )

    # --------------------------------------------------------
    # Desktop image
    # --------------------------------------------------------

    image_data = payload.image.model_dump()

    # --------------------------------------------------------
    # Mobile image
    # --------------------------------------------------------

    image_mobile_data = (
        payload.image_mobile.model_dump()
        if payload.image_mobile
        else None
    )

    # --------------------------------------------------------
    # Create object
    # --------------------------------------------------------

    slide = HeroSlide(
        **slide_data,
        display_order=0,
        image=image_data,
        image_mobile=image_mobile_data,
    )

    # --------------------------------------------------------
    # Apply display order
    # --------------------------------------------------------

    _place_in_order(
        db,
        slide,
        requested_order,
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    db.add(slide)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(slide)

    # --------------------------------------------------------
    # Clear cache
    # --------------------------------------------------------

    _invalidate_cache()

    return slide


# ============================================================
# UPDATE HERO SLIDE
# ============================================================


def update_hero_slide(
    db: Session,
    slide_id: int,
    payload: HeroSlideUpdate,
) -> HeroSlide:
    """
    Update an existing Hero slide.

    Handles:

        - desktop image
        - mobile image
        - image position
        - badge
        - headline
        - subtext
        - package_type
        - package_id
        - offer_text
        - visibility
        - scheduling
        - display order

    Package selection is validated using the resulting
    package_type/package_id combination.
    """

    # --------------------------------------------------------
    # Find slide
    # --------------------------------------------------------

    slide = (
        db.query(HeroSlide)
        .filter(
            HeroSlide.id == slide_id
        )
        .first()
    )

    if not slide:
        raise HTTPException(
            status_code=404,
            detail="Hero slide not found",
        )

    # --------------------------------------------------------
    # Convert update payload
    # --------------------------------------------------------

    update_data = payload.model_dump(
        exclude_unset=True
    )

    # --------------------------------------------------------
    # Determine resulting package selection
    # --------------------------------------------------------

    resulting_package_type = update_data.get(
        "package_type",
        slide.package_type,
    )

    resulting_package_id = update_data.get(
        "package_id",
        slide.package_id,
    )

    # --------------------------------------------------------
    # Validate resulting package selection
    # --------------------------------------------------------

    _validate_package_selection(
        db=db,
        package_type=resulting_package_type,
        package_id=resulting_package_id,
    )

    # --------------------------------------------------------
    # Desktop image
    # --------------------------------------------------------

    if (
        "image" in update_data
        and update_data["image"] is not None
    ):
        image = update_data["image"]

        update_data["image"] = (
            image
            if isinstance(image, dict)
            else image.model_dump()
        )

    # --------------------------------------------------------
    # Mobile image
    # --------------------------------------------------------

    if (
        "image_mobile" in update_data
        and update_data["image_mobile"] is not None
    ):
        image_mobile = update_data["image_mobile"]

        update_data["image_mobile"] = (
            image_mobile
            if isinstance(image_mobile, dict)
            else image_mobile.model_dump()
        )

    # --------------------------------------------------------
    # Display order
    # --------------------------------------------------------

    has_order_change = (
        "display_order" in update_data
    )

    new_order = update_data.pop(
        "display_order",
        None,
    )

    # --------------------------------------------------------
    # Apply normal updates
    # --------------------------------------------------------

    for field, value in update_data.items():
        setattr(
            slide,
            field,
            value,
        )

    # --------------------------------------------------------
    # Reposition
    # --------------------------------------------------------

    if (
        has_order_change
        and new_order is not None
    ):
        _place_in_order(
            db,
            slide,
            new_order,
            exclude_id=slide.id,
        )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(slide)

    # --------------------------------------------------------
    # Clear cache
    # --------------------------------------------------------

    _invalidate_cache()

    return slide


# ============================================================
# DELETE HERO SLIDE
# ============================================================


def delete_hero_slide(
    db: Session,
    slide_id: int,
) -> None:
    """
    Delete a Hero slide and automatically renumber
    the remaining slides.
    """

    # --------------------------------------------------------
    # Find slide
    # --------------------------------------------------------

    slide = (
        db.query(HeroSlide)
        .filter(
            HeroSlide.id == slide_id
        )
        .first()
    )

    if not slide:
        raise HTTPException(
            status_code=404,
            detail="Hero slide not found",
        )

    # --------------------------------------------------------
    # Delete
    # --------------------------------------------------------

    db.delete(slide)

    # Make sure deleted slide is removed from the
    # current transaction before normalization.
    db.flush()

    # --------------------------------------------------------
    # Normalize remaining slides
    # --------------------------------------------------------

    _normalize_display_orders(db)

    # --------------------------------------------------------
    # Commit
    # --------------------------------------------------------

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    # --------------------------------------------------------
    # Clear cache
    # --------------------------------------------------------

    _invalidate_cache()


# ============================================================
# ONE-TIME UTILITY — RENUMBER DISPLAY ORDERS
# ============================================================


def renumber_display_orders(
    db: Session,
) -> int:
    """
    One-time cleanup utility.

    Renumbers all Hero slides:

        1, 2, 3, 4, ...

    according to the existing display_order and ID.

    Returns the total number of Hero slides.
    """

    _normalize_display_orders(db)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    _invalidate_cache()

    return (
        db.query(HeroSlide).count()
    )




