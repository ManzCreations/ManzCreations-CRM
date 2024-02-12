from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy with no settings
db = SQLAlchemy()


class Employee(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    availability = db.Column(db.Enum('NW', 'W', '~A', 'NA'), nullable=False)
    hired_date = db.Column(db.Date, nullable=True)
    pay = db.Column(db.Numeric(10, 2), nullable=True)
    pay_conversion = db.Column(db.String(10), nullable=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(25), nullable=False)
    preferred_contact_method = db.Column(db.Enum('Phone', 'Email'))
    address = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(25), nullable=False)
    state = db.Column(db.String(25), nullable=False)
    zipcode = db.Column(db.String(10), nullable=False)
    job_id = db.Column(db.String(15), nullable=True)
    resume_path = db.Column(db.String(255), nullable=True)
    employee_type = db.Column(db.Enum('Direct Placement', 'Contract', 'Contract to Hire', 'Full Time/Contract', '1099'),
                              nullable=True)


def init_app(app):
    """Function to initialize the SQLAlchemy app"""
    db.init_app(app)
    with app.app_context():
        db.create_all()  # Creates the table if it doesn't already exist
