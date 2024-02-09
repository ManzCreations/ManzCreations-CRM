import random

from faker import Faker

from tools.mydb import execute_query

faker = Faker()


def insert_employee(data):
    query = """
    INSERT INTO employees (
        availability, hired_date, pay, pay_conversion, first_name, last_name, email,
        phone, address, city, state, zipcode, job_id, employee_type
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    execute_query(query, data)


def insert_client(data):
    query = """
    INSERT INTO clients (
        employer_company, contact_person, contact_phone, contact_email, address,
        billing_allowance, active_employees
    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    execute_query(query, data)


# Generate 20 random entries for the employees table
employees_entries = []
for _ in range(20):
    employees_entries.append({
        "availability": random.choice(['NW', 'W', '~A', 'NA']),
        "hired_date": faker.date_between(start_date='-5y', end_date='today').isoformat() if random.choice(
            [True, False]) else None,
        "pay": round(random.uniform(50000, 200000), 2) if random.choice([True, False]) else None,
        "pay_conversion": random.choice(['$/hr', '$/yr']) if random.choice([True, False]) else None,
        "first_name": faker.first_name(),
        "last_name": faker.last_name(),
        "email": faker.email(),
        "phone": faker.phone_number(),
        "address": faker.street_address(),
        "city": faker.city(),
        "state": faker.state_abbr(),
        "zipcode": faker.zipcode(),
        "job_id": str(faker.random_number(digits=5)) if random.choice([True, False]) else None,
        "employee_type": random.choice(
            ['Direct Placement', 'Contract', 'Contract to Hire', 'Full Time/Contract', '1099']) if random.choice(
            [True, False]) else None,
    })

# Generate 5 random entries for the clients table
clients_entries = []
for _ in range(5):
    clients_entries.append({
        "employer_company": faker.company(),
        "contact_person": faker.name(),
        "contact_phone": faker.phone_number(),
        "contact_email": faker.email(),
        "address": faker.address(),
        "billing_allowance": round(random.uniform(1000, 100000), 2),
        "active_employees": faker.random_int(min=0, max=100),
    })

# Assuming `employees_entries` and `clients_entries` are lists of dictionaries
# with the data for each table as generated previously
for employee in employees_entries:
    # Convert each employee dictionary to a tuple of values
    employee_data = tuple(employee.values())
    insert_employee(employee_data)

for client in clients_entries:
    # Convert each client dictionary to a tuple of values
    client_data = tuple(client.values())
    insert_client(client_data)
