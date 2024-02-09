import pandas as pd
import mysql.connector
import random
from faker import Faker  # A library for generating fake data

# Database connection parameters
host = 'localhost'
user = 'root'
password = 'Easton21!'
database = 'Manz_CRM'

# Create a connection to the database
conn = mysql.connector.connect(
    host=host,
    user=user,
    password=password,
    database=database
)

# SQL query to fetch data from a table (replace 'your_table_name' with the actual table name)
table_name = 'website_record'  # Replace with the actual table name
query = f"SELECT * FROM {table_name}"

# Use Pandas to import data into a DataFrame
df = pd.read_sql(query, conn)

# Close the database connection
conn.close()

# Now you can work with the DataFrame 'df'
print(df)

# Database connection parameters
host = 'localhost'
user = 'root'
password = 'Easton21!'
database = 'Manz_CRM'

# Create a connection to the database
conn = mysql.connector.connect(
    host=host,
    user=user,
    password=password,
    database=database
)

# Number of random rows to generate
num_random_rows = 10

# Generate random data for each column
fake = Faker()
random_data = {
    'created_at': [fake.date_time_this_decade() for _ in range(num_random_rows)],
    'first_name': [fake.first_name() for _ in range(num_random_rows)],
    'last_name': [fake.last_name() for _ in range(num_random_rows)],
    'email': [fake.email() for _ in range(num_random_rows)],
    'phone': [fake.phone_number() for _ in range(num_random_rows)],
    'address': [fake.street_address() for _ in range(num_random_rows)],
    'city': [fake.city() for _ in range(num_random_rows)],
    'state': [fake.state() for _ in range(num_random_rows)],
    'zipcode': [fake.zipcode() for _ in range(num_random_rows)]
}

# Convert random data to a DataFrame
random_df = pd.DataFrame(random_data)

# Insert the new random data into the database
cursor = conn.cursor()

# Define the SQL statement to insert data
insert_query = f"INSERT INTO website_record (created_at, first_name, last_name, email, phone, address, city, state, zipcode) " \
               f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"

# Loop through the random DataFrame and insert rows into the database
for index, row in random_df.iterrows():
    values = tuple(row)
    cursor.execute(insert_query, values)

# Commit the changes to the database
conn.commit()

# Close the cursor and the database connection
cursor.close()
conn.close()

print(f'Inserted {num_random_rows} random rows into the database.')