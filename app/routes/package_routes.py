
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db

from app.schemas.package import (
    PackageCreate,
    PackageUpdate,
    PackageOut,
)

from app.services import package_service
from app.core.deps import require_admin_or_creator
from app.models.user import User


router = APIRouter(
    prefix="/packages",
    tags=["Packages"],
)


# ============================================================
# PUBLIC ROUTES
# ============================================================


@router.get(
    "",
    response_model=list[dict],
)
def list_published_packages(
    collection: str | None = Query(
        default=None,
        description=(
            "Optional discovery collection: "
            "popular, recommended, trending, featured, "
            "new, most_visited"
        ),
    ),
    db: Session = Depends(get_db),
):
    """
    Get published packages.

    Optional:

        ?collection=popular
        ?collection=recommended
        ?collection=trending
        ?collection=featured
        ?collection=new
        ?collection=most_visited

    A package may also have an optional
    seasoned_destination_id.
    """

    return package_service.get_published_packages(
        db,
        collection=collection,
    )


# ============================================================
# PUBLIC — GET PACKAGE BY SLUG
# ============================================================


@router.get(
    "/slug/{slug}",
    response_model=dict,
)
def get_package_by_slug(
    slug: str,
    db: Session = Depends(get_db),
):
    """
    Get a published package by slug.

    Response includes:

    - destination_id
    - seasoned_destination_id
    - package details
    """

    return package_service.get_package_by_slug(
        db,
        slug,
    )


# ============================================================
# ADMIN / CREATOR ROUTES
# ============================================================

# IMPORTANT:
# Keep /admin/* routes BEFORE /{package_id}
# so "admin" is never interpreted as an integer
# package ID.


# ------------------------------------------------------------
# ADMIN — GET ALL PACKAGES
# ------------------------------------------------------------


@router.get(
    "/admin/all",
    response_model=list[PackageOut],
    dependencies=[Depends(require_admin_or_creator)],
)
def list_all_packages(
    db: Session = Depends(get_db),
):
    """
    Get all packages for admin/creator management.

    Includes:
        - draft packages
        - published packages

    Each package can contain:

        destination_id
        seasoned_destination_id
    """

    return package_service.get_all_packages_admin(db)


# ------------------------------------------------------------
# ADMIN — CREATE PACKAGE
# ------------------------------------------------------------


@router.post(
    "/admin",
    response_model=PackageOut,
)
def create_package(
    payload: PackageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_creator),
):
    """
    Create a new package.

    Relationships:

        destination_id
            -> MostVisited.id

        seasoned_destination_id
            -> SeasonedDestination.id

    Both relationships are handled and validated
    by package_service.create_package().
    """

    return package_service.create_package(
        db,
        payload,
        current_user.id,
    )


# ------------------------------------------------------------
# ADMIN — UPDATE PACKAGE
# ------------------------------------------------------------


@router.put(
    "/admin/{package_id}",
    response_model=PackageOut,
    dependencies=[Depends(require_admin_or_creator)],
)
def update_package(
    package_id: int,
    payload: PackageUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing package.

    destination_id can be changed.

    seasoned_destination_id can also be:

        - assigned
        - changed
        - set to null

    The service validates the corresponding
    destination relationships.
    """

    return package_service.update_package(
        db,
        package_id,
        payload,
    )


# ------------------------------------------------------------
# ADMIN — DELETE PACKAGE
# ------------------------------------------------------------


@router.delete(
    "/admin/{package_id}",
    status_code=204,
    dependencies=[Depends(require_admin_or_creator)],
)
def delete_package(
    package_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a package.
    """

    package_service.delete_package(
        db,
        package_id,
    )

    return None


# ============================================================
# PUBLIC — GET PACKAGE BY ID
# ============================================================

# IMPORTANT:
# Keep this AFTER /admin routes.
#
# Example:
#
# GET /packages/1
#
# This endpoint currently calls get_package_by_id().
#
# NOTE:
# get_package_by_id() currently returns both draft and
# published packages. If this endpoint is public, consider
# restricting it to published packages.


@router.get(
    "/{package_id}",
    response_model=dict,
)
def get_package(
    package_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a package by ID.

    Response includes:

        destination_id
        seasoned_destination_id
    """

    return package_service.get_package_by_id(
        db,
        package_id,
    )
















































# from fastapi import APIRouter, Depends, Query
# from sqlalchemy.orm import Session

# from app.db.database import get_db

# from app.schemas.package import (
#     PackageCreate,
#     PackageUpdate,
#     PackageOut,
# )

# from app.services import package_service

# from app.core.deps import require_admin_or_creator
# from app.models.user import User

# router = APIRouter(
#     prefix="/packages",
#     tags=["Packages"],
# )


# # ============================================================
# # PUBLIC ROUTES
# # ============================================================


# @router.get(
#     "",
#     response_model=list[dict],
# )
# def list_published_packages(
#     collection: str | None = Query(
#         default=None,
#         description=(
#             "Optional discovery collection: "
#             "popular, recommended, trending, featured, "
#             "new, most_visited"
#         ),
#     ),
#     db: Session = Depends(get_db),
# ):
#     """
#     Get published packages.

#     Optional:
#         ?collection=popular
#         ?collection=recommended
#         ?collection=trending
#         ?collection=featured
#         ?collection=new
#         ?collection=most_visited
#     """

#     return package_service.get_published_packages(
#         db,
#         collection=collection,
#     )


# # ============================================================
# # PUBLIC — GET PACKAGE BY SLUG
# # ============================================================


# @router.get(
#     "/slug/{slug}",
#     response_model=dict,
# )
# def get_package_by_slug(
#     slug: str,
#     db: Session = Depends(get_db),
# ):
#     """
#     Get a published package by slug.
#     """

#     return package_service.get_package_by_slug(
#         db,
#         slug,
#     )


# # ============================================================
# # ADMIN / CREATOR ROUTES
# # ============================================================


# # IMPORTANT:
# # Keep /admin/* routes BEFORE /{package_id}
# # so "admin" is never interpreted as an integer package ID.


# # ------------------------------------------------------------
# # ADMIN — GET ALL PACKAGES
# # ------------------------------------------------------------


# @router.get(
#     "/admin/all",
#     response_model=list[PackageOut],
#     dependencies=[Depends(require_admin_or_creator)],
# )
# def list_all_packages(
#     db: Session = Depends(get_db),
# ):
#     """
#     Get all packages for admin/creator management.

#     Includes:
#         - draft packages
#         - published packages
#     """

#     return package_service.get_all_packages_admin(db)


# # ------------------------------------------------------------
# # ADMIN — CREATE PACKAGE
# # ------------------------------------------------------------


# @router.post(
#     "/admin",
#     response_model=PackageOut,
# )
# def create_package(
#     payload: PackageCreate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(require_admin_or_creator),
# ):
#     """
#     Create a new package.

#     destination_id is the authoritative
#     destination relationship.
#     """

#     return package_service.create_package(
#         db,
#         payload,
#         current_user.id,
#     )


# # ------------------------------------------------------------
# # ADMIN — UPDATE PACKAGE
# # ------------------------------------------------------------


# @router.put(
#     "/admin/{package_id}",
#     response_model=PackageOut,
#     dependencies=[Depends(require_admin_or_creator)],
# )
# def update_package(
#     package_id: int,
#     payload: PackageUpdate,
#     db: Session = Depends(get_db),
# ):
#     """
#     Update an existing package.

#     destination_id can be changed here.
#     The service validates the destination
#     and synchronizes the legacy destination
#     text field.
#     """

#     return package_service.update_package(
#         db,
#         package_id,
#         payload,
#     )


# # ------------------------------------------------------------
# # ADMIN — DELETE PACKAGE
# # ------------------------------------------------------------


# @router.delete(
#     "/admin/{package_id}",
#     status_code=204,
#     dependencies=[Depends(require_admin_or_creator)],
# )
# def delete_package(
#     package_id: int,
#     db: Session = Depends(get_db),
# ):
#     """
#     Delete a package.
#     """

#     package_service.delete_package(
#         db,
#         package_id,
#     )

#     return None


# # ============================================================
# # PUBLIC — GET PACKAGE BY ID
# # ============================================================
# #
# # Keep this AFTER /admin routes.
# #
# # Example:
# # GET /packages/1
# #
# # NOTE:
# # This endpoint currently calls get_package_by_id().
# # If this endpoint is publicly accessible, the service should
# # ensure that unpublished/draft packages are not exposed.
# # ============================================================


# @router.get(
#     "/{package_id}",
#     response_model=dict,
# )
# def get_package(
#     package_id: int,
#     db: Session = Depends(get_db),
# ):
#     """
#     Get a package by ID.
#     """

#     return package_service.get_package_by_id(
#         db,
#         package_id,
#     )
