from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False, default="Administrator")
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, nullable=True, index=True)
    title = Column(String, nullable=False)
    aim = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False, default=0)
    pdf_filename = Column(String, nullable=True)
    is_published = Column(Boolean, nullable=False, default=True)

    concepts = relationship(
        "Concept",
        back_populates="chapter",
        cascade="all, delete-orphan",
        order_by="Concept.display_order",
    )


class Concept(Base):
    __tablename__ = "concepts"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, nullable=True, index=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    s_no = Column(String, nullable=True)
    title = Column(String, nullable=False)
    display_order = Column(Integer, nullable=False, default=0)
    concept_description = Column(Text, nullable=True)
    sessions = Column(String, nullable=True)
    learning_outcomes = Column(Text, nullable=True)
    integration_other_sub = Column(Text, nullable=True)
    teaching_materials_methods = Column(Text, nullable=True)
    library = Column(Text, nullable=True)
    activity = Column(Text, nullable=True)
    life_lesson = Column(Text, nullable=True)
    remarks = Column(Text, nullable=True)
    exhibit_ref = Column(String, nullable=True)

    chapter = relationship("Chapter", back_populates="concepts")
    exhibits = relationship(
        "Exhibit",
        back_populates="concept",
        cascade="all, delete-orphan",
        order_by="Exhibit.sort_order",
    )


class Exhibit(Base):
    __tablename__ = "exhibits"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, nullable=True, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)
    field_key = Column(String, nullable=False)
    field_type = Column(String, nullable=False, default="string")
    field_value = Column(Text, nullable=True)
    file_key = Column(String, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)

    concept = relationship("Concept", back_populates="exhibits")

