from flask import Flask, Response, flash, redirect, render_template, request, url_for, session
from model import db , Admin, Student, Company, JobPosition, Application, Placement
from werkzeug.security import check_password_hash as cph, generate_password_hash as gph
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from datetime import datetime
import os

app = Flask(__name__, template_folder="template")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///placement_portal.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "Project"  # Change this in production


@app.route('/')
def index():
    return render_template("access.html")


@app.route('/favicon.ico')
def favicon():
    return Response(status=204)


def ensure_student_password_column() -> None:
    """Backfill students.password for older SQLite schemas."""
    columns = db.session.execute(text("PRAGMA table_info(students)")).mappings().all()
    column_names = {column["name"] for column in columns}

    if columns and "password" not in column_names:
        try:
            db.session.execute(
                text("ALTER TABLE students ADD COLUMN password VARCHAR(120) DEFAULT ''")
            )
            db.session.commit()
        except OperationalError as error:
            db.session.rollback()
            if "duplicate column name" not in str(error).lower():
                raise


def ensure_company_auth_columns() -> None:
    """Backfill companies.email and companies.password for older SQLite schemas."""
    columns = db.session.execute(text("PRAGMA table_info(companies)")).mappings().all()
    column_names = {column["name"] for column in columns}

    if columns and "email" not in column_names:
        try:
            db.session.execute(
                text("ALTER TABLE companies ADD COLUMN email VARCHAR(120) DEFAULT ''")
            )
            db.session.commit()
        except OperationalError as error:
            db.session.rollback()
            if "duplicate column name" not in str(error).lower():
                raise

    if columns and "password" not in column_names:
        try:
            db.session.execute(
                text("ALTER TABLE companies ADD COLUMN password VARCHAR(120) DEFAULT ''")
            )
            db.session.commit()
        except OperationalError as error:
            db.session.rollback()
            if "duplicate column name" not in str(error).lower():
                raise


def ensure_company_blacklist_column() -> None:
    """Backfill companies.is_blacklisted for older SQLite schemas."""
    columns = db.session.execute(text("PRAGMA table_info(companies)")).mappings().all()
    column_names = {column["name"] for column in columns}

    if columns and "is_blacklisted" not in column_names:
        try:
            db.session.execute(
                text("ALTER TABLE companies ADD COLUMN is_blacklisted BOOLEAN DEFAULT 0")
            )
            db.session.commit()
        except OperationalError as error:
            db.session.rollback()
            if "duplicate column name" not in str(error).lower():
                raise


def ensure_company_approval_column() -> None:
    """Backfill companies.is_approved for older SQLite schemas."""
    columns = db.session.execute(text("PRAGMA table_info(companies)")).mappings().all()
    column_names = {column["name"] for column in columns}

    if columns and "is_approved" not in column_names:
        try:
            db.session.execute(
                text("ALTER TABLE companies ADD COLUMN is_approved BOOLEAN DEFAULT 0")
            )
            db.session.commit()
        except OperationalError as error:
            db.session.rollback()
            if "duplicate column name" not in str(error).lower():
                raise


def ensure_student_profile_columns() -> None:
    """Backfill students.resume_url for older SQLite schemas."""
    columns = db.session.execute(text("PRAGMA table_info(students)")).mappings().all()
    column_names = {column["name"] for column in columns}

    if columns and "resume_url" not in column_names:
        try:
            db.session.execute(
                text("ALTER TABLE students ADD COLUMN resume_url VARCHAR(255) DEFAULT ''")
            )
            db.session.commit()
        except OperationalError as error:
            db.session.rollback()
            if "duplicate column name" not in str(error).lower():
                raise


def ensure_student_deactivation_column() -> None:
    """Backfill students.is_deactivated for admin deactivate feature."""
    columns = db.session.execute(text("PRAGMA table_info(students)")).mappings().all()
    column_names = {column["name"] for column in columns}

    if columns and "is_deactivated" not in column_names:
        try:
            db.session.execute(
                text("ALTER TABLE students ADD COLUMN is_deactivated BOOLEAN DEFAULT 0")
            )
            db.session.commit()
        except OperationalError as error:
            db.session.rollback()
            if "duplicate column name" not in str(error).lower():
                raise



def remove_student_is_active_column() -> None:
    """Remove legacy students.is_active column from SQLite schema if it exists."""
    columns = db.session.execute(text("PRAGMA table_info(students)")).mappings().all()
    column_names = {column["name"] for column in columns}

    if columns and "is_active" in column_names:
        try:
            db.session.execute(text("ALTER TABLE students DROP COLUMN is_active"))
            db.session.commit()
        except OperationalError as error:
            db.session.rollback()
            print(f"Could not drop students.is_active column automatically: {error}")


