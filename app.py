from flask import Flask, render_template
from model import db , Admin, Student, Company, JobPosition, Application, Placement

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


@app.route('/register')
def register():
    return render_template("register.html")

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/access')
def access_db():
    return render_template("access.html")


if __name__ == "__main__":
    app.run(debug=True)