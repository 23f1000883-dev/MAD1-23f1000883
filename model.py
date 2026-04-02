from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint
from datetime import datetime
from sqlalchemy import event
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Admin(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def set_password(self, raw_password: str) -> None:
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password or "", raw_password)

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
    is_blacklisted = db.Column(db.Boolean, nullable=False, default=False)
    is_approved = db.Column(db.Boolean, nullable=False, default=False)

    job_positions = db.relationship(
        "JobPosition", back_populates="company", cascade="all, delete-orphan"
    )

    def set_password(self, raw_password: str) -> None:
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password or "", raw_password)

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
    skills = db.Column(db.String(255), nullable=True)
    graduation_year = db.Column(db.Integer, nullable=True)
    resume_url = db.Column(db.String(255), nullable=True)
    is_deactivated = db.Column(db.Boolean, nullable=False, default=False)

    applications = db.relationship(
        "Application", back_populates="student", cascade="all, delete-orphan"
    )

    def set_password(self, raw_password: str) -> None:
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password or "", raw_password)

    def __repr__(self):
        return f"<Student>{self.full_name}>"


class JobPosition(db.Model):
    __tablename__ = "job_positions"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    eligibility_criteria = db.Column(db.String(255), nullable=True)
    required_skills = db.Column(db.String(255), nullable=True)
    experience_required = db.Column(db.String(120), nullable=True)
    application_deadline = db.Column(db.Date, nullable=True)
    location = db.Column(db.String(120), nullable=True)
    salary_lpa = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(30), nullable=False, default="pending")
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


_HASH_PREFIXES = ("scrypt:", "pbkdf2:")


def _ensure_password_hashed(mapper, connection, target) -> None:
    """Hash passwords automatically before insert/update if plain text is assigned."""
    password = getattr(target, "password", None)

    if not password:
        return

    if isinstance(password, str) and not password.startswith(_HASH_PREFIXES):
        target.password = generate_password_hash(password)


for _model in (Admin, Company, Student):
    event.listen(_model, "before_insert", _ensure_password_hashed)
    event.listen(_model, "before_update", _ensure_password_hashed)


def init_db(app) -> None:
    """Initialize database and create all tables programmatically (no data seeding)."""
    db.init_app(app)
    with app.app_context():
        db.create_all()
