import os

from flask import Flask, render_template, request, redirect, url_for

from database.db_connector import DBConnector
from database.models import db, init_app

# Initialize Flask app
app = Flask(__name__,
            static_folder=os.path.join(os.path.pardir, 'static'),
            template_folder=os.path.join(os.path.pardir, 'templates'))

# Adjust the SQLALCHEMY_DATABASE_URI using environment variables or a secure configuration method
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI',
                                                       'mysql+pymysql://root:Easton21!@localhost/Empty_CRM')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with the Flask app
init_app(app)

# Assuming you've set your environment variables for database connection
db = DBConnector()


# Route to render the index.html template
@app.route('/')
def home():
    """Route to render the index.html template."""
    return render_template('index.html')


# Route to handle form submission
@app.route('/submit-form', methods=['POST'])
def submit_form():
    """Route to handle form submission."""
    data = request.form
    resume_file = request.files['resume']  # Access the file
    resume_path = "path/to/store/" + resume_file.filename  # Placeholder for file saving logic

    # Combine 'address' and 'address_2', with handling for empty 'address_2'
    full_address = data['address']
    if data.get('address_2'):  # Checks if 'address_2' is not empty and is provided
        full_address += ", " + data['address_2']  # Adds 'address_2' to 'address' with a comma separator

    query = """
    INSERT INTO employees (first_name, last_name, email, phone, preferred_contact_method, address, city, state, 
    zipcode, resume_path)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (data['first_name'], data['last_name'], data['email'], data['phone'],
              data['preferred_contact_method'], full_address, data['city'],
              data['state'], data['zipcode'], resume_path)

    try:
        db.execute_query(query, params)
        return redirect(url_for('submission_success'))
    except Exception as e:
        error_message = f"An error occurred. Please try again. Error: {str(e)}"
        return render_template('error.html', error_message=error_message), 500


@app.route('/submission-success')
def submission_success():
    """Route to show success message after form submission."""
    return render_template('success.html')


# Route to serve the favicon
@app.route('/favicon.ico')
def favicon():
    """Route to serve the favicon."""
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    app.run(debug=True)
