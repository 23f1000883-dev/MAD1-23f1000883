from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint
from datetime import datetime

db = SQLAlchemy()


class Admin(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f'<Admin {self.username}>'


class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    industry = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(120), nullable=True)
    website = db.Column(db.String(255), nullable=True)

    job_positions = db.relationship(
        "JobPosition", back_populates="company", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Company {self.name}>"


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    course = db.Column(db.String(100), nullable=True)
    graduation_year = db.Column(db.Integer, nullable=True)

    applications = db.relationship(
        "Application", back_populates="student", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Student>{self.full_name}>"


class JobPosition(db.Model):
    __tablename__ = "job_positions"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(120), nullable=True)
    salary_lpa = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    posted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    company = db.relationship("Company", back_populates="job_positions")
    applications = db.relationship(
        "Application", back_populates="job_position", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<JobPosition {self.title}>"


class Application(db.Model):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "job_position_id", name="uq_student_job_application"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    job_position_id = db.Column(
        db.Integer, db.ForeignKey("job_positions.id"), nullable=False
    )
    status = db.Column(db.String(30), nullable=False, default="applied")
    applied_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    student = db.relationship("Student", back_populates="applications")
    job_position = db.relationship("JobPosition", back_populates="applications")
    placement = db.relationship(
        "Placement", back_populates="application", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Application student={self.student_id} job={self.job_position_id}>"


class Placement(db.Model):
    __tablename__ = "placements"

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(
        db.Integer, db.ForeignKey("applications.id"), unique=True, nullable=False
    )
    placed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    offered_package_lpa = db.Column(db.Float, nullable=True)

    application = db.relationship("Application", back_populates="placement")

    def __repr__(self):
        return f"<Placement application={self.application_id}>"


def init_db(app) -> None:
    """Initialize database and create all tables programmatically (no data seeding)."""
    db.init_app(app)
    with app.app_context():
        db.create_all()
