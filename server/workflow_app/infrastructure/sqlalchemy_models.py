from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SAProject(Base):
    __tablename__ = "workflow_app_project"

    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False)
    manager = Column(String(100), nullable=False)
    organization = Column(String(255), nullable=False)
    code = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class SAResearcher(Base):
    __tablename__ = "workflow_app_researcher"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    role = Column(String(100), nullable=False)
    email = Column(String(254), nullable=False)
    organization = Column(String(255), nullable=False)
    major = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class SAProjectMember(Base):
    __tablename__ = "workflow_app_projectmember"

    id = Column(Integer, primary_key=True)
    project_id = Column(String, ForeignKey("workflow_app_project.id"), nullable=False)
    researcher_id = Column(Integer, ForeignKey("workflow_app_researcher.id"), nullable=False)
    role = Column(String(100), nullable=False)
    contribution = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
