


from typing import Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.package import Package, StatusEnum
from app.models.most_visited import MostVisited
from app.models.seasoned_visit import SeasonedDestination
from app.schemas.package import (
    PackageCreate,
    PackageUpdate,
)

from app.core.redis_client import (
    cache_get,
    cache_set,
    cache_delete_pattern,
)

from app.core.slugify import unique_slug


CACHE_PREFIX = "packages"


# ============================================================
# SERIALIZATION
# ============================================================


def _serialize(pkg: Package) -> dict:
    """
    Convert a Package SQLAlchemy object into a JSON-safe dictionary.

    A package belongs to exactly ONE destination system:

        Normal:
            destination_id != None
            seasoned_destination_id == None

        Seasonal:
            destination_id == None
            seasoned_destination_id != None
    """

    return {
        "id": pkg.id,
        "title": pkg.title,
        "slug": pkg.slug,

        # ----------------------------------------------------
        # Legacy display/compatibility destination text
        # ----------------------------------------------------
        "destination": pkg.destination,

        # ----------------------------------------------------
        # Normal destination
        # ----------------------------------------------------
        "destination_id": pkg.destination_id,

        # ----------------------------------------------------
        # Seasonal destination
        # ----------------------------------------------------
        "seasoned_destination_id": pkg.seasoned_destination_id,

        # ----------------------------------------------------
        # Package classification
        # ----------------------------------------------------
        "package_type": (
            pkg.package_type.value
            if pkg.package_type
            else None
        ),

        # ----------------------------------------------------
        # Admin-controlled display order
        # ----------------------------------------------------
        "display_order": pkg.display_order,

        # ----------------------------------------------------
        # Discovery / visibility flags
        # ----------------------------------------------------
        "is_popular": bool(pkg.is_popular),
        "is_recommended": bool(pkg.is_recommended),
        "is_trending": bool(pkg.is_trending),
        "is_featured": bool(pkg.is_featured),
        "is_new": bool(pkg.is_new),
        "is_most_visited": bool(pkg.is_most_visited),

        # ----------------------------------------------------
        # Pricing & duration
        # ----------------------------------------------------
        "price": str(pkg.price),
        "duration_days": pkg.duration_days,
        "duration_nights": pkg.duration_nights,

        # ----------------------------------------------------
        # Description
        # ----------------------------------------------------
        "description": pkg.description,

        # ----------------------------------------------------
        # Images & itinerary
        # ----------------------------------------------------
        "images": pkg.images or [],
        "itinerary": pkg.itinerary or [],

        # ----------------------------------------------------
        # Package details
        # ----------------------------------------------------
        "facilities": pkg.facilities or [],
        "inclusions": pkg.inclusions or [],
        "exclusions": pkg.exclusions or [],

        # ----------------------------------------------------
        # Package policies
        # ----------------------------------------------------
        "terms_and_conditions": pkg.terms_and_conditions,
        "cancellation_policy": pkg.cancellation_policy,

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------
        "status": (
            pkg.status.value
            if pkg.status
            else None
        ),

        # ----------------------------------------------------
        # Metadata
        # ----------------------------------------------------
        "created_by": pkg.created_by,

        "created_at": (
            pkg.created_at.isoformat()
            if pkg.created_at
            else None
        ),

        "updated_at": (
            pkg.updated_at.isoformat()
            if pkg.updated_at
            else None
        ),
    }


# ============================================================
# DESTINATION VALIDATION
# ============================================================


def _get_destination(
    db: Session,
    destination_id: int,
) -> MostVisited:
    """
    Find the normal MostVisited destination.

    Only published destinations can be assigned to packages.
    """

    destination = (
        db.query(MostVisited)
        .filter(
            MostVisited.id == destination_id,
            MostVisited.status == "published",
        )
        .first()
    )

    if not destination:
        raise HTTPException(
            status_code=400,
            detail="Invalid or unpublished destination",
        )

    return destination


# ============================================================
# SEASONAL DESTINATION VALIDATION
# ============================================================


def _get_seasoned_destination(
    db: Session,
    seasoned_destination_id: int,
) -> SeasonedDestination:
    """
    Find the seasonal destination.

    Only published seasonal destinations can be assigned
    to packages.
    """

    seasoned_destination = (
        db.query(SeasonedDestination)
        .filter(
            SeasonedDestination.id == seasoned_destination_id,
            SeasonedDestination.status == "published",
        )
        .first()
    )

    if not seasoned_destination:
        raise HTTPException(
            status_code=400,
            detail="Invalid or unpublished seasonal destination",
        )

    return seasoned_destination


# ============================================================
# PACKAGE DESTINATION VALIDATION
# ============================================================


