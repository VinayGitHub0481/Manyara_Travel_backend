
# if (isEditingExisting) {
#   delete payload.slug;
#   await updateSeasonedDestination(editing.id, payload);
# }

from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.seasoned_visit import SeasonedDestination
from app.models.package import Package, StatusEnum

from app.schemas.seasoned_schema import (
    SeasonedDestinationCreate,
    SeasonedDestinationUpdate,
)

from app.core.redis_client import (
    cache_get,
    cache_set,
    cache_delete_pattern,
)

from app.core.slugify import unique_slug


CACHE_PREFIX = "seasoned_destinations"


# ============================================================
# SERIALIZATION
# ============================================================


def _serialize_package(pkg: Package) -> dict:
    """
    Convert a Package SQLAlchemy object into the lightweight
    package structure used inside a seasoned destination.
    """

    return {
        "id": pkg.id,
        "title": pkg.title,
        "slug": pkg.slug,
        "destination": pkg.destination,
        "price": pkg.price,
        "duration_days": pkg.duration_days,
        "duration_nights": pkg.duration_nights,
        "images": pkg.images or [],
        "package_type": (
            pkg.package_type.value
            if pkg.package_type
            else None
        ),
        "status": (
            pkg.status.value
            if pkg.status
            else None
        ),
        "is_popular": bool(pkg.is_popular),
        "is_recommended": bool(pkg.is_recommended),
        "is_trending": bool(pkg.is_trending),
        "is_featured": bool(pkg.is_featured),
        "is_new": bool(pkg.is_new),
        "is_most_visited": bool(pkg.is_most_visited),
        "display_order": pkg.display_order,
    }


def _serialize(
    destination: SeasonedDestination,
    include_packages: bool = False,
) -> dict:
    """
    Convert a SeasonedDestination SQLAlchemy object
    into a JSON-safe dictionary.

    If include_packages=True, only published packages
    associated with this seasoned destination are returned.
    """

    data = {
        "id": destination.id,
        "place_name": destination.place_name,
        "slug": destination.slug,
        "image": destination.image,
        "description": destination.description,
        "season_label": destination.season_label,
        "season_start_date": (
            destination.season_start_date.isoformat()
            if destination.season_start_date
            else None
        ),
        "season_end_date": (
            destination.season_end_date.isoformat()
            if destination.season_end_date
            else None
        ),
        "best_time_to_visit": destination.best_time_to_visit,
        "starting_from": (
            str(destination.starting_from)
            if destination.starting_from is not None
            else None
        ),
        "display_order": destination.display_order,
        "status": (
            destination.status.value
            if hasattr(destination.status, "value")
            else destination.status
        ),
        "created_by": destination.created_by,
        "created_at": (
            destination.created_at.isoformat()
            if destination.created_at
            else None
        ),
        "updated_at": (
            destination.updated_at.isoformat()
            if destination.updated_at
            else None
        ),
    }

    if include_packages:
        packages = (
            db_query_packages_for_destination(
                destination
            )
        )

        data["packages"] = [
            _serialize_package(package)
            for package in packages
        ]

    return data


# ============================================================
# PACKAGE QUERY
# ============================================================


def db_query_packages_for_destination(
    destination: SeasonedDestination,
) -> list[Package]:
    """
    Return published packages belonging to this
    seasoned destination.

    This helper intentionally uses the relationship
    already defined on SeasonedDestination.

    Relationship:

        SeasonedDestination
                |
                | packages
                v
             Package
    """

    return [
        package
        for package in destination.packages
        if package.status == StatusEnum.published
    ]


# ============================================================
# DISPLAY ORDER
# ============================================================


def _place_in_order(
    db: Session,
    destination: SeasonedDestination,
    new_order: Optional[int],
    exclude_id: Optional[int] = None,
) -> None:
    """
    Put the seasoned destination at position new_order
    and renumber all seasoned destinations 1..n.

    - 0 / None -> goes last
    - Beyond the end -> goes last
    - Existing destination is excluded using exclude_id
    """

    query = db.query(SeasonedDestination)

    if exclude_id is not None:
        query = query.filter(
            SeasonedDestination.id != exclude_id
        )

    others = (
        query.order_by(
            SeasonedDestination.display_order.asc(),
            SeasonedDestination.id.asc(),
        )
        .all()
    )

    total = len(others) + 1

    if not new_order:
        position = total
    else:
        position = max(
            1,
            min(int(new_order), total),
        )

    others.insert(
        position - 1,
        destination,
    )

    for index, item in enumerate(
        others,
        start=1,
    ):
        if item.display_order != index:
            item.display_order = index


def _normalize_display_orders(
    db: Session,
) -> None:
    """
    Renumber every seasoned destination 1..n.
    """

    destinations = (
        db.query(SeasonedDestination)
        .order_by(
            SeasonedDestination.display_order.asc(),
            SeasonedDestination.id.asc(),
        )
        .all()
    )

    for index, item in enumerate(
        destinations,
        start=1,
    ):
        if item.display_order != index:
            item.display_order = index


