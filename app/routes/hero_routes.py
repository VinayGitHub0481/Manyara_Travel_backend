

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.hero import (
    HeroSlideCreate,
    HeroSlideUpdate,
    HeroSlideOut,
)
from app.services import hero_service
from app.core.deps import require_admin_or_creator


router = APIRouter(
    prefix="/hero",
    tags=["Hero"],
)


# ============================================================
# PUBLIC ROUTES
# ============================================================


# ------------------------------------------------------------
# PUBLIC — GET CURRENTLY LIVE HERO SLIDES
# ------------------------------------------------------------

@router.get(
    "",
    response_model=list[HeroSlideOut],
)
def list_active_hero_slides(
    db: Session = Depends(get_db),
):
    """
    Get currently live Hero slides.

    The service applies:
        - is_active = True
        - starts_at <= current UTC time
        - ends_at >= current UTC time

    Results are ordered by display_order.
    """
    return hero_service.get_active_hero_slides(db)


# ============================================================
# ADMIN / CREATOR ROUTES
# ============================================================

# IMPORTANT:
#
# Keep all /admin/* routes before /{slide_id}
# so "admin" is never interpreted as an integer ID.
#


# ------------------------------------------------------------
# ADMIN — GET ALL HERO SLIDES
# ------------------------------------------------------------

@router.get(
    "/admin/all",
    response_model=list[HeroSlideOut],
    dependencies=[Depends(require_admin_or_creator)],
)
def list_all_hero_slides(
    db: Session = Depends(get_db),
):
    """
    Get all Hero slides for admin/creator management.

    Includes:
        - active
        - inactive
        - future scheduled
        - expired scheduled
    """
    return hero_service.get_all_hero_slides_admin(db)


# ------------------------------------------------------------
# ADMIN — CREATE HERO SLIDE
# ------------------------------------------------------------

@router.post(
    "/admin",
    response_model=HeroSlideOut,
    dependencies=[Depends(require_admin_or_creator)],
)
def create_hero_slide(
    payload: HeroSlideCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new Hero slide.

    display_order:
        0 / None -> last position
        1         -> first position
        2         -> second position
        etc.

    Existing slides are automatically shifted.

    package_type:
        Required.

    package_id:
        Optional.

    If package_id is supplied, the service verifies that
    the selected Package belongs to the selected package_type.
    """
    return hero_service.create_hero_slide(
        db,
        payload,
    )


# ------------------------------------------------------------
# ADMIN — UPDATE HERO SLIDE
# ------------------------------------------------------------

@router.put(
    "/admin/{slide_id}",
    response_model=HeroSlideOut,
    dependencies=[Depends(require_admin_or_creator)],
)
def update_hero_slide(
    slide_id: int,
    payload: HeroSlideUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing Hero slide.

    Supports updating:
        - images
        - image position
        - badge
        - headline
        - subtext
        - package_type
        - package_id
        - offer_text
        - display_order
        - is_active
        - starts_at
        - ends_at

    If package_type/package_id changes, package selection
    is validated again.

    If display_order changes, the service automatically
    repositions the slide and renumbers the other slides.
    """
    return hero_service.update_hero_slide(
        db,
        slide_id,
        payload,
    )


# ------------------------------------------------------------
# ADMIN — DELETE HERO SLIDE
# ------------------------------------------------------------

@router.delete(
    "/admin/{slide_id}",
    status_code=204,
    dependencies=[Depends(require_admin_or_creator)],
)
def delete_hero_slide(
    slide_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a Hero slide.

    Remaining slides are automatically renumbered:
        1, 2, 3, ... n
    """
    hero_service.delete_hero_slide(
        db,
        slide_id,
    )

    return None


# ------------------------------------------------------------
# ADMIN — GET HERO SLIDE BY ID
# ------------------------------------------------------------

@router.get(
    "/admin/{slide_id}",
    response_model=HeroSlideOut,
    dependencies=[Depends(require_admin_or_creator)],
)
def get_hero_slide_admin(
    slide_id: int,
    db: Session = Depends(get_db),
):
    """
    Get any Hero slide by ID for admin/creator management.

    This can return:
        - active slides
        - inactive slides
        - future scheduled slides
        - expired scheduled slides
    """
    return hero_service.get_hero_slide_by_id(
        db,
        slide_id,
    )