def ensure_jobposition_columns() -> None:
    """Backfill new job_positions columns for status-based drive flow."""
    columns = db.session.execute(text("PRAGMA table_info(job_positions)")).mappings().all()
    column_names = {column["name"] for column in columns}

    if columns and "eligibility_criteria" not in column_names:
        try:
            db.session.execute(
                text("ALTER TABLE job_positions ADD COLUMN eligibility_criteria VARCHAR(255) DEFAULT ''")
            )
            db.session.commit()
        except OperationalError as error:
            db.session.rollback()
            if "duplicate column name" not in str(error).lower():
                raise

    if columns and "application_deadline" not in column_names:
        try:
            db.session.execute(
                text("ALTER TABLE job_positions ADD COLUMN application_deadline DATE")
            )
            db.session.commit()
        except OperationalError as error:
            db.session.rollback()
            if "duplicate column name" not in str(error).lower():
                raise

    if columns and "status" not in column_names:
        try:
            db.session.execute(
                text("ALTER TABLE job_positions ADD COLUMN status VARCHAR(30) DEFAULT 'pending'")
            )
            db.session.commit()
        except OperationalError as error:
            db.session.rollback()
            if "duplicate column name" not in str(error).lower():
                raise


def close_expired_job_positions() -> None:
    """Automatically close active job positions once deadline has passed."""
    today = datetime.utcnow().date()

    expired_positions = JobPosition.query.filter(
        JobPosition.is_active == True,
        JobPosition.application_deadline.isnot(None),
        JobPosition.application_deadline < today,
    ).all()

    if not expired_positions:
        return

    for position in expired_positions:
        position.is_active = False
        position.status = "closed"

    db.session.commit()


def ensure_default_admin() -> None:
    """Create pre-existing admin user if missing."""
    existing_admin = Admin.query.filter_by(username="admin").first()
    if not existing_admin:
        admin = Admin()
        admin.username = "admin"
        admin.email = "admin@placement.local"
        admin.password = gph("admin123")
        db.session.add(admin)
        db.session.commit()





# DATABASE Connection
db.init_app(app)  # Flask -----------> SQLAlchemy
with app.app_context():
    db.create_all()  # create missing tables
    ensure_student_password_column()  # fix older students table schema
    ensure_student_profile_columns()  # add resume for students
    ensure_student_deactivation_column()  # add student deactivate flag
    remove_student_is_active_column()  # remove legacy student activation column
    ensure_company_auth_columns()  # fix older companies table schema
    ensure_company_blacklist_column()  # fix older companies blacklist schema
    ensure_company_approval_column()  # add company approval flag
    ensure_jobposition_columns()  # add job status and metadata fields
    close_expired_job_positions()  # auto-close jobs with expired deadlines
    ensure_default_admin()  # keep pre-existing admin ready

@app.route('/home')
def hello_world():
    return 'Hello, World!'


@app.route('/access')
def access():
    return render_template("access.html")


@app.route('/login-page')
def login_page():
    return render_template("login.html")


@app.route('/register-page')
def register_page():
    return render_template("register.html")


# ADMIN LOGIN
@app.route('/admin-login', methods=['POST'])
def admin_login():
    username = request.form.get("username") or ""
    password = request.form.get("password") or ""

    admin = Admin.query.filter_by(username=username).first()
    if admin and cph(admin.password, password):
        print(f"Admin login success for username: {username}")
        session['admin_id'] = admin.id
        session['admin_username'] = admin.username
        flash("Welcome Admin.", "success")
        return redirect(url_for("admin_portal"))
    else:
        print(f"Admin login failed for username: {username}")
        flash("Invalid admin credentials.", "danger")
    
    return redirect(url_for("login_page"))


@app.route('/admin-portal')
def admin_portal():
    if 'admin_id' not in session:
        return redirect(url_for("access"))

    close_expired_job_positions()

    search = (request.args.get("search") or "").strip().lower()

    def safe_all(query_builder):
        try:
            return query_builder().all()
        except OperationalError as error:
            db.session.rollback()
            print(f"Admin portal query skipped due to schema mismatch: {error}")
            return []

    students = safe_all(lambda: Student.query.order_by(Student.id.desc()))
    companies = safe_all(lambda: Company.query.order_by(Company.id.desc()))
    job_positions = safe_all(lambda: JobPosition.query.order_by(JobPosition.id.desc()))
    applications = safe_all(lambda: Application.query.order_by(Application.id.desc()))
    placements = safe_all(lambda: Placement.query.order_by(Placement.id.desc()))

    if search:
        students = [
            student for student in students
            if search in str(student.id)
            or search in (student.full_name or "").lower()
            or search in (student.email or "").lower()
            or search in (student.phone or "").lower()
        ]
        companies = [
            company for company in companies
            if search in str(company.id)
            or search in (company.name or "").lower()
            or search in (company.email or "").lower()
            or search in (company.industry or "").lower()
            or search in (company.location or "").lower()
        ]

    blacklisted_count = sum(1 for company in companies if company.is_blacklisted)
    approved_companies_count = sum(1 for company in companies if company.is_approved)

    return render_template(
        'admin.html',
        students=students,
        companies=companies,
        job_positions=job_positions,
        applications=applications,
        placements=placements,
        blacklisted_count=blacklisted_count,
        approved_companies_count=approved_companies_count,
        search=search,
    )