def _validate_destination_assignment(
    destination_id: Optional[int],
    seasoned_destination_id: Optional[int],
) -> None:
    """
    Enforce the package destination business rule.

    Exactly ONE destination relationship must exist.

    Valid:

        destination_id=5
        seasoned_destination_id=None

    OR:

        destination_id=None
        seasoned_destination_id=3

    Invalid:

        destination_id=5
        seasoned_destination_id=3

    Invalid:

        destination_id=None
        seasoned_destination_id=None
    """

    if (
        destination_id is not None
        and seasoned_destination_id is not None
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "A package can belong to either a normal "
                "destination or a seasonal destination, "
                "not both."
            ),
        )

    if (
        destination_id is None
        and seasoned_destination_id is None
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "A package must belong to either a normal "
                "destination or a seasonal destination."
            ),
        )


# ============================================================
# DISPLAY ORDER
# ============================================================


def _place_in_order(
    db: Session,
    pkg: Package,
    new_order: Optional[int],
    exclude_id: Optional[int] = None,
) -> None:
    """
    Put pkg at position new_order and renumber ALL packages 1..n.

    - Fixes duplicate / zero display_order values.
    - new_order empty / 0 / beyond the end -> package goes last.
    - exclude_id prevents an existing package from being counted twice.

    Called before db.commit().
    """

    query = db.query(Package)

    if exclude_id is not None:
        query = query.filter(
            Package.id != exclude_id
        )

    others = (
        query
        .order_by(
            Package.display_order.asc(),
            Package.id.asc(),
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

    others.insert(position - 1, pkg)

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
    Renumber every package 1..n.
    """

    packages = (
        db.query(Package)
        .order_by(
            Package.display_order.asc(),
            Package.id.asc(),
        )
        .all()
    )

    for index, item in enumerate(
        packages,
        start=1,
    ):
        if item.display_order != index:
            item.display_order = index


# ============================================================
# CACHE
# ============================================================


def _invalidate_cache() -> None:
    """
    Wipe every cached packages:* key.
    """

    cache_delete_pattern(
        f"{CACHE_PREFIX}:*"
    )


def _invalidate_destination_cache() -> None:
    """
    Packages are included inside MostVisited responses.
    """

    cache_delete_pattern(
        "most_visited:*"
    )


def _invalidate_seasoned_destination_cache() -> None:
    """
    Packages are included inside SeasonedDestination responses.
    """

    cache_delete_pattern(
        "seasoned_destinations:*"
    )


def _invalidate_all_related_cache() -> None:
    """
    Clear package, normal destination and seasonal
    destination caches.
    """

    _invalidate_cache()
    _invalidate_destination_cache()
    _invalidate_seasoned_destination_cache()


# ============================================================
# PUBLIC — GET ALL PUBLISHED PACKAGES
# ============================================================


def get_published_packages(
    db: Session,
    collection: Optional[str] = None,
) -> list[dict]:
    """
    Public endpoint.

    Returns published packages.

    Discovery collections:

        /packages
        /packages?collection=popular
        /packages?collection=recommended
        /packages?collection=trending
        /packages?collection=featured
        /packages?collection=new
        /packages?collection=most_visited

    Seasonal packages are NOT automatically excluded here.

    If the public site needs a separate seasonal listing,
    use get_published_seasonal_packages().
    """

    collection = (
        collection.strip().lower()
        if collection
        else None
    )

    collection_filters = {
        "popular": Package.is_popular,
        "recommended": Package.is_recommended,
        "trending": Package.is_trending,
        "featured": Package.is_featured,
        "new": Package.is_new,
        "most_visited": Package.is_most_visited,
    }

    if (
        collection
        and collection not in collection_filters
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid collection. "
                "Allowed values: "
                "popular, recommended, trending, "
                "featured, new, most_visited."
            ),
        )

    if collection:
        cache_key = (
            f"{CACHE_PREFIX}:published:{collection}"
        )
    else:
        cache_key = f"{CACHE_PREFIX}:published"

    cached = cache_get(cache_key)

    if cached is not None:
        return cached

    query = (
        db.query(Package)
        .filter(
            Package.status
            == StatusEnum.published
        )
    )

    if collection:
        query = query.filter(
            collection_filters[collection].is_(True)
        )

    packages = (
        query
        .order_by(
            Package.display_order.asc(),
            Package.created_at.desc(),
        )
        .all()
    )

    data = [
        _serialize(package)
        for package in packages
    ]

    cache_set(
        cache_key,
        data,
    )

    return data


# ============================================================
# PUBLIC — GET PUBLISHED NORMAL PACKAGES
# ============================================================


def get_published_normal_packages(
    db: Session,
) -> list[dict]:
    """
    Return only published regular/normal packages.

    A normal package MUST have:

        destination_id != NULL
        seasoned_destination_id == NULL
    """

    cache_key = (
        f"{CACHE_PREFIX}:published:normal"
    )

    cached = cache_get(cache_key)

    if cached is not None:
        return cached

    packages = (
        db.query(Package)
        .filter(
            Package.status
            == StatusEnum.published,
            Package.destination_id.isnot(None),
            Package.seasoned_destination_id.is_(None),
        )
        .order_by(
            Package.display_order.asc(),
            Package.created_at.desc(),
        )
        .all()
    )

    data = [
        _serialize(package)
        for package in packages
    ]

    cache_set(
        cache_key,
        data,
    )

    return data


# ============================================================
# PUBLIC — GET PUBLISHED SEASONAL PACKAGES
# ============================================================


def get_published_seasonal_packages(
    db: Session,
    seasoned_destination_id: Optional[int] = None,
) -> list[dict]:
    """
    Return only published seasonal packages.

    A seasonal package MUST have:

        destination_id == NULL
        seasoned_destination_id != NULL

    Optional seasoned_destination_id can be used to return
    packages belonging to one specific seasonal destination.
    """

    if seasoned_destination_id is not None:
        cache_key = (
            f"{CACHE_PREFIX}:published:"
            f"seasonal:{seasoned_destination_id}"
        )
    else:
        cache_key = (
            f"{CACHE_PREFIX}:published:seasonal"
        )

    cached = cache_get(cache_key)

    if cached is not None:
        return cached

    query = (
        db.query(Package)
        .filter(
            Package.status
            == StatusEnum.published,
            Package.destination_id.is_(None),
            Package.seasoned_destination_id.isnot(None),
        )
    )

    if seasoned_destination_id is not None:
        query = query.filter(
            Package.seasoned_destination_id
            == seasoned_destination_id
        )

    packages = (
        query
        .order_by(
            Package.display_order.asc(),
            Package.created_at.desc(),
        )
        .all()
    )

    data = [
        _serialize(package)
        for package in packages
    ]

    cache_set(
        cache_key,
        data,
    )

    return data


# ============================================================
# PUBLIC / ADMIN — GET PACKAGE BY ID
# ============================================================


def get_package_by_id(
    db: Session,
    package_id: int,
) -> dict:
    """
    Get a package by ID.

    This function does not restrict status.
    """

    cache_key = (
        f"{CACHE_PREFIX}:id:{package_id}"
    )

    cached = cache_get(cache_key)

    if cached is not None:
        return cached

    pkg = (
        db.query(Package)
        .filter(
            Package.id == package_id
        )
        .first()
    )

    if not pkg:
        raise HTTPException(
            status_code=404,
            detail="Package not found",
        )

    data = _serialize(pkg)

    cache_set(
        cache_key,
        data,
    )

    return data


# ============================================================
# PUBLIC — GET PACKAGE BY SLUG
# ============================================================


def get_package_by_slug(
    db: Session,
    slug: str,
) -> dict:
    """
    Get a published package by slug.
    """

    cache_key = (
        f"{CACHE_PREFIX}:slug:{slug}"
    )

    cached = cache_get(cache_key)

    if cached is not None:
        return cached

    pkg = (
        db.query(Package)
        .filter(
            Package.slug == slug,
            Package.status
            == StatusEnum.published,
        )
        .first()
    )

    if not pkg:
        raise HTTPException(
            status_code=404,
            detail="Package not found",
        )

    data = _serialize(pkg)

    cache_set(
        cache_key,
        data,
    )

    return data


# ============================================================
# ADMIN — GET ALL PACKAGES
# ============================================================


def get_all_packages_admin(
    db: Session,
) -> list[dict]:
    """
    Admin/creator view.

    Includes:
        - draft packages
        - published packages
        - normal packages
        - seasonal packages
    """

    packages = (
        db.query(Package)
        .order_by(
            Package.display_order.asc(),
            Package.created_at.desc(),
        )
        .all()
    )

    return [
        _serialize(package)
        for package in packages
    ]


# ============================================================
# CREATE PACKAGE
# ============================================================


def create_package(
    db: Session,
    payload: PackageCreate,
    user_id: int,
) -> Package:
    """
    Create a new package.

    BUSINESS RULE:

        Normal package:
            destination_id required
            seasoned_destination_id must be NULL

        Seasonal package:
            seasoned_destination_id required
            destination_id must be NULL

    Exactly ONE destination relationship is allowed.
    """

    # --------------------------------------------------------
    # Read destination IDs
    # --------------------------------------------------------

    destination_id = payload.destination_id
    seasoned_destination_id = (
        payload.seasoned_destination_id
    )

    # --------------------------------------------------------
    # Validate XOR destination rule
    # --------------------------------------------------------

    _validate_destination_assignment(
        destination_id,
        seasoned_destination_id,
    )

    # --------------------------------------------------------
    # Validate normal destination
    # --------------------------------------------------------

    destination = None

    if destination_id is not None:
        destination = _get_destination(
            db,
            destination_id,
        )

    # --------------------------------------------------------
    # Validate seasonal destination
    # --------------------------------------------------------

    seasoned_destination = None

    if seasoned_destination_id is not None:
        seasoned_destination = (
            _get_seasoned_destination(
                db,
                seasoned_destination_id,
            )
        )

    # --------------------------------------------------------
    # Generate unique slug
    # --------------------------------------------------------

    slug = unique_slug(
        db,
        Package,
        payload.title,
    )

    # --------------------------------------------------------
    # Convert payload
    # --------------------------------------------------------

    package_data = payload.model_dump(
        exclude={
            "images",
            "itinerary",
            "destination",
            "destination_id",
            "seasoned_destination_id",
        }
    )

    # --------------------------------------------------------
    # Requested position
    # --------------------------------------------------------

    requested_order = package_data.pop(
        "display_order",
        None,
    )

    # --------------------------------------------------------
    # Create package
    # --------------------------------------------------------

    pkg = Package(
        **package_data,

        # Temporary value.
        # _place_in_order() assigns final position.
        display_order=0,

        # ----------------------------------------------------
        # Normal destination
        # ----------------------------------------------------
        destination_id=(
            destination.id
            if destination
            else None
        ),

        # Legacy display text.
        #
        # For seasonal packages there is no normal
        # destination, so this remains None.
        destination=(
            destination.place_name
            if destination
            else None
        ),

        # ----------------------------------------------------
        # Seasonal destination
        # ----------------------------------------------------
        seasoned_destination_id=(
            seasoned_destination.id
            if seasoned_destination
            else None
        ),

        # ----------------------------------------------------
        # Images
        # ----------------------------------------------------
        images=[
            img.model_dump()
            for img in payload.images
        ],

        # ----------------------------------------------------
        # Itinerary
        # ----------------------------------------------------
        itinerary=[
            item.model_dump()
            for item in payload.itinerary
        ],

        slug=slug,
        created_by=user_id,
    )

    # --------------------------------------------------------
    # Display order
    # --------------------------------------------------------

    _place_in_order(
        db,
        pkg,
        requested_order,
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    db.add(pkg)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(pkg)

    # --------------------------------------------------------
    # Clear caches
    # --------------------------------------------------------

    _invalidate_all_related_cache()

    return pkg


# ============================================================
# UPDATE PACKAGE
# ============================================================


def update_package(
    db: Session,
    package_id: int,
    payload: PackageUpdate,
) -> Package:
    """
    Update an existing package.

    Destination switching rules:

        Normal -> Seasonal:
            destination_id = NULL
            seasoned_destination_id = selected ID

        Seasonal -> Normal:
            seasoned_destination_id = NULL
            destination_id = selected ID

    Both can NEVER be populated simultaneously.
    """

    # --------------------------------------------------------
    # Find package
    # --------------------------------------------------------

    pkg = (
        db.query(Package)
        .filter(
            Package.id == package_id
        )
        .first()
    )

    if not pkg:
        raise HTTPException(
            status_code=404,
            detail="Package not found",
        )

    # --------------------------------------------------------
    # Convert update payload
    # --------------------------------------------------------

    update_data = payload.model_dump(
        exclude_unset=True
    )

    # --------------------------------------------------------
    # Determine final destination state
    # --------------------------------------------------------
    #
    # IMPORTANT:
    # We need to calculate the FINAL state before applying
    # updates, because changing from normal -> seasonal or
    # seasonal -> normal requires clearing the other FK.
    # --------------------------------------------------------

    final_destination_id = (
        update_data.get(
            "destination_id",
            pkg.destination_id,
        )
    )

    final_seasoned_destination_id = (
        update_data.get(
            "seasoned_destination_id",
            pkg.seasoned_destination_id,
        )
    )

    # --------------------------------------------------------
    # If user explicitly selects a normal destination,
    # automatically remove seasonal destination.
    # --------------------------------------------------------

    if "destination_id" in update_data:

        selected_destination_id = (
            update_data["destination_id"]
        )

        if selected_destination_id is not None:
            final_destination_id = (
                selected_destination_id
            )

            final_seasoned_destination_id = None

            update_data[
                "seasoned_destination_id"
            ] = None

    # --------------------------------------------------------
    # If user explicitly selects a seasonal destination,
    # automatically remove normal destination.
    # --------------------------------------------------------

    if "seasoned_destination_id" in update_data:

        selected_seasoned_destination_id = (
            update_data[
                "seasoned_destination_id"
            ]
        )

        if selected_seasoned_destination_id is not None:
            final_seasoned_destination_id = (
                selected_seasoned_destination_id
            )

            final_destination_id = None

            update_data[
                "destination_id"
            ] = None

    # --------------------------------------------------------
    # Validate final XOR state
    # --------------------------------------------------------

    _validate_destination_assignment(
        final_destination_id,
        final_seasoned_destination_id,
    )

    # --------------------------------------------------------
    # Handle normal destination
    # --------------------------------------------------------

    if (
        final_destination_id is not None
    ):
        destination = _get_destination(
            db,
            final_destination_id,
        )

        update_data["destination_id"] = (
            destination.id
        )

        # Keep legacy text synchronized.
        update_data["destination"] = (
            destination.place_name
        )

        # Normal package must not have seasonal FK.
        update_data[
            "seasoned_destination_id"
        ] = None

    # --------------------------------------------------------
    # Handle seasonal destination
    # --------------------------------------------------------

    if (
        final_seasoned_destination_id
        is not None
    ):
        seasoned_destination = (
            _get_seasoned_destination(
                db,
                final_seasoned_destination_id,
            )
        )

        update_data[
            "seasoned_destination_id"
        ] = seasoned_destination.id

        # Seasonal package must not have normal FK.
        update_data["destination_id"] = None

        # Clear legacy normal destination text.
        update_data["destination"] = None

    # --------------------------------------------------------
    # Itinerary
    # --------------------------------------------------------

    if (
        "itinerary" in update_data
        and update_data["itinerary"] is not None
    ):
        update_data["itinerary"] = [
            item
            if isinstance(item, dict)
            else item.model_dump()
            for item in update_data["itinerary"]
        ]

    # --------------------------------------------------------
    # Images
    # --------------------------------------------------------

    if (
        "images" in update_data
        and update_data["images"] is not None
    ):
        update_data["images"] = [
            img
            if isinstance(img, dict)
            else img.model_dump()
            for img in update_data["images"]
        ]

    # --------------------------------------------------------
    # Generate new slug when title changes
    # --------------------------------------------------------

    if (
        "title" in update_data
        and update_data["title"] != pkg.title
    ):
        update_data["slug"] = unique_slug(
            db,
            Package,
            update_data["title"],
            exclude_id=pkg.id,
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
            pkg,
            field,
            value,
        )

    # --------------------------------------------------------
    # Display order
    # --------------------------------------------------------

    if (
        has_order_change
        and new_order is not None
    ):
        _place_in_order(
            db,
            pkg,
            new_order,
            exclude_id=pkg.id,
        )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(pkg)

    # --------------------------------------------------------
    # Clear caches
    # --------------------------------------------------------

    _invalidate_all_related_cache()

    return pkg


# ============================================================
# DELETE PACKAGE
# ============================================================


def delete_package(
    db: Session,
    package_id: int,
) -> None:
    """
    Delete a package and renumber the remaining packages.
    """

    pkg = (
        db.query(Package)
        .filter(
            Package.id == package_id
        )
        .first()
    )

    if not pkg:
        raise HTTPException(
            status_code=404,
            detail="Package not found",
        )

    db.delete(pkg)

    db.flush()

    _normalize_display_orders(db)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    _invalidate_all_related_cache()


# ============================================================
# ONE-TIME UTILITY
# RENUMBER display_order AS 1, 2, 3, ...
# ============================================================


def renumber_display_orders(
    db: Session,
) -> int:
    """
    Optional utility to clean existing display_order values.
    """

    _normalize_display_orders(db)

    db.commit()

    _invalidate_all_related_cache()

    return db.query(Package).count()











































# from typing import Optional

# from sqlalchemy.orm import Session
# from fastapi import HTTPException

# from app.models.package import Package, StatusEnum
# from app.models.most_visited import MostVisited

# from app.schemas.package import (
#     PackageCreate,
#     PackageUpdate,
# )

# from app.core.redis_client import (
#     cache_get,
#     cache_set,
#     cache_delete_pattern,
# )

# from app.core.slugify import unique_slug

# CACHE_PREFIX = "packages"


# # ============================================================
# # SERIALIZATION
# # ============================================================


# def _serialize(pkg: Package) -> dict:
#     """
#     Convert a Package SQLAlchemy object into a JSON-safe dictionary.
#     """

#     return {
#         "id": pkg.id,
#         "title": pkg.title,
#         "slug": pkg.slug,
#         # Existing display/compatibility field
#         "destination": pkg.destination,
#         # NEW: actual destination relationship
#         "destination_id": pkg.destination_id,
#         # ----------------------------------------------------
#         # Package classification
#         # ----------------------------------------------------
#         "package_type": (pkg.package_type.value if pkg.package_type else None),
#         # ----------------------------------------------------
#         # Admin-controlled display order
#         # ----------------------------------------------------
#         "display_order": pkg.display_order,
#         # ----------------------------------------------------
#         # Discovery / visibility flags
#         # ----------------------------------------------------
#         "is_popular": bool(pkg.is_popular),
#         "is_recommended": bool(pkg.is_recommended),
#         "is_trending": bool(pkg.is_trending),
#         "is_featured": bool(pkg.is_featured),
#         "is_new": bool(pkg.is_new),
#         "is_most_visited": bool(pkg.is_most_visited),
#         # ----------------------------------------------------
#         # Pricing & duration
#         # ----------------------------------------------------
#         "price": str(pkg.price),
#         "duration_days": pkg.duration_days,
#         "duration_nights": pkg.duration_nights,
#         # ----------------------------------------------------
#         # Description
#         # ----------------------------------------------------
#         "description": pkg.description,
#         # ----------------------------------------------------
#         # Images & itinerary
#         # ----------------------------------------------------
#         "images": pkg.images or [],
#         "itinerary": pkg.itinerary or [],
#         # ----------------------------------------------------
#         # Package details
#         # ----------------------------------------------------
#         "facilities": pkg.facilities or [],
#         "inclusions": pkg.inclusions or [],
#         "exclusions": pkg.exclusions or [],
#         # ----------------------------------------------------
#         # Package policies
#         # ----------------------------------------------------
#         "terms_and_conditions": pkg.terms_and_conditions,
#         "cancellation_policy": pkg.cancellation_policy,
#         # ----------------------------------------------------
#         # Status
#         # ----------------------------------------------------
#         "status": (pkg.status.value if pkg.status else None),
#         # ----------------------------------------------------
#         # Metadata
#         # ----------------------------------------------------
#         "created_by": pkg.created_by,
#         "created_at": (pkg.created_at.isoformat() if pkg.created_at else None),
#         "updated_at": (pkg.updated_at.isoformat() if pkg.updated_at else None),
#     }


# # ============================================================
# # DESTINATION VALIDATION
# # ============================================================


# def _get_destination(
#     db: Session,
#     destination_id: int,
# ) -> MostVisited:
#     """
#     Find the destination referenced by destination_id.

#     Only published destinations can be assigned to packages.
#     """

#     destination = (
#         db.query(MostVisited)
#         .filter(
#             MostVisited.id == destination_id,
#             MostVisited.status == "published",
#         )
#         .first()
#     )

#     if not destination:
#         raise HTTPException(
#             status_code=400,
#             detail="Invalid or unpublished destination",
#         )

#     return destination


# # ============================================================
# # DISPLAY ORDER
# # ============================================================


# def _place_in_order(
#     db: Session,
#     pkg: Package,
#     new_order: Optional[int],
#     exclude_id: Optional[int] = None,
# ) -> None:
#     """
#     Put `pkg` at position `new_order` and renumber ALL packages 1..n.

#     - Fixes duplicate / zero display_order values automatically.
#     - new_order empty / 0 / beyond the end -> the package goes last.
#     - exclude_id: pass pkg.id when the package already exists in the DB,
#       so it is not counted twice.

#     Examples (unique orders 1..5):
#         move 5 -> 2 : old 2, 3, 4 become 3, 4, 5
#         move 2 -> 5 : old 3, 4, 5 become 2, 3, 4

#     Call this BEFORE db.commit() so the reorder and the package
#     save happen in one transaction.
#     """

#     query = db.query(Package)

#     if exclude_id is not None:
#         query = query.filter(Package.id != exclude_id)

#     others = query.order_by(
#         Package.display_order.asc(),
#         Package.id.asc(),
#     ).all()

#     total = len(others) + 1

#     if not new_order:
#         position = total
#     else:
#         position = max(1, min(int(new_order), total))

#     others.insert(position - 1, pkg)

#     for index, item in enumerate(others, start=1):
#         if item.display_order != index:
#             item.display_order = index


# def _normalize_display_orders(db: Session) -> None:
#     """
#     Renumber every package 1..n (used after delete).
#     """

#     packages = (
#         db.query(Package)
#         .order_by(
#             Package.display_order.asc(),
#             Package.id.asc(),
#         )
#         .all()
#     )

#     for index, item in enumerate(packages, start=1):
#         if item.display_order != index:
#             item.display_order = index


# # ============================================================
# # CACHE
# # ============================================================


# def _invalidate_cache() -> None:
#     """
#     Wipe every cached packages:* key.
#     """

#     cache_delete_pattern(f"{CACHE_PREFIX}:*")


# def _invalidate_destination_cache() -> None:
#     """
#     Packages are included inside destination responses.

#     Therefore, whenever a package changes, cached
#     MostVisited/destination responses must also be cleared.
#     """

#     cache_delete_pattern("most_visited:*")


# def _invalidate_all_related_cache() -> None:
#     """
#     Clear both package and destination caches.
#     """

#     _invalidate_cache()
#     _invalidate_destination_cache()


# # ============================================================
# # PUBLIC — GET ALL PUBLISHED PACKAGES
# # ============================================================


# def get_published_packages(
#     db: Session,
#     collection: Optional[str] = None,
# ) -> list[dict]:
#     """
#     Public endpoint.

#     Returns only published packages.

#     Optional discovery collections:

#         /packages
#         /packages?collection=popular
#         /packages?collection=recommended
#         /packages?collection=trending
#         /packages?collection=featured
#         /packages?collection=new
#         /packages?collection=most_visited
#     """

#     collection = collection.strip().lower() if collection else None

#     collection_filters = {
#         "popular": Package.is_popular,
#         "recommended": Package.is_recommended,
#         "trending": Package.is_trending,
#         "featured": Package.is_featured,
#         "new": Package.is_new,
#         "most_visited": Package.is_most_visited,
#     }

#     if collection and collection not in collection_filters:
#         raise HTTPException(
#             status_code=400,
#             detail=(
#                 "Invalid collection. "
#                 "Allowed values: "
#                 "popular, recommended, trending, "
#                 "featured, new, most_visited."
#             ),
#         )

#     if collection:
#         cache_key = f"{CACHE_PREFIX}:" f"published:" f"{collection}"
#     else:
#         cache_key = f"{CACHE_PREFIX}:published"

#     cached = cache_get(cache_key)

#     if cached is not None:
#         return cached

#     query = db.query(Package).filter(Package.status == StatusEnum.published)

#     if collection:
#         query = query.filter(collection_filters[collection].is_(True))

#     packages = query.order_by(
#         Package.display_order.asc(),
#         Package.created_at.desc(),
#     ).all()

#     data = [_serialize(package) for package in packages]

#     cache_set(cache_key, data)

#     return data


# # ============================================================
# # PUBLIC / ADMIN — GET PACKAGE BY ID
# # ============================================================


# def get_package_by_id(
#     db: Session,
#     package_id: int,
# ) -> dict:
#     """
#     Get a package by ID.

#     This function does not restrict status, so it can return
#     both draft and published packages.

#     Public routes should preferably use get_package_by_slug().
#     """

#     cache_key = f"{CACHE_PREFIX}:id:{package_id}"

#     cached = cache_get(cache_key)

#     if cached is not None:
#         return cached

#     pkg = db.query(Package).filter(Package.id == package_id).first()

#     if not pkg:
#         raise HTTPException(
#             status_code=404,
#             detail="Package not found",
#         )

#     data = _serialize(pkg)

#     cache_set(cache_key, data)

#     return data


# # ============================================================
# # PUBLIC — GET PACKAGE BY SLUG
# # ============================================================


# def get_package_by_slug(
#     db: Session,
#     slug: str,
# ) -> dict:
#     """
#     Get a published package by slug.
#     Used by the public package detail page.
#     """

#     cache_key = f"{CACHE_PREFIX}:slug:{slug}"

#     cached = cache_get(cache_key)

#     if cached is not None:
#         return cached

#     pkg = (
#         db.query(Package)
#         .filter(
#             Package.slug == slug,
#             Package.status == StatusEnum.published,
#         )
#         .first()
#     )

#     if not pkg:
#         raise HTTPException(
#             status_code=404,
#             detail="Package not found",
#         )

#     data = _serialize(pkg)

#     cache_set(cache_key, data)

#     return data


# # ============================================================
# # ADMIN — GET ALL PACKAGES
# # ============================================================


# def get_all_packages_admin(
#     db: Session,
# ) -> list[dict]:
#     """
#     Admin/creator view.

#     Includes:
#     - draft packages
#     - published packages
#     """

#     packages = (
#         db.query(Package)
#         .order_by(
#             Package.display_order.asc(),
#             Package.created_at.desc(),
#         )
#         .all()
#     )

#     return [_serialize(package) for package in packages]


# # ============================================================
# # CREATE PACKAGE
# # ============================================================


# def create_package(
#     db: Session,
#     payload: PackageCreate,
#     user_id: int,
# ) -> Package:
#     """
#     Create a new package.

#     destination_id is the authoritative destination relationship.
#     The legacy destination text field is synchronized automatically.

#     display_order: the package is inserted at the requested position
#     and all packages are renumbered 1..n. Empty / 0 adds it last.
#     """

#     # --------------------------------------------------------
#     # Validate destination
#     # --------------------------------------------------------

#     destination = _get_destination(
#         db,
#         payload.destination_id,
#     )

#     # --------------------------------------------------------
#     # Generate unique slug
#     # --------------------------------------------------------

#     slug = unique_slug(
#         db,
#         Package,
#         payload.title,
#     )

#     # --------------------------------------------------------
#     # Convert payload
#     # --------------------------------------------------------

#     package_data = payload.model_dump(
#         exclude={
#             "images",
#             "itinerary",
#             "destination",
#         }
#     )

#     # Requested position (handled by _place_in_order below)
#     requested_order = package_data.pop("display_order", None)

#     # destination_id is authoritative from the resolved destination
#     package_data.pop("destination_id", None)

#     # --------------------------------------------------------
#     # Create package
#     # --------------------------------------------------------

#     pkg = Package(
#         **package_data,
#         # temporary value, set properly by _place_in_order
#         display_order=0,
#         # destination_id is authoritative
#         destination_id=destination.id,
#         # Keep old destination column synchronized
#         destination=destination.place_name,
#         # Convert Pydantic image objects
#         images=[img.model_dump() for img in payload.images],
#         # Convert itinerary objects
#         itinerary=[item.model_dump() for item in payload.itinerary],
#         slug=slug,
#         created_by=user_id,
#     )

#     # --------------------------------------------------------
#     # Display order
#     # Must run BEFORE db.add(pkg) so the new package is not
#     # already part of the query result.
#     # --------------------------------------------------------

#     _place_in_order(
#         db,
#         pkg,
#         requested_order,
#     )

#     # --------------------------------------------------------
#     # Save (reorder + insert in one transaction)
#     # --------------------------------------------------------

#     db.add(pkg)

#     try:
#         db.commit()
#     except Exception:
#         db.rollback()
#         raise

#     db.refresh(pkg)

#     # --------------------------------------------------------
#     # Clear related caches
#     # --------------------------------------------------------

#     _invalidate_all_related_cache()

#     return pkg


# # ============================================================
# # UPDATE PACKAGE
# # ============================================================


# def update_package(
#     db: Session,
#     package_id: int,
#     payload: PackageUpdate,
# ) -> Package:
#     """
#     Update an existing package.

#     destination_id is the authoritative destination relationship.

#     display_order: when provided, the package is moved to that
#     position and all packages are renumbered 1..n, so no two
#     packages ever share the same order.
#     """

#     # --------------------------------------------------------
#     # Find package
#     # --------------------------------------------------------

#     pkg = db.query(Package).filter(Package.id == package_id).first()

#     if not pkg:
#         raise HTTPException(
#             status_code=404,
#             detail="Package not found",
#         )

#     # --------------------------------------------------------
#     # Convert update payload
#     # --------------------------------------------------------

#     update_data = payload.model_dump(exclude_unset=True)

#     # --------------------------------------------------------
#     # Handle destination change
#     # --------------------------------------------------------

#     if "destination_id" in update_data:

#         destination = _get_destination(
#             db,
#             update_data["destination_id"],
#         )

#         # Update FK
#         update_data["destination_id"] = destination.id

#         # Keep legacy text field synchronized
#         update_data["destination"] = destination.place_name

#     elif "destination" in update_data:
#         """
#         Do not allow the old text field to change
#         independently of destination_id.

#         Since destination_id is now authoritative,
#         ignore a standalone destination text update.
#         """

#         update_data.pop("destination", None)

#     # --------------------------------------------------------
#     # Update itinerary
#     # --------------------------------------------------------

#     if "itinerary" in update_data and update_data["itinerary"] is not None:
#         update_data["itinerary"] = [
#             item if isinstance(item, dict) else item.model_dump()
#             for item in update_data["itinerary"]
#         ]

#     # --------------------------------------------------------
#     # Update images
#     # --------------------------------------------------------

#     if "images" in update_data and update_data["images"] is not None:
#         update_data["images"] = [
#             img if isinstance(img, dict) else img.model_dump()
#             for img in update_data["images"]
#         ]

#     # --------------------------------------------------------
#     # Generate new slug when title changes
#     # --------------------------------------------------------

#     if "title" in update_data and update_data["title"] != pkg.title:
#         update_data["slug"] = unique_slug(
#             db,
#             Package,
#             update_data["title"],
#             exclude_id=pkg.id,
#         )

#     # --------------------------------------------------------
#     # Display order: take it out of update_data,
#     # it is applied by _place_in_order below
#     # --------------------------------------------------------

#     has_order_change = "display_order" in update_data
#     new_order = update_data.pop("display_order", None)

#     # --------------------------------------------------------
#     # Apply updates
#     # --------------------------------------------------------

#     for field, value in update_data.items():
#         setattr(
#             pkg,
#             field,
#             value,
#         )

#     # --------------------------------------------------------
#     # Display order: reposition and renumber everything 1..n
#     # --------------------------------------------------------

#     if has_order_change and new_order is not None:
#         _place_in_order(
#             db,
#             pkg,
#             new_order,
#             exclude_id=pkg.id,
#         )

#     # --------------------------------------------------------
#     # Save (reorder + update in one transaction)
#     # --------------------------------------------------------

#     try:
#         db.commit()
#     except Exception:
#         db.rollback()
#         raise

#     db.refresh(pkg)

#     # --------------------------------------------------------
#     # Clear related caches
#     # --------------------------------------------------------

#     _invalidate_all_related_cache()

#     return pkg


# # ============================================================
# # DELETE PACKAGE
# # ============================================================


# def delete_package(
#     db: Session,
#     package_id: int,
# ) -> None:
#     """
#     Delete a package and renumber the remaining ones 1..n.
#     """

#     pkg = db.query(Package).filter(Package.id == package_id).first()

#     if not pkg:
#         raise HTTPException(
#             status_code=404,
#             detail="Package not found",
#         )

#     db.delete(pkg)
#     db.flush()

#     _normalize_display_orders(db)

#     try:
#         db.commit()
#     except Exception:
#         db.rollback()
#         raise

#     # --------------------------------------------------------
#     # Clear related caches
#     # --------------------------------------------------------

#     _invalidate_all_related_cache()


# # ============================================================
# # ONE-TIME UTILITY — RENUMBER display_order AS 1, 2, 3, ...
# # ============================================================


# def renumber_display_orders(db: Session) -> int:
#     """
#     Optional: run once to clean existing data immediately.
#     (Every create / update / delete now also keeps orders clean.)

#     Returns the number of packages renumbered.
#     """

#     _normalize_display_orders(db)

#     db.commit()

#     _invalidate_all_related_cache()

#     return db.query(Package).count()



