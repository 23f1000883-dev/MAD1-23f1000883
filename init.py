from datetime import date, datetime, timedelta

from app import app
from model import Application, Admin, Company, JobPosition, Placement, Student, db


# --------------------------
# Helper functions (simple)
# --------------------------
def get_or_create_admin(username: str, email: str, password: str) -> Admin:
    admin = Admin.query.filter_by(username=username).first()
    if admin:
        return admin

    admin = Admin()
    admin.username = username
    admin.email = email
    admin.password = password
    db.session.add(admin)
    db.session.flush()
    return admin


def get_or_create_company(
    name: str,
    email: str,
    password: str,
    industry: str,
    location: str,
    website: str,
    is_approved: bool = True,
    is_blacklisted: bool = False,
) -> Company:
    company = Company.query.filter_by(email=email).first()
    if company:
        return company

    company = Company()
    company.name = name
    company.email = email
    company.password = password
    company.industry = industry
    company.location = location
    company.website = website
    company.is_approved = is_approved
    company.is_blacklisted = is_blacklisted
    db.session.add(company)
    db.session.flush()
    return company


def get_or_create_student(
    full_name: str,
    email: str,
    password: str,
    phone: str,
    course: str,
    skills: str,
    graduation_year: int,
    resume_url: str = "",
    is_deactivated: bool = False,
) -> Student:
    student = Student.query.filter_by(email=email).first()
    if student:
        return student

    student = Student()
    student.full_name = full_name
    student.email = email
    student.password = password
    student.phone = phone
    student.course = course
    student.skills = skills
    student.graduation_year = graduation_year
    student.resume_url = resume_url
    student.is_deactivated = is_deactivated
    db.session.add(student)
    db.session.flush()
    return student


def get_or_create_job(
    company_id: int,
    title: str,
    description: str,
    eligibility_criteria: str,
    required_skills: str,
    experience_required: str,
    application_deadline: date,
    location: str,
    salary_lpa: float,
    status: str = "approved",
    is_active: bool = True,
) -> JobPosition:
    existing = JobPosition.query.filter_by(company_id=company_id, title=title).first()
    if existing:
        return existing

    job = JobPosition()
    job.company_id = company_id
    job.title = title
    job.description = description
    job.eligibility_criteria = eligibility_criteria
    job.required_skills = required_skills
    job.experience_required = experience_required
    job.application_deadline = application_deadline
    job.location = location
    job.salary_lpa = salary_lpa
    job.status = status
    job.is_active = is_active
    job.posted_at = datetime.utcnow()
    db.session.add(job)
    db.session.flush()
    return job


def get_or_create_application(student_id: int, job_position_id: int, status: str) -> Application:
    app_row = Application.query.filter_by(
        student_id=student_id,
        job_position_id=job_position_id,
    ).first()
    if app_row:
        return app_row

    app_row = Application()
    app_row.student_id = student_id
    app_row.job_position_id = job_position_id
    app_row.status = status
    app_row.applied_at = datetime.utcnow() - timedelta(days=2)
    db.session.add(app_row)
    db.session.flush()
    return app_row


def get_or_create_placement(application_id: int, offered_package_lpa: float) -> Placement:
    placement = Placement.query.filter_by(application_id=application_id).first()
    if placement:
        return placement

    placement = Placement()
    placement.application_id = application_id
    placement.offered_package_lpa = offered_package_lpa
    placement.placed_at = datetime.utcnow()
    db.session.add(placement)
    db.session.flush()
    return placement