@app.route('/admin/student/add', methods=['POST'])
def admin_add_student():
    if 'admin_id' not in session:
        return redirect(url_for("access"))
    flash("Manual add is disabled. Students must register through the registration page.", "warning")
    return redirect(url_for("admin_portal"))


@app.route('/admin/student/<int:student_id>/remove', methods=['POST'])
def admin_remove_student(student_id):
    if 'admin_id' not in session:
        return redirect(url_for("access"))

    student = Student.query.get(student_id)
    if student:
        db.session.delete(student)
        db.session.commit()
        flash("Student removed.", "info")

    return redirect(url_for("admin_portal"))


@app.route('/admin/student/<int:student_id>/edit', methods=['POST'])
def admin_edit_student(student_id):
    if 'admin_id' not in session:
        return redirect(url_for("access"))

    student = Student.query.get(student_id)
    if not student:
        return redirect(url_for("admin_portal"))

    full_name = request.form.get("full_name") or student.full_name
    phone = request.form.get("phone") or ""
    course = request.form.get("course") or ""
    graduation_year_raw = request.form.get("graduation_year") or "0"
    graduation_year = int(graduation_year_raw) if graduation_year_raw.isdigit() else student.graduation_year

    student.full_name = full_name
    student.phone = phone
    student.course = course
    student.graduation_year = graduation_year
    db.session.commit()
    flash("Student details updated.", "success")
    return redirect(url_for("admin_portal"))


@app.route('/admin/student/<int:student_id>/deactivate', methods=['POST'])
def deactivate_student(student_id):
    if 'admin_id' not in session:
        return redirect(url_for("access"))

    student = Student.query.get(student_id)
    if student:
        student.is_deactivated = True
        db.session.commit()
        flash("Student deactivated.", "warning")

    return redirect(url_for("admin_portal"))


@app.route('/admin/student/<int:student_id>/activate', methods=['POST'])
def activate_student(student_id):
    if 'admin_id' not in session:
        return redirect(url_for("access"))

    student = Student.query.get(student_id)
    if student:
        student.is_deactivated = False
        db.session.commit()
        flash("Student activated.", "success")

    return redirect(url_for("admin_portal"))


@app.route('/admin/company/add', methods=['POST'])
def admin_add_company():
    if 'admin_id' not in session:
        return redirect(url_for("access"))
    flash("Manual add is disabled. Companies must register through the registration page.", "warning")
    return redirect(url_for("admin_portal"))


@app.route('/admin/company/<int:company_id>/remove', methods=['POST'])
def admin_remove_company(company_id):
    if 'admin_id' not in session:
        return redirect(url_for("access"))

    company = Company.query.get(company_id)
    if company:
        db.session.delete(company)
        db.session.commit()
        flash("Company removed.", "info")

    return redirect(url_for("admin_portal"))


@app.route('/admin/company/<int:company_id>/edit', methods=['POST'])
def admin_edit_company(company_id):
    if 'admin_id' not in session:
        return redirect(url_for("access"))

    company = Company.query.get(company_id)
    if not company:
        return redirect(url_for("admin_portal"))

    industry = request.form.get("industry") or ""
    location = request.form.get("location") or ""
    website = request.form.get("website") or ""

    company.industry = industry
    company.location = location
    company.website = website
    db.session.commit()
    flash("Company details updated.", "success")
    return redirect(url_for("admin_portal"))


@app.route('/admin/company/<int:company_id>/blacklist', methods=['POST'])
def blacklist_company(company_id):
    if 'admin_id' not in session:
        return redirect(url_for("access"))

    company = Company.query.get(company_id)
    if company:
        company.is_blacklisted = True
        db.session.commit()
        flash("Company blacklisted.", "warning")

    return redirect(url_for("admin_portal"))


@app.route('/admin/company/<int:company_id>/allow', methods=['POST'])
def allow_company(company_id):
    if 'admin_id' not in session:
        return redirect(url_for("access"))

    company = Company.query.get(company_id)
    if company:
        company.is_blacklisted = False
        db.session.commit()
        flash("Company allowed again.", "success")

    return redirect(url_for("admin_portal"))


@app.route('/admin/company/<int:company_id>/approve', methods=['POST'])
def approve_company(company_id):
    if 'admin_id' not in session:
        return redirect(url_for("access"))

    company = Company.query.get(company_id)
    if company:
        company.is_approved = True
        db.session.commit()
        flash("Company approved.", "success")

    return redirect(url_for("admin_portal"))


