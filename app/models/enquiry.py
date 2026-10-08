
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class Enquiry(Base):
    __tablename__ = "enquiries"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # Package this enquiry belongs to.
    # NULL for customized enquiries.
    package_id = Column(
        Integer,
        ForeignKey("packages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Seasoned/Batch this enquiry belongs to.
    # NULL for customized enquiries.
    seasoned_id = Column(
        Integer,
        ForeignKey("package_batches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Type/category selected in the enquiry form.
    # Examples:
    # pilgrimage, beach, family, mountains_adventure, custom
    package_type = Column(
        String(50),
        nullable=False,
        index=True,
    )

    # Destination.
    # Used by Custom Enquiry.
    # NULL for the global Plan a Trip enquiry.
    destination = Column(
        String(150),
        nullable=True,
        index=True,
    )

    # Customer name.
    name = Column(
        String(100),
        nullable=False,
    )

    # Customer phone / WhatsApp number.
    phone = Column(
        String(20),
        nullable=False,
        index=True,
    )

    # Number of adults.
    adults = Column(
        Integer,
        nullable=False,
    )

    # Number of kids.
    kids = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # Number of nights.
    nights = Column(
        Integer,
        nullable=False,
    )

    # Requested travel date.
    travel_date = Column(
        Date,
        nullable=False,
    )

    # Customer requirements / message.
    message = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationship with Package.
    package = relationship("Package")

    # Relationship with Seasoned/Batch.
    batch = relationship("PackageBatch")

    @property
    def package_title(self):
        return self.package.title if self.package else None











































# from datetime import datetime

# from sqlalchemy import (
#     Column,
#     Integer,
#     String,
#     Text,
#     Date,
#     DateTime,
#     ForeignKey,
# )
# from sqlalchemy.orm import relationship

# from app.db.database import Base


# class Enquiry(Base):
#     __tablename__ = "enquiries"

#     id = Column(
#         Integer,
#         primary_key=True,
#         index=True,
#     )

#     # Package this enquiry belongs to.
#     # NULL for customized enquiries.
#     package_id = Column(
#         Integer,
#         ForeignKey("packages.id", ondelete="SET NULL"),
#         nullable=True,
#         index=True,
#     )

#     # Batch is optional.
#     # NULL for customized enquiries.
#     batch_id = Column(
#         Integer,
#         ForeignKey("package_batches.id", ondelete="SET NULL"),
#         nullable=True,
#         index=True,
#     )

#     # Type/category selected in the enquiry form.
#     # Examples:
#     # pilgrimage, beach, family, mountains_adventure, custom
#     package_type = Column(
#         String(50),
#         nullable=False,
#         index=True,
#     )

#     # Destination.
#     # Used by Custom Enquiry.
#     # NULL for the global Plan a Trip enquiry.
#     destination = Column(
#         String(150),
#         nullable=True,
#         index=True,
#     )

#     # Customer name.
#     name = Column(
#         String(100),
#         nullable=False,
#     )

#     # Customer phone / WhatsApp number.
#     phone = Column(
#         String(20),
#         nullable=False,
#         index=True,
#     )

#     # Number of travellers.
#     travellers = Column(
#         Integer,
#         nullable=False,
#     )

#     # Requested travel date.
#     travel_date = Column(
#         Date,
#         nullable=False,
#     )

#     # Customer requirements / message.
#     message = Column(
#         Text,
#         nullable=True,
#     )

#     created_at = Column(
#         DateTime,
#         default=datetime.utcnow,
#         nullable=False,
#     )

#     updated_at = Column(
#         DateTime,
#         default=datetime.utcnow,
#         onupdate=datetime.utcnow,
#         nullable=False,
#     )

#     # Relationship with Package.
#     package = relationship("Package")

#     # Relationship with Batch.
#     batch = relationship("PackageBatch")

#     @property
#     def package_title(self):
#         return self.package.title if self.package else None






