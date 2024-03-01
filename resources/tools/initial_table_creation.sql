USE empty_crm;
-- Create the 'employees' table
CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT,
    availability ENUM('NW', 'W', '~A', 'NA') NOT NULL,
    hired_date DATE NULL,
    pay DECIMAL(10, 2) NULL,
    pay_conversion VARCHAR(10) NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(25) NOT NULL,
    preferred_contact_method ENUM('Phone', 'Email') NULL,
    address VARCHAR(100) NOT NULL,
    city VARCHAR(25) NOT NULL,
    state VARCHAR(25) NOT NULL,
    zipcode VARCHAR(10) NOT NULL,
    job_id VARCHAR(15) NULL,
    resume_path VARCHAR(255) NULL,
    employee_type ENUM('Direct Placement', 'Contract', 'Contract to Hire',
                       'Full Time/Contract', '1099') NULL,
    PRIMARY KEY (id)
);

-- Create the 'clients' table
CREATE TABLE IF NOT EXISTS clients (
    id INT AUTO_INCREMENT,
    employer_company VARCHAR(100) NOT NULL,
    contact_person VARCHAR(100) NOT NULL,
    contact_phone VARCHAR(25) NULL,
    contact_email VARCHAR(255) NULL,
    address VARCHAR(100) NOT NULL,
    billing_allowance DECIMAL(20, 2) NOT NULL,
    active_employees INT NOT NULL,
    PRIMARY KEY (id)
);

-- Create the 'job_orders' table
CREATE TABLE IF NOT EXISTS job_orders (
    id INT AUTO_INCREMENT,
    po_order_number VARCHAR(15) NOT NULL UNIQUE,
    location VARCHAR(100) NOT NULL,
    company VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    active_employees INT NOT NULL,
    needed_employees INT NOT NULL,
    job_title VARCHAR(255) NOT NULL,
    position_type ENUM('Direct Placement', 'Contract', 'Contract to Hire',
                       'Full Time/Contract', '1099') NOT NULL,
    bill_rate_min DECIMAL(10, 2) NULL, 
    bill_rate_max DECIMAL(10, 2) NULL,
    bill_rate_conversion VARCHAR(10) NULL,
    pay_rate DECIMAL(10, 2) NULL,
    pay_rate_conversion VARCHAR(10) NULL,
    min_experience VARCHAR(255) NOT NULL,
    requirements VARCHAR(255) NULL,
    remote VARCHAR(15) NULL,
    job_description_path VARCHAR(255) NULL,
    notes_path VARCHAR(255) NULL,
    PRIMARY KEY (id)
);

-- Create the 'job2employer_ids' table
CREATE TABLE IF NOT EXISTS job2employer_ids (
    employee_id INT NOT NULL,
    job_order_id INT NOT NULL,
    client_id INT NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (job_order_id) REFERENCES job_orders(id),
    FOREIGN KEY (client_id) REFERENCES clients(id),
    PRIMARY KEY (employee_id, job_order_id, client_id)
);

-- Create the 'old_employee_job_orders' table
CREATE TABLE IF NOT EXISTS old_employee_job_orders (
    id INT AUTO_INCREMENT,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    hired_date DATE NULL,
    pay DECIMAL(10, 2) NULL,
    pay_conversion VARCHAR(10) NULL,
    po_order_number VARCHAR(15) NOT NULL,
    location VARCHAR(100) NOT NULL,
    company VARCHAR(255) NOT NULL,
    job_title VARCHAR(255) NOT NULL,
    position_type ENUM('Direct Placement', 'Contract', 'Contract to Hire',
                       'Full Time/Contract', '1099') NOT NULL,
    remote VARCHAR(15) NULL,
    PRIMARY KEY (id)
);

-- Create the 'old_company_job_orders' table
CREATE TABLE IF NOT EXISTS old_company_job_orders (
    id INT AUTO_INCREMENT,
    employer_company VARCHAR(100) NOT NULL,
    contact_person VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL,
    po_order_number VARCHAR(15) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    needed_employees INT NOT NULL,
    job_title VARCHAR(255) NOT NULL,
    position_type ENUM('Direct Placement', 'Contract', 'Contract to Hire',
                       'Full Time/Contract', '1099') NOT NULL,
    bill_rate_min DECIMAL(10, 2) NULL, 
    bill_rate_max DECIMAL(10, 2) NULL,
    bill_rate_conversion VARCHAR(10) NULL,
    pay_rate DECIMAL(10, 2) NULL,
    pay_rate_conversion VARCHAR(10) NULL,
    min_experience VARCHAR(255) NOT NULL,
    requirements VARCHAR(255) NULL,
    remote VARCHAR(15) NULL,
    job_description_path VARCHAR(255) NULL,
    notes_path VARCHAR(255) NULL,
    PRIMARY KEY (id)
);