@app.route('/admin/company/<int:company_id>/reject', methods=['POST'])
def reject_company(company_id):
    if 'admin_id' not in session:
        return redirect(url_for("access"))

    company = Company.query.get(company_id)
    if company:
        company.is_approved = False
        db.session.commit()
        flash("Company set to not approved.", "warning")

    return redirect(url_for("admin_portal"))


@app.route('/admin/job/<int:job_id>/approve', methods=['POST'])
def approve_job(job_id):
    if 'admin_id' not in session:
        return redirect(url_for("access"))

    job = JobPosition.query.get(job_id)
    if job:
        job.status = "approved"
        job.is_active = True
        db.session.commit()
        flash("Placement drive approved.", "success")

    return redirect(url_for("admin_portal"))


@app.route('/admin/job/<int:job_id>/reject', methods=['POST'])
def reject_job(job_id):
    if 'admin_id' not in session:
        return redirect(url_for("access"))

    job = JobPosition.query.get(job_id)
    if job:
        job.status = "rejected"
        job.is_active = False
        db.session.commit()
        flash("Placement drive rejected.", "warning")

    return redirect(url_for("admin_portal"))


@app.route('/admin/job/<int:job_id>/close', methods=['POST'])
def close_job(job_id):
    if 'admin_id' not in session:
        return redirect(url_for("access"))

    job = JobPosition.query.get(job_id)
    if job:
        job.status = "closed"
        job.is_active = False
        db.session.commit()
        flash("Placement drive closed.", "info")

    return redirect(url_for("admin_portal"))


# STUDENT LOGIN
@app.route('/login', methods=['POST'])
def login():
    email = request.form.get("email") or ""
    password = request.form.get("password") or ""

    student = Student.query.filter_by(email=email).first()
    if student and cph(student.password, password) and not student.is_deactivated:
        print(f"Student login success for email: {email}")
        session['student_id'] = student.id
        session['student_email'] = student.email
        session['student_name'] = student.full_name
        flash("Login successful.", "success")
        return redirect(url_for("student_dashboard"))
    else:
        print(f"Student login failed for email: {email}")
        flash("Invalid credentials or account deactivated.", "danger")
        return redirect(url_for("login_page"))


# COMPANY LOGIN
@app.route('/company-login', methods=['POST'])
def company_login():
    email = request.form.get("email") or ""
    password = request.form.get("password") or ""

    company = Company.query.filter_by(email=email).first()
    if company and cph(company.password, password) and company.is_approved and not company.is_blacklisted:
        print(f"Company login success for email: {email}")
        session['company_id'] = company.id
        session['company_email'] = company.email
        session['company_name'] = company.name
        flash("Login successful.", "success")
        return redirect(url_for("company_dashboard"))
    else:
        print(f"Company login failed for email: {email}")
        flash("Company is not approved / blacklisted / invalid credentials.", "danger")
    
    return redirect(url_for("login_page"))


@app.route('/company-dashboard')
def company_dashboard():
    if 'company_id' not in session:
        return redirect(url_for("access"))

    close_expired_job_positions()

    company = Company.query.get(session['company_id'])
    if not company or company.is_blacklisted:
        session.clear()
        return redirect(url_for("access"))

    positions = JobPosition.query.filter_by(company_id=company.id).order_by(JobPosition.id.desc()).all()
    applications = Application.query.join(JobPosition).filter(
        JobPosition.company_id == company.id
    ).order_by(Application.id.desc()).all()

    applicant_counts = {}
    for position in positions:
        applicant_counts[position.id] = 0

    for application in applications:
        position_id = application.job_position_id
        applicant_counts[position_id] = applicant_counts.get(position_id, 0) + 1

    return render_template(
        'company.html',
        company=company,
        positions=positions,
        applications=applications,
        applicant_counts=applicant_counts,
    )


@app.route('/company/student-details')
def company_student_details():
    if 'company_id' not in session:
        return redirect(url_for("access"))

    company = Company.query.get(session['company_id'])
    if not company or company.is_blacklisted:
        session.clear()
        return redirect(url_for("access"))

    student_id_raw = (request.args.get("student_id") or "").strip()
    if not student_id_raw.isdigit():
        flash("Please enter a valid student ID.", "warning")
        return redirect(url_for("company_dashboard"))

    student_id = int(student_id_raw)
    student = Student.query.get(student_id)
    if not student:
        flash("No student found with this ID.", "warning")
        return redirect(url_for("company_dashboard"))

    student_applications = Application.query.join(JobPosition).filter(
        Application.student_id == student.id,
        JobPosition.company_id == company.id
    ).order_by(Application.id.desc()).all()

    return render_template(
        'company_student_detail.html',
        company=company,
        student=student,
        student_applications=student_applications,
    )


@app.route('/company/job/create', methods=['POST'])
def company_create_job():
    if 'company_id' not in session:
        return redirect(url_for("access"))

    company = Company.query.get(session['company_id'])
    if not company or company.is_blacklisted:
        flash("Your company has been blacklisted and cannot create drives.", "warning")
        return redirect(url_for("access"))

    if not company.is_approved:
        flash("Your company must be approved by admin before creating drives. Please wait for approval.", "warning")
        return redirect(url_for("company_dashboard"))

    title = request.form.get("title") or ""
    description = request.form.get("description") or ""
    eligibility_criteria = request.form.get("eligibility_criteria") or ""
    deadline_raw = request.form.get("application_deadline") or ""
    location = request.form.get("location") or ""
    salary_raw = request.form.get("salary_lpa") or ""

    salary_lpa = None
    if salary_raw:
        try:
            salary_lpa = float(salary_raw)
        except ValueError:
            salary_lpa = None

    if not title:
        flash("Job title is required.", "warning")
        return redirect(url_for("company_dashboard"))

    application_deadline = None
    if deadline_raw:
        try:
            application_deadline = datetime.strptime(deadline_raw, "%Y-%m-%d").date()
        except ValueError:
            application_deadline = None

    position = JobPosition()
    position.company_id = company.id
    position.title = title
    position.description = description
    position.eligibility_criteria = eligibility_criteria
    position.application_deadline = application_deadline
    position.location = location
    position.salary_lpa = salary_lpa
    position.status = "pending"
    position.is_active = True

    db.session.add(position)
    db.session.commit()
    flash("Drive created and sent for admin approval.", "success")
    return redirect(url_for("company_dashboard"))


@app.route('/company/job/<int:position_id>/edit', methods=['POST'])
def company_edit_job(position_id):
    if 'company_id' not in session:
        return redirect(url_for("access"))

    company = Company.query.get(session['company_id'])
    if not company or company.is_blacklisted:
        flash("Your company has been blacklisted.", "warning")
        return redirect(url_for("access"))

    position = JobPosition.query.filter_by(id=position_id, company_id=company.id).first()
    if not position:
        return redirect(url_for("company_dashboard"))

    title = request.form.get("title") or ""
    description = request.form.get("description") or ""
    eligibility_criteria = request.form.get("eligibility_criteria") or ""
    deadline_raw = request.form.get("application_deadline") or ""
    location = request.form.get("location") or ""
    salary_raw = request.form.get("salary_lpa") or ""
    is_active = request.form.get("is_active") == "on"

    if not title:
        flash("Job title cannot be empty.", "warning")
        return redirect(url_for("company_dashboard"))

    application_deadline = None
    if deadline_raw:
        try:
            application_deadline = datetime.strptime(deadline_raw, "%Y-%m-%d").date()
        except ValueError:
            application_deadline = None

    salary_lpa = None
    if salary_raw:
        try:
            salary_lpa = float(salary_raw)
        except ValueError:
            salary_lpa = None

    position.title = title
    position.description = description
    position.eligibility_criteria = eligibility_criteria
    position.application_deadline = application_deadline
    position.location = location
    position.salary_lpa = salary_lpa
    position.is_active = is_active
    if position.status == "rejected":
        position.status = "pending"

    db.session.commit()
    flash("Drive updated.", "success")
    return redirect(url_for("company_dashboard"))


@app.route('/company/job/<int:position_id>/close', methods=['POST'])
def company_close_job(position_id):
    if 'company_id' not in session:
        return redirect(url_for("access"))

    position = JobPosition.query.filter_by(id=position_id, company_id=session['company_id']).first()
    if position:
        position.status = "closed"
        position.is_active = False
        db.session.commit()
        flash("Drive closed.", "info")

    return redirect(url_for("company_dashboard"))


@app.route('/company/job/<int:position_id>/remove', methods=['POST'])
def company_remove_job(position_id):
    if 'company_id' not in session:
        return redirect(url_for("access"))

    position = JobPosition.query.filter_by(id=position_id, company_id=session['company_id']).first()
    if position:
        db.session.delete(position)
        db.session.commit()
        flash("Drive removed.", "info")

    return redirect(url_for("company_dashboard"))


@app.route('/company/application/<int:application_id>/status', methods=['POST'])
def update_application_status(application_id):
    if 'company_id' not in session:
        return redirect(url_for("access"))

    allowed_statuses = {"applied", "shortlisted", "selected", "rejected"}
    new_status = (request.form.get("status") or "").lower()
    if new_status not in allowed_statuses:
        flash("Invalid application status.", "warning")
        return redirect(url_for("company_dashboard"))

    application = Application.query.join(JobPosition).filter(
        Application.id == application_id,
        JobPosition.company_id == session['company_id']
    ).first()

    if application:
        application.status = new_status
        db.session.commit()
        flash("Application status updated.", "success")

    return redirect(url_for("company_dashboard"))

 
# REGISTRATION (STUDENT or COMPANY)
@app.route('/register', methods=['POST'])
def register():
    account_type = request.form.get("account_type") or ""
    email = request.form.get("email") or ""
    password = request.form.get("password") or ""

    if not email or not password:
        flash("Email and password are required.", "warning")
        return redirect(url_for("register_page"))

    hash_password = gph(password)
    
    if account_type == "student":
        full_name = request.form.get("full_name") or ""
        phone = request.form.get("phone") or ""
        course = request.form.get("course") or ""
        graduation_year_raw = request.form.get("graduation_year") or "0"
        graduation_year = int(graduation_year_raw) if graduation_year_raw.isdigit() else 0

        if not full_name or not phone or not course or graduation_year == 0:
            flash("Please fill all student fields.", "warning")
            return redirect(url_for("register_page"))

        existing_student = Student.query.filter_by(email=email).first()
        if existing_student:
            flash("Student email already registered.", "warning")
            return redirect(url_for("register_page"))
        
        print(f"Student Registration - Name: {full_name}, Email: {email}, Phone: {phone}, Course: {course}, Grad Year: {graduation_year}")
        

        student = Student()
        student.full_name = full_name
        student.email = email
        student.password = hash_password
        student.phone = phone
        student.course = course
        student.graduation_year = graduation_year
        db.session.add(student)
        db.session.commit()
        flash("Student registration successful. Please login.", "success")
        
    elif account_type == "company":
        company_name = request.form.get("company_name") or ""
        industry = request.form.get("industry") or ""
        location = request.form.get("location") or ""
        website = request.form.get("website") or ""

        if not company_name or not industry or not location:
            flash("Please fill all required company fields.", "warning")
            return redirect(url_for("register_page"))

        existing_company = Company.query.filter(
            (Company.email == email) | (Company.name == company_name)
        ).first()
        if existing_company:
            flash("Company name or email already registered.", "warning")
            return redirect(url_for("register_page"))
        
        print(f"Company Registration - Name: {company_name}, Email: {email}, Industry: {industry}, Location: {location}, Website: {website}")
        
    
        company = Company()
        company.name = company_name
        company.email = email
        company.password = hash_password
        company.industry = industry
        company.location = location
        company.website = website
        company.is_approved = False
        db.session.add(company)
        db.session.commit()
        flash("Company registered. Wait for admin approval before login.", "info")

    else:
        flash("Please select a valid account type.", "warning")
        return redirect(url_for("register_page"))
    

    return redirect(url_for("login_page"))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("access"))


# STUDENT DASHBOARD
@app.route('/student-dashboard')
def student_dashboard():
    if 'student_id' not in session:
        return redirect(url_for("access"))

    close_expired_job_positions()
    
    student = Student.query.get(session['student_id'])
    if not student:
        return redirect(url_for("access"))
    
    # Get all applications for the student
    applications = Application.query.filter_by(student_id=student.id).all()
    
    # Get all active job positions (drives) from non-blacklisted companies
    active_positions = JobPosition.query.join(Company).filter(
        JobPosition.is_active == True,
        JobPosition.status == "approved",
        Company.is_blacklisted == False,
        Company.is_approved == True
    ).all()
    
    # Get applied job position IDs
    applied_position_ids = [app.job_position_id for app in applications]
    
    # Get all placements for the student
    placements = Placement.query.join(Application).filter(
        Application.student_id == student.id
    ).all()
    
    return render_template('student.html', 
                         student=student, 
                         applications=applications,
                         active_positions=active_positions,
                         applied_position_ids=applied_position_ids,
                         placements=placements)


@app.route('/student/company-details')
def student_company_details():
    if 'student_id' not in session:
        return redirect(url_for("access"))

    student = Student.query.get(session['student_id'])
    if not student:
        return redirect(url_for("access"))

    company_name = (request.args.get("company_name") or "").strip()
    if not company_name:
        flash("Please enter a company name.", "warning")
        return redirect(url_for("student_dashboard"))

    # Simple beginner-friendly search: case-insensitive exact name match
    companies = Company.query.filter_by(is_blacklisted=False, is_approved=True).all()
    matched_company = None
    for company in companies:
        if (company.name or "").strip().lower() == company_name.lower():
            matched_company = company
            break

    if not matched_company:
        flash("No approved company found with this name.", "warning")
        return redirect(url_for("student_dashboard"))

    company_positions = JobPosition.query.filter_by(
        company_id=matched_company.id,
        is_active=True,
        status="approved"
    ).order_by(JobPosition.id.desc()).all()

    return render_template(
        'student_company_detail.html',
        student=student,
        company=matched_company,
        company_positions=company_positions,
    )


@app.route('/student/job/<int:position_id>')
def student_job_details(position_id):
    if 'student_id' not in session:
        return redirect(url_for("access"))

    close_expired_job_positions()

    student = Student.query.get(session['student_id'])
    if not student:
        return redirect(url_for("access"))

    position = JobPosition.query.join(Company).filter(
        JobPosition.id == position_id,
        JobPosition.is_active == True,
        JobPosition.status == "approved",
        Company.is_blacklisted == False,
        Company.is_approved == True
    ).first()
    if not position:
        return redirect(url_for("student_dashboard"))

    has_applied = Application.query.filter_by(
        student_id=student.id,
        job_position_id=position.id
    ).first() is not None

    return render_template(
        'student_job_detail.html',
        student=student,
        position=position,
        has_applied=has_applied,
    )


