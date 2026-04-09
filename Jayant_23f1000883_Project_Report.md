# Placement Portal Project Report

**Name:** Jayant  
**Roll No:** 23f1000883  
**Course:** MAD I  
**Date:** 09 April 2026

---

## 1. Introduction

I developed a **Placement Portal** web application to manage campus recruitment activities in a structured way. The system supports three user roles:

1. **Admin**
2. **Company**
3. **Student**

The main goal of this project is to digitalize the placement workflow, starting from registration and verification, then job drive posting, student applications, and final placement tracking.

This project is built using the technologies required in the course instructions, with focus on backend logic, role-based access control, and clean user interface.

---

## 2. Objectives of the Project

The primary objectives were:

- To implement a multi-user role-based placement system.
- To allow companies to create drives and manage applications.
- To allow students to search and apply for drives.
- To allow admin to monitor and control the whole process.
- To maintain data consistency using relational database constraints.
- To ensure all core workflows work without JavaScript-based business logic.

---

## 3. Technology Stack (as per requirements)

The project has been implemented using the required stack:

- **Backend Framework:** Flask
- **Template Engine:** Jinja2
- **Database:** SQLite (programmatically created through SQLAlchemy models)
- **ORM:** Flask-SQLAlchemy / SQLAlchemy
- **Frontend:** HTML5 + CSS3 + Bootstrap 5
- **Authentication Security:** Werkzeug password hashing (`generate_password_hash`, `check_password_hash`)

### Important compliance point
No JavaScript is used for **core application logic**. Core operations such as authentication, role checks, CRUD operations, validations, and state transitions are handled in Flask routes and database layer.

---

## 4. Project Architecture and Design

The project follows a modular Flask structure:

- `app.py` → route handlers, session management, business logic, workflow rules.
- `model.py` → database schema (Admin, Student, Company, JobPosition, Application, Placement) and relationships.
- `template/` → Jinja2 templates for all role dashboards and pages.
- `static/uploads/resumes/` → uploaded resume files.
- `instance/` + SQLite DB → persistent storage.

The architecture is intentionally simple and readable so that each route can be traced directly to user actions from the UI.

---

## 5. Database Design

I implemented the following models:

1. **Admin**
   - Credentials for admin login.
2. **Student**
   - Basic details, course, skills, graduation year, resume URL, deactivation status.
3. **Company**
   - Company profile fields and approval/blacklist flags.
4. **JobPosition**
   - Drive details: title, criteria, required skills, deadline, salary, status.
5. **Application**
   - Bridge between student and job position with status tracking.
6. **Placement**
   - One-to-one mapping with selected application and package info.

### Key constraints and relationships

- **UniqueConstraint** on `(student_id, job_position_id)` prevents duplicate applications.
- Company to JobPosition: one-to-many.
- Student to Application: one-to-many.
- JobPosition to Application: one-to-many.
- Application to Placement: one-to-one.

This schema ensures clean workflow progression and avoids duplicate/invalid records.

---

## 6. Core Functionalities Implemented

### 6.1 Authentication and Access Control

- Separate login flows for Admin, Student, and Company.
- Session-based access checks on protected routes.
- Company login allowed only if company is approved and not blacklisted.
- Student login blocked if account is deactivated.
- Passwords are securely hashed.

### 6.2 Registration System

- Student self-registration with profile fields and optional resume upload.
- Company registration with pending status until admin approval.
- Validation for required fields and duplicate records.

### 6.3 Admin Module

Admin has full control over platform operations:

- View dashboard and analytics.
- View/manage students (edit, activate/deactivate, remove).
- View/manage companies (approve/reject, blacklist/allow, edit/remove).
- View/manage placement drives (approve/reject/close).
- View applications and placements.
- Create/edit/remove placement records.

### 6.4 Company Module

Company users can:

- Manage their profile.
- Create new job drives (initially pending approval).
- Edit, close, or remove job drives.
- View applicants for their drives.
- Update application statuses (`applied`, `shortlisted`, `interview`, `selected`, `placed`, `rejected`).

### 6.5 Student Module

Student users can:

- Edit profile and upload resume.
- View approved active drives.
- Search drives.
- View company details and job details.
- Apply to drives.
- Track application statuses.
- Withdraw applications.
- Delete account.
- View placement records.

---

## 7. Business Rules and Workflow Logic

The most important business rules implemented are:

1. Students cannot apply twice for the same drive.
2. Companies must be approved before they can access protected company operations.
3. Blacklisted companies are blocked from normal access.
4. Deactivated students are blocked from login.
5. Expired job drives are automatically closed by deadline logic.
6. Status transitions are controlled by role-specific routes.
7. Placement records are synchronized with application status (`placed`).

These rules were implemented in backend routes and database interactions, making the workflow robust and auditable.

---

## 8. User Interface Implementation

The UI is built using server-rendered Jinja templates and Bootstrap classes.

Current templates include pages for:

- Access/Login/Register flows
- Admin dashboard pages (overview, analytics, students, companies, jobs, applications, placements)
- Company dashboard and profile pages
- Student dashboard, profile, applications, and detail views

The interface is responsive and supports desktop/mobile layouts using Bootstrap grid and utility classes.

---

## 9. Validation, Error Handling, and Security

### Validation

- Required field checks in forms and backend.
- Numeric/date parsing checks where needed.
- Duplicate user/application checks.

### Error handling

- Flash messages to communicate success/failure to user.
- Transaction rollback on DB exceptions.
- Route-level guard checks for unauthorized access.

### Security

- Password hashing through Werkzeug.
- Session-based authorization checks.
- Cookies configured with secure options (`HttpOnly`, `SameSite`, optional secure flag).

---

## 10. Requirement Compliance Summary

Based on implementation and verification:

- Flask + Jinja2 + SQLite stack is used.
- Multi-role system (Admin/Company/Student) is implemented.
- Programmatic schema creation is implemented.
- Core logic is implemented in backend (no JS dependency for core behavior).
- Validation, status management, and role checks are present.
- Full end-to-end placement lifecycle is implemented.

Hence, the project aligns with the expected requirements of the course implementation guidelines.

---

## 11. Declaration on LLM Usage

I confirm the following:

- **The core project logic, workflow design, route implementation, and database modeling were developed by me.**
- I used **LLM assistance only for styling-related refinements** (for example, improving visual structure and Bootstrap-level UI polish).
- The central functionality and major engineering decisions are my own work.

---

## 12. Conclusion

This project demonstrates a complete role-based placement management system with real-world workflow controls. Through this project, I strengthened my understanding of:

- Flask route design and session management
- Database schema design with SQLAlchemy
- Role-based authorization and status-driven workflow
- Form validation and exception handling
- Building responsive UI using Bootstrap with Jinja templates

Overall, the Placement Portal satisfies the functional requirements and provides a solid, extensible base for future enhancements such as email notifications, pagination, and advanced reporting.

---

**End of Report**