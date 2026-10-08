import enum
from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.db.database import Base


class BlogStatus(str, enum.Enum):
    draft = "draft"
    published = "published"


class Blog(Base):
    __tablename__ = "blogs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(220), nullable=False)
    slug = Column(String(240), unique=True, index=True, nullable=False)
    excerpt = Column(String(400), nullable=True)
    content = Column(Text, nullable=False)
    cover_image = Column(JSON, nullable=True)  # {url, public_id}
    target_keyword = Column(String(150), nullable=True)  # for the SEO checklist
    meta_description = Column(String(300), nullable=True)
    status = Column(
        Enum(BlogStatus), default=BlogStatus.draft, nullable=False, index=True
    )
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