@app.route('/student-preview')
def student_preview():
    """Public preview of student dashboard in a new tab from access page."""
    student = Student.query.order_by(Student.id.asc()).first()

    return render_template(
        'student.html',
        student=student,
        applications=[],
        active_positions=[],
        applied_position_ids=[],
        placements=[],
    )


# APPLY FOR JOB POSITION
@app.route('/student/apply/<int:position_id>', methods=['POST'])
def apply_job(position_id):
    if 'student_id' not in session:
        return redirect(url_for("access"))

    close_expired_job_positions()
    
    student_id = session['student_id']
    
    position = JobPosition.query.join(Company).filter(
        JobPosition.id == position_id,
        JobPosition.is_active == True,
        JobPosition.status == "approved",
        Company.is_blacklisted == False,
        Company.is_approved == True
    ).first()
    if not position:
        flash("This drive is not available.", "warning")
        return redirect(url_for("student_dashboard"))

    # Check if student already applied
    existing_application = Application.query.filter_by(
        student_id=student_id,
        job_position_id=position_id
    ).first()
    
    if existing_application:
        print(f"Student already applied for this position")
        flash("You have already applied for this drive.", "info")
        return redirect(url_for("student_dashboard"))
    
    try:
        application = Application()
        application.student_id = student_id
        application.job_position_id = position_id
        application.status = 'applied'
        db.session.add(application)
        db.session.commit()
        print(f"Application created successfully for position {position_id}")
        flash("Application submitted successfully.", "success")
    except Exception as e:
        print(f"Error creating application: {e}")
        db.session.rollback()
        flash("Could not submit application.", "danger")
    
    return redirect(url_for("student_dashboard"))


# VIEW APPLICATIONS
@app.route('/student/applications')
def view_applications():
    if 'student_id' not in session:
        return redirect(url_for("access"))
    
    student = Student.query.get(session['student_id'])
    if not student:
        return redirect(url_for("access"))
    
    applications = Application.query.filter_by(student_id=student.id).all()
    
    return render_template('student_applications.html', 
                         student=student,
                         applications=applications)


# EDIT STUDENT PROFILE
@app.route('/student/profile', methods=['GET', 'POST'])
def edit_profile():
    if 'student_id' not in session:
        return redirect(url_for("access"))
    
    student = Student.query.get(session['student_id'])
    if not student:
        return redirect(url_for("access"))
    
    if request.method == 'POST':
        phone = request.form.get("phone") or ""
        course = request.form.get("course") or ""
        resume_url = request.form.get("resume_url") or ""
        graduation_year_raw = request.form.get("graduation_year") or "0"
        graduation_year = int(graduation_year_raw) if graduation_year_raw.isdigit() else 0
        
        student.phone = phone
        student.course = course
        student.resume_url = resume_url
        student.graduation_year = graduation_year
        
        try:
            db.session.commit()
            print(f"Profile updated for student {student.id}")
            flash("Profile updated successfully.", "success")
        except Exception as e:
            print(f"Error updating profile: {e}")
            db.session.rollback()
            flash("Could not update profile.", "danger")
        
        return redirect(url_for("student_dashboard"))
    
    return render_template('student_profile.html', student=student)


# DELETE STUDENT ACCOUNT
@app.route('/student/delete-account', methods=['POST'])
def delete_student_account():
    if 'student_id' not in session:
        return redirect(url_for("access"))
    
    student_id = session['student_id']
    student = Student.query.get(student_id)
    
    if not student:
        return redirect(url_for("access"))
    
    try:
        # Delete all applications first (cascade will delete placements)
        Application.query.filter_by(student_id=student_id).delete()
        
        # Then delete the student
        db.session.delete(student)
        db.session.commit()
        
        # Clear the session
        session.clear()
        
        print(f"Student account deleted: {student.email}")
        flash("Your account has been deleted permanently.", "info")
        return redirect(url_for("access"))
    except Exception as e:
        print(f"Error deleting student account: {e}")
        db.session.rollback()
        flash("Could not delete account.", "danger")
        return redirect(url_for("student_dashboard"))


# WITHDRAW APPLICATION
@app.route('/student/application/<int:application_id>/withdraw', methods=['POST'])
def withdraw_application(application_id):
    if 'student_id' not in session:
        return redirect(url_for("access"))
    
    student_id = session['student_id']
    
    # Find application that belongs to this student
    application = Application.query.filter_by(
        id=application_id,
        student_id=student_id
    ).first()
    
    if not application:
        flash("Application not found.", "warning")
        return redirect(url_for("view_applications"))
    
    try:
        # Delete the application
        db.session.delete(application)
        db.session.commit()
        
        print(f"Application withdrawn: {application_id}")
        flash("Application withdrawn successfully.", "success")
    except Exception as e:
        print(f"Error withdrawing application: {e}")
        db.session.rollback()
        flash("Could not withdraw application.", "danger")
    
    return redirect(url_for("view_applications"))