# ============================================================
# CACHE
# ============================================================


def _invalidate_cache() -> None:
    """
    Clear all seasoned destination caches.
    """

    cache_delete_pattern(
        f"{CACHE_PREFIX}:*"
    )


def _invalidate_package_cache() -> None:
    """
    Packages are included in seasoned destination
    responses.

    This function clears package caches whenever the
    seasonal destination service changes a destination.

    This is useful if package responses contain
    destination information or if your frontend caches
    related data together.
    """

    cache_delete_pattern("packages:*")


def _invalidate_all_related_cache() -> None:
    """
    Clear seasoned destination and package caches.
    """

    _invalidate_cache()
    _invalidate_package_cache()


# ============================================================
# PUBLIC — GET ALL PUBLISHED SEASONED DESTINATIONS
# ============================================================


def get_published_seasoned_destinations(
    db: Session,
) -> list[dict]:
    """
    Public endpoint.

    Returns only published seasoned destinations.

    Ordered according to display_order.
    """

    cache_key = (
        f"{CACHE_PREFIX}:published"
    )

    cached = cache_get(cache_key)

    if cached is not None:
        return cached

    destinations = (
        db.query(SeasonedDestination)
        .filter(
            SeasonedDestination.status == "published"
        )
        .order_by(
            SeasonedDestination.display_order.asc(),
            SeasonedDestination.created_at.desc(),
        )
        .all()
    )

    data = [
        _serialize(destination)
        for destination in destinations
    ]

    cache_set(
        cache_key,
        data,
    )

    return data


# ============================================================
# PUBLIC — GET SEASONED DESTINATION BY SLUG
# ============================================================


def get_seasoned_destination_by_slug(
    db: Session,
    slug: str,
) -> dict:
    """
    Public destination detail endpoint.

    Returns:

    - seasoned destination information
    - season information
    - published packages associated with it
    """

    cache_key = (
        f"{CACHE_PREFIX}:slug:{slug}"
    )

    cached = cache_get(cache_key)

    if cached is not None:
        return cached

    destination = (
        db.query(SeasonedDestination)
        .filter(
            SeasonedDestination.slug == slug,
            SeasonedDestination.status == "published",
        )
        .first()
    )

    if not destination:
        raise HTTPException(
            status_code=404,
            detail="Seasoned destination not found",
        )

    data = _serialize(
        destination,
        include_packages=True,
    )

    cache_set(
        cache_key,
        data,
    )

    return data


# ============================================================
# PUBLIC / ADMIN — GET BY ID
# ============================================================


def get_seasoned_destination_by_id(
    db: Session,
    destination_id: int,
) -> dict:
    """
    Get a seasoned destination by ID.

    This function does not restrict status, so it can
    return both draft and published destinations.

    Packages returned here are published packages only.
    """

    cache_key = (
        f"{CACHE_PREFIX}:id:{destination_id}"
    )

    cached = cache_get(cache_key)

    if cached is not None:
        return cached

    destination = (
        db.query(SeasonedDestination)
        .filter(
            SeasonedDestination.id == destination_id
        )
        .first()
    )

    if not destination:
        raise HTTPException(
            status_code=404,
            detail="Seasoned destination not found",
        )

    data = _serialize(
        destination,
        include_packages=True,
    )

    cache_set(
        cache_key,
        data,
    )

    return data


# ============================================================
# ADMIN — GET ALL SEASONED DESTINATIONS
# ============================================================


def get_all_seasoned_destinations_admin(
    db: Session,
) -> list[dict]:
    """
    Admin/creator view.

    Includes:

    - draft seasoned destinations
    - published seasoned destinations
    """

    destinations = (
        db.query(SeasonedDestination)
        .order_by(
            SeasonedDestination.display_order.asc(),
            SeasonedDestination.created_at.desc(),
        )
        .all()
    )

    return [
        _serialize(destination)
        for destination in destinations
    ]


# ============================================================
# CREATE SEASONED DESTINATION
# ============================================================


