from flask import Flask, redirect, render_template, request, url_for
from model import db , Admin, Student, Company, JobPosition, Application, Placement
from werkzeug.security import check_password_hash as cph, generate_password_hash as gph

app = Flask(__name__, template_folder="template")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///placement_portal.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# DATABASE Connection
db.init_app(app) # Flask -----------> SQLAlchemy
app.app_context().push() # without it changes will not happen
db.create_all() # it update or create the database tables

@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/access')
def access():
    return render_template("access.html")


# ADMIN LOGIN
@app.route('/admin-login', methods=['POST'])
def admin_login():
    username = request.form.get("username") or ""
    password = request.form.get("password") or ""

    admin = Admin.query.filter_by(username=username).first()
    if admin and cph(admin.password, password):
        print(f"Admin login success for username: {username}")
    else:
        print(f"Admin login failed for username: {username}")
    
    return redirect(url_for("access"))


# STUDENT LOGIN
@app.route('/login', methods=['POST'])
def login():
    email = request.form.get("email") or ""
    password = request.form.get("password") or ""

    student = Student.query.filter_by(email=email).first()
    if student and cph(student.password, password):
        print(f"Student login success for email: {email}")
    else:
        print(f"Student login failed for email: {email}")
    
    return redirect(url_for("access"))


# COMPANY LOGIN
@app.route('/company-login', methods=['POST'])
def company_login():
    email = request.form.get("email") or ""
    password = request.form.get("password") or ""

    company = Company.query.filter_by(email=email).first()
    if company and cph(company.password, password):
        print(f"Company login success for email: {email}")
    else:
        print(f"Company login failed for email: {email}")
    
    return redirect(url_for("access"))


# REGISTRATION (STUDENT or COMPANY)
@app.route('/register', methods=['POST'])
def register():
    account_type = request.form.get("account_type") or ""
    email = request.form.get("email") or ""
    password = request.form.get("password") or ""

    if not email or not password:
        return redirect(url_for("access"))

    hash_password = gph(password)
    
    if account_type == "student":
        full_name = request.form.get("full_name") or ""
        phone = request.form.get("phone") or ""
        course = request.form.get("course") or ""
        graduation_year_raw = request.form.get("graduation_year") or "0"
        graduation_year = int(graduation_year_raw) if graduation_year_raw.isdigit() else 0
        
        print(f"Student Registration - Name: {full_name}, Email: {email}, Phone: {phone}, Course: {course}, Grad Year: {graduation_year}")
        
        # TODO: Create new Student in database
        # try:
        #     new_student = Student(
        #         full_name=full_name,
        #         email=email,
        #         password=password,
        #         phone=phone,
        #         course=course,
        #         graduation_year=int(graduation_year)
        #     )
        #     db.session.add(new_student)
        #     db.session.commit()
        # except Exception as e:
        #     print(f"Error: {e}")
        student = Student()
        student.full_name = full_name
        student.email = email
        student.password = hash_password
        student.phone = phone
        student.course = course
        student.graduation_year = graduation_year
        db.session.add(student)
        db.session.commit()
        
    elif account_type == "company":
        company_name = request.form.get("company_name") or ""
        industry = request.form.get("industry") or ""
        location = request.form.get("location") or ""
        website = request.form.get("website") or ""
        
        print(f"Company Registration - Name: {company_name}, Email: {email}, Industry: {industry}, Location: {location}, Website: {website}")
        
        # TODO: Create new Company in database
        # try:
        #     new_company = Company(
        #         name=company_name,
        #         email=email,
        #         password=password,
        #         industry=industry,
        #         location=location,
        #         website=website
        #     )
        #     db.session.add(new_company)
        #     db.session.commit()
        # except Exception as e:
        #     print(f"Error: {e}")
        company = Company()
        company.name = company_name
        company.email = email
        company.password = hash_password
        company.industry = industry
        company.location = location
        company.website = website
        db.session.add(company)
        db.session.commit()
    

    return redirect(url_for("access"))


@app.route('/logout')
def logout():
    return redirect(url_for("access"))


if __name__ == "__main__":
    app.run(debug=True)