# COMPANY PROFILE EDIT
@app.route('/company/profile/edit', methods=['GET', 'POST'])
def edit_company_profile():
    if 'company_id' not in session:
        return redirect(url_for("access"))
    
    company = Company.query.get(session['company_id'])
    if not company or company.is_blacklisted:
        session.clear()
        return redirect(url_for("access"))
    
    if request.method == 'POST':
        industry = request.form.get("industry") or ""
        location = request.form.get("location") or ""
        website = request.form.get("website") or ""
        
        if not industry or not location:
            flash("Industry and location are required.", "warning")
            return redirect(url_for("edit_company_profile"))
        
        try:
            company.industry = industry
            company.location = location
            company.website = website
            db.session.commit()
            
            print(f"Company profile updated: {company.name}")
            flash("Company profile updated successfully.", "success")
        except Exception as e:
            print(f"Error updating company profile: {e}")
            db.session.rollback()
            flash("Could not update profile.", "danger")
        
        return redirect(url_for("company_dashboard"))
    
    return render_template('company_profile.html', company=company)


# ADMIN: CREATE PLACEMENT
@app.route('/admin/placement/create', methods=['POST'])
def admin_create_placement():
    if 'admin_id' not in session:
        return redirect(url_for("access"))
    
    application_id_raw = request.form.get("application_id") or ""
    offered_package_raw = request.form.get("offered_package_lpa") or ""
    
    if not application_id_raw:
        flash("Application ID is required.", "warning")
        return redirect(url_for("admin_portal"))
    
    try:
        application_id = int(application_id_raw)
    except ValueError:
        flash("Invalid application ID.", "warning")
        return redirect(url_for("admin_portal"))
    
    application = Application.query.get(application_id)
    if not application:
        flash("Application not found.", "warning")
        return redirect(url_for("admin_portal"))
    
    # Check if placement already exists
    existing_placement = Placement.query.filter_by(application_id=application_id).first()
    if existing_placement:
        flash("Placement already exists for this application.", "warning")
        return redirect(url_for("admin_portal"))
    
    offered_package_lpa = None
    if offered_package_raw:
        try:
            offered_package_lpa = float(offered_package_raw)
        except ValueError:
            offered_package_lpa = None
    
    try:
        # Update application status to selected
        application.status = "selected"
        
        # Create placement
        placement = Placement()
        placement.application_id = application_id
        placement.offered_package_lpa = offered_package_lpa
        
        db.session.add(placement)
        db.session.commit()
        
        print(f"Placement created for application: {application_id}")
        flash("Placement created successfully.", "success")
    except Exception as e:
        print(f"Error creating placement: {e}")
        db.session.rollback()
        flash("Could not create placement.", "danger")
    
    return redirect(url_for("admin_portal"))


# ADMIN: UPDATE PLACEMENT
@app.route('/admin/placement/<int:placement_id>/edit', methods=['POST'])
def admin_edit_placement(placement_id):
    if 'admin_id' not in session:
        return redirect(url_for("access"))
    
    placement = Placement.query.get(placement_id)
    if not placement:
        flash("Placement not found.", "warning")
        return redirect(url_for("admin_portal"))
    
    offered_package_raw = request.form.get("offered_package_lpa") or ""
    
    offered_package_lpa = None
    if offered_package_raw:
        try:
            offered_package_lpa = float(offered_package_raw)
        except ValueError:
            offered_package_lpa = None
    
    try:
        placement.offered_package_lpa = offered_package_lpa
        db.session.commit()
        
        print(f"Placement updated: {placement_id}")
        flash("Placement updated successfully.", "success")
    except Exception as e:
        print(f"Error updating placement: {e}")
        db.session.rollback()
        flash("Could not update placement.", "danger")
    
    return redirect(url_for("admin_portal"))


# ADMIN: DELETE PLACEMENT
@app.route('/admin/placement/<int:placement_id>/remove', methods=['POST'])
def admin_remove_placement(placement_id):
    if 'admin_id' not in session:
        return redirect(url_for("access"))
    
    placement = Placement.query.get(placement_id)
    if not placement:
        flash("Placement not found.", "warning")
        return redirect(url_for("admin_portal"))
    
    try:
        # Set application status back to selected (not placed)
        application = placement.application
        if application:
            application.status = "selected"
        
        # Delete placement
        db.session.delete(placement)
        db.session.commit()
        
        print(f"Placement removed: {placement_id}")
        flash("Placement removed successfully.", "info")
    except Exception as e:
        print(f"Error removing placement: {e}")
        db.session.rollback()
        flash("Could not remove placement.", "danger")
    
    return redirect(url_for("admin_portal"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)