def create_seasoned_destination(
    db: Session,
    payload: SeasonedDestinationCreate,
    user_id: int,
) -> SeasonedDestination:
    """
    Create a new seasoned destination.

    Slug is generated uniquely from place_name.

    display_order:
    - requested position is respected
    - 0 / None adds it last
    - all destinations are renumbered 1..n
    """

    # --------------------------------------------------------
    # Generate unique slug
    # --------------------------------------------------------

    slug = unique_slug(
        db,
        SeasonedDestination,
        payload.place_name,
    )

    # --------------------------------------------------------
    # Convert payload
    # --------------------------------------------------------

    destination_data = payload.model_dump(
        exclude={
            "slug",
            "display_order",
            "created_by",
        }
    )

    requested_order = payload.display_order

    # --------------------------------------------------------
    # Create destination
    # --------------------------------------------------------

    destination = SeasonedDestination(
        **destination_data,

        slug=slug,

        display_order=0,

        created_by=user_id,
    )

    # --------------------------------------------------------
    # Display order
    #
    # Must happen before db.add() for the same reason
    # as package_service.py.
    # --------------------------------------------------------

    _place_in_order(
        db,
        destination,
        requested_order,
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    db.add(destination)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(destination)

    # --------------------------------------------------------
    # Clear caches
    # --------------------------------------------------------

    _invalidate_all_related_cache()

    return destination


# ============================================================
# UPDATE SEASONED DESTINATION
# ============================================================


def update_seasoned_destination(
    db: Session,
    destination_id: int,
    payload: SeasonedDestinationUpdate,
) -> SeasonedDestination:
    """
    Update an existing seasoned destination.

    All fields are optional.

    If place_name changes and slug was not explicitly
    provided, a new unique slug is generated.

    If display_order changes, destinations are reordered
    and renumbered 1..n.
    """

    # --------------------------------------------------------
    # Find destination
    # --------------------------------------------------------

    destination = (
        db.query(SeasonedDestination)
        .filter(
            SeasonedDestination.id == destination_id
        )
        .first()
    )

    if not destination:
        raise HTTPException(
            status_code=404,
            detail="Seasoned destination not found",
        )

    # --------------------------------------------------------
    # Convert update payload
    # --------------------------------------------------------

    update_data = payload.model_dump(
        exclude_unset=True
    )

    # --------------------------------------------------------
    # Handle slug
    #
    # If place_name changes and slug was not manually
    # supplied, generate a new unique slug.
    # --------------------------------------------------------

    if (
        "place_name" in update_data
        and update_data["place_name"]
        != destination.place_name
        and "slug" not in update_data
    ):
        update_data["slug"] = unique_slug(
            db,
            SeasonedDestination,
            update_data["place_name"],
            exclude_id=destination.id,
        )

    # --------------------------------------------------------
    # If slug is manually changed, validate uniqueness
    # through unique_slug.
    # --------------------------------------------------------

    if (
        "slug" in update_data
        and update_data["slug"]
        and update_data["slug"]
        != destination.slug
    ):
        update_data["slug"] = unique_slug(
            db,
            SeasonedDestination,
            update_data["slug"],
            exclude_id=destination.id,
        )

    # --------------------------------------------------------
    # Validate season dates
    # --------------------------------------------------------

    start_date = update_data.get(
        "season_start_date",
        destination.season_start_date,
    )

    end_date = update_data.get(
        "season_end_date",
        destination.season_end_date,
    )

    if (
        start_date is not None
        and end_date is not None
        and start_date > end_date
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "season_start_date cannot be "
                "later than season_end_date"
            ),
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
    # Apply updates
    # --------------------------------------------------------

    for field, value in update_data.items():
        setattr(
            destination,
            field,
            value,
        )

    # --------------------------------------------------------
    # Reorder
    # --------------------------------------------------------

    if (
        has_order_change
        and new_order is not None
    ):
        _place_in_order(
            db,
            destination,
            new_order,
            exclude_id=destination.id,
        )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(destination)

    # --------------------------------------------------------
    # Clear caches
    # --------------------------------------------------------

    _invalidate_all_related_cache()

    return destination


# ============================================================
# DELETE SEASONED DESTINATION
# ============================================================


def delete_seasoned_destination(
    db: Session,
    destination_id: int,
) -> None:
    """
    Delete a seasoned destination and renumber the
    remaining destinations.

    Packages are NOT deleted.

    Because Package.seasoned_destination_id is nullable,
    packages associated with this destination must first
    have their seasoned_destination_id cleared.
    """

    destination = (
        db.query(SeasonedDestination)
        .filter(
            SeasonedDestination.id == destination_id
        )
        .first()
    )

    if not destination:
        raise HTTPException(
            status_code=404,
            detail="Seasoned destination not found",
        )

    # --------------------------------------------------------
    # Detach associated packages first.
    #
    # We intentionally do NOT delete packages.
    # --------------------------------------------------------

    packages = (
        db.query(Package)
        .filter(
            Package.seasoned_destination_id
            == destination.id
        )
        .all()
    )

    for package in packages:
        package.seasoned_destination_id = None

    # --------------------------------------------------------
    # Delete destination
    # --------------------------------------------------------

    db.delete(destination)

    db.flush()

    # --------------------------------------------------------
    # Normalize remaining display orders
    # --------------------------------------------------------

    _normalize_display_orders(db)

    # --------------------------------------------------------
    # Commit everything in one transaction
    # --------------------------------------------------------

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    # --------------------------------------------------------
    # Clear related caches
    # --------------------------------------------------------

    _invalidate_all_related_cache()


# ============================================================
# ONE-TIME UTILITY
# RENUMBER SEASONED DESTINATION display_order
# ============================================================


def renumber_display_orders(
    db: Session,
) -> int:
    """
    Optional utility.

    Renumber all seasoned destinations as:

        1
        2
        3
        4
        ...

    Returns the total number of seasoned destinations.
    """

    _normalize_display_orders(db)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    _invalidate_all_related_cache()

    return (
        db.query(SeasonedDestination)
        .count()
    )