# --------------------------
# Main seeding function
# --------------------------
def seed_dummy_data() -> None:
    with app.app_context():
        db.create_all()

        # 1) Admins
        admin_main = get_or_create_admin(
            username="admin",
            email="admin@placement.local",
            password="admin123",
        )
        admin_demo = get_or_create_admin(
            username="admin_demo",
            email="admin.demo@placement.local",
            password="admin123",
        )

        # 2) Companies
        company_1 = get_or_create_company(
            name="TechNova Pvt Ltd",
            email="hr@technova.com",
            password="company123",
            industry="Software",
            location="Bengaluru",
            website="https://technova.example",
            is_approved=True,
            is_blacklisted=False,
        )
        company_2 = get_or_create_company(
            name="DataNest Analytics",
            email="careers@datanest.com",
            password="company123",
            industry="Data Analytics",
            location="Hyderabad",
            website="https://datanest.example",
            is_approved=True,
            is_blacklisted=False,
        )

        # 3) Students
        student_1 = get_or_create_student(
            full_name="Aarav Sharma",
            email="aarav@student.com",
            password="student123",
            phone="9876543210",
            course="B.Tech CSE",
            skills="Python, Flask, SQL",
            graduation_year=2026,
            resume_url="/static/uploads/resumes/aarav_resume.pdf",
            is_deactivated=False,
        )
        student_2 = get_or_create_student(
            full_name="Diya Patel",
            email="diya@student.com",
            password="student123",
            phone="9123456780",
            course="B.Tech IT",
            skills="Java, Spring Boot, MySQL",
            graduation_year=2026,
            resume_url="/static/uploads/resumes/diya_resume.pdf",
            is_deactivated=False,
        )
        student_3 = get_or_create_student(
            full_name="Rohan Mehta",
            email="rohan@student.com",
            password="student123",
            phone="9988776655",
            course="B.E. ECE",
            skills="Embedded C, C++, IoT",
            graduation_year=2025,
            resume_url="/static/uploads/resumes/rohan_resume.pdf",
            is_deactivated=False,
        )

        # 4) Job Positions (linked to companies)
        today = date.today()
        job_1 = get_or_create_job(
            company_id=company_1.id,
            title="Software Engineer Intern",
            description="Work on Flask APIs and frontend integration.",
            eligibility_criteria="B.Tech CSE/IT, 2025/2026 pass-out",
            required_skills="Python, Flask, SQL, Git",
            experience_required="0-1 years",
            application_deadline=today + timedelta(days=20),
            location="Bengaluru",
            salary_lpa=6.5,
            status="approved",
            is_active=True,
        )
        job_2 = get_or_create_job(
            company_id=company_2.id,
            title="Data Analyst Trainee",
            description="Build dashboards and analyze student placement data.",
            eligibility_criteria="B.Tech / B.Sc CS, strong aptitude",
            required_skills="SQL, Excel, Power BI, Python",
            experience_required="0-1 years",
            application_deadline=today + timedelta(days=15),
            location="Hyderabad",
            salary_lpa=5.8,
            status="approved",
            is_active=True,
        )

        # 5) Applications (linked students <-> jobs)
        application_1 = get_or_create_application(
            student_id=student_1.id,
            job_position_id=job_1.id,
            status="selected",
        )
        application_2 = get_or_create_application(
            student_id=student_2.id,
            job_position_id=job_1.id,
            status="interview",
        )
        application_3 = get_or_create_application(
            student_id=student_3.id,
            job_position_id=job_2.id,
            status="shortlisted",
        )

        # 6) Placement (linked to one application)
        placement_1 = get_or_create_placement(
            application_id=application_1.id,
            offered_package_lpa=7.2,
        )

        # Keep application status aligned with placement
        application_1.status = "placed"

        db.session.commit()

        print("Dummy data seeded successfully.")
        print(f"Admins: 2 (includes {admin_main.username}, {admin_demo.username})")
        print(f"Companies: 2 ({company_1.name}, {company_2.name})")
        print(f"Students: 3 ({student_1.full_name}, {student_2.full_name}, {student_3.full_name})")
        print(f"Jobs: 2 ({job_1.title}, {job_2.title})")
        print(f"Applications: 3 ({application_1.id}, {application_2.id}, {application_3.id})")
        print(f"Placements: 1 ({placement_1.id})")


if __name__ == "__main__":
    seed_dummy_data()
