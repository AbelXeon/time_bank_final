create database TIME_BANK;

use TIME_BANK;

create table branch(
branch_id int primary key not null,
branch_name varchar(50),
city varchar(50),
address varchar(50)
);

INSERT INTO branch(branch_id, branch_name, city, address)
VALUES
    (1, 'Main Branch', 'Addis Ababa', '22 Bole Road'),
    (2, 'North Branch', 'Mekele', '15 Hawzen Street'),
    (3, 'East Branch', 'Dire Dawa', '8 Kebele Avenue'),
    (4, 'South Branch', 'Hawassa', '3 Lake View Road'),
    (5, 'West Branch', 'Bahir Dar', '12 Tana Circle');


create table department(
dep_id int primary key not null,
dep_name varchar(50));

INSERT INTO department (dep_id, dep_name)
VALUES
    (101, 'Accountant'),
    (102, 'Manager'),
    (103, 'Finance'),
    (104, 'Security'),
    (105, 'Cleaner'),
    (107, 'HR');



create table customer(
cust_id int primary key not null,
cust_name varchar(50),
dob date,
phone int,
city varchar(50),
address varchar(50),
email varchar(50));


create table employee(
emp_id int primary key not null,
emp_name varchar(50),
gender enum('M','F'),
dep_id int,
branch_id int,
job_title varchar(50),
salary float,
dbo date,
phone int,
city varchar(50),
address varchar(50),
email varchar(50),
username VARCHAR(100),
passwords VARCHAR(255) UNIQUE NOT NULL,
foreign key (dep_id) references department(dep_id),
foreign key (branch_id) references branch(branch_id)
);

INSERT INTO employee (
    emp_id, 
    emp_name, 
    gender, 
    dep_id, 
    branch_id, 
    job_title, 
    salary, 
    dbo, 
    phone, 
    city, 
    address, 
    email, 
    username, 
    passwords
) VALUES (
    999, 
    'Test HR Employee', 
    'M', 
    107, 
    1,   
    'HR Specialist', 
    15000.00, 
    '1990-01-01', 
    911223344, 
    'Addis Ababa', 
    '22 Bole Road', 
    'testhr@timebank.com', 
    'testhr', 
    'securepassword123'  
);


CREATE TABLE accounts (
    account_no INT PRIMARY KEY,
    cust_id INT,
    balance FLOAT,
    opened_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    account_type VARCHAR(50),
    account_status ENUM('Active', 'Inactive', 'Closed') DEFAULT 'Active',
    interest_rate DECIMAL(5, 2) DEFAULT 0.00,
    minimum_balance FLOAT DEFAULT 0.00,
    currency VARCHAR(10) DEFAULT 'ETB'
);

CREATE TABLE transactions (
    transaction_id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    account_no INT NOT NULL, 
    transaction_type ENUM('Deposit', 'Withdrawal', 'Transfer') NOT NULL,
    transaction_amount FLOAT NOT NULL, 
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP, 
    transaction_description VARCHAR(255),
	transaction_status ENUM('Pending', 'Completed', 'Failed') DEFAULT 'Pending', 
    FOREIGN KEY (account_no) REFERENCES accounts (account_no) 
);


CREATE TABLE employee_branch (
    emp_id INT NOT NULL,
    branch_id INT NOT NULL,
    PRIMARY KEY (emp_id, branch_id),
    FOREIGN KEY (emp_id) REFERENCES employee (emp_id),
    FOREIGN KEY (branch_id) REFERENCES branch (branch_id)
);

CREATE TABLE loan (
    loan_id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    cust_id INT NOT NULL,
    account_no INT NOT NULL,
    loan_amount FLOAT NOT NULL,
    interest_rate DECIMAL(5, 2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status ENUM('Active', 'Paid', 'Defaulted') DEFAULT 'Active',
    FOREIGN KEY (cust_id) REFERENCES customer (cust_id),
    FOREIGN KEY (account_no) REFERENCES accounts (account_no)
);

CREATE TABLE loan_repayment (
    repayment_id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    loan_id INT NOT NULL,
    repayment_date DATE NOT NULL,
    amount_paid FLOAT NOT NULL,
    FOREIGN KEY (loan_id) REFERENCES loan (loan_id)
);

CREATE TABLE transaction_log (
    log_id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    transaction_id INT NOT NULL,
    account_no INT NOT NULL,
    transaction_type ENUM('Deposit', 'Withdrawal', 'Transfer') NOT NULL,
    transaction_amount FLOAT NOT NULL,
    transaction_date DATETIME NOT NULL,
    transaction_description VARCHAR(255),
    transaction_status ENUM('Pending', 'Completed', 'Failed') DEFAULT 'Pending',
    log_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES transactions (transaction_id),
    FOREIGN KEY (account_no) REFERENCES accounts (account_no)
);

DELIMITER $$

CREATE TRIGGER after_transaction_insert
AFTER INSERT ON transactions
FOR EACH ROW
BEGIN
   
    INSERT INTO transaction_log (
        transaction_id,
        account_no,
        transaction_type,
        transaction_amount,
        transaction_date,
        transaction_description,
        transaction_status
    ) VALUES (
        NEW.transaction_id,
        NEW.account_no,
        NEW.transaction_type,
        NEW.transaction_amount,
        NEW.transaction_date,
        NEW.transaction_description,
        NEW.transaction_status
    );
END$$

DELIMITER ;


CREATE TABLE employee_actions (
    action_id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    emp_id INT NOT NULL,
    action_type ENUM('Hire', 'Fire') NOT NULL,
    action_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    details TEXT,
    FOREIGN KEY (emp_id) REFERENCES employee (emp_id)
);


DELIMITER $$
CREATE TRIGGER after_employee_update
AFTER UPDATE ON employee
FOR EACH ROW
BEGIN
    IF OLD.job_title IS NULL AND NEW.job_title IS NOT NULL THEN
        INSERT INTO employee_actions (
            emp_id, action_type, details
        ) VALUES (
            NEW.emp_id, 'Hire', CONCAT('Employee hired as ', NEW.job_title)
        );
    ELSEIF OLD.job_title IS NOT NULL AND NEW.job_title IS NULL THEN
        INSERT INTO employee_actions (
            emp_id, action_type, details
        ) VALUES (
            NEW.emp_id, 'Fire', 'Employee fired'
        );
    END IF;
END$$
DELIMITER ;

CREATE VIEW bank_metrics AS
SELECT
    (SELECT COUNT(*) FROM employee) AS total_employees,
    (SELECT SUM(balance) FROM accounts) AS total_bank_balance,
    (SELECT COUNT(*) FROM employee WHERE dep_id = 107) AS hr_employees,
    (SELECT COUNT(*) FROM employee WHERE dep_id = 103) AS finance_employees,
    (SELECT COUNT(*) FROM employee WHERE dep_id = 101) AS accountant_employees,
    (SELECT COUNT(*) FROM employee WHERE dep_id = 104) AS security_employees,
    (SELECT COUNT(*) FROM employee WHERE dep_id = 105) AS cleaner_employees,
    (SELECT COUNT(*) FROM employee WHERE dep_id = 102) AS manager_employees;

DELIMITER $$

CREATE PROCEDURE get_bank_metrics()
BEGIN
    DECLARE total_employees INT;
    DECLARE total_bank_balance FLOAT;
    DECLARE hr_employees INT;
    DECLARE finance_employees INT;
    DECLARE accountant_employees INT;
    DECLARE security_employees INT;
    DECLARE cleaner_employees INT;
    DECLARE manager_employees INT;

    SELECT COUNT(*) INTO total_employees FROM employee;
 
    SELECT SUM(balance) INTO total_bank_balance FROM accounts;
    SELECT COUNT(*) INTO hr_employees FROM employee WHERE dep_id = 107;
    SELECT COUNT(*) INTO finance_employees FROM employee WHERE dep_id = 103;
    SELECT COUNT(*) INTO accountant_employees FROM employee WHERE dep_id = 101;
    SELECT COUNT(*) INTO security_employees FROM employee WHERE dep_id = 104;
    SELECT COUNT(*) INTO cleaner_employees FROM employee WHERE dep_id = 105;
    SELECT COUNT(*) INTO manager_employees FROM employee WHERE dep_id = 102;

    SELECT
        total_employees AS total_employees,
        total_bank_balance AS total_bank_balance,
        hr_employees AS hr_employees,
        finance_employees AS finance_employees,
        accountant_employees AS accountant_employees,
        security_employees AS security_employees,
        cleaner_employees AS cleaner_employees,
        manager_employees AS manager_employees;
END$$

DELIMITER ;


CREATE INDEX idx_account_no ON transactions (account_no);
CREATE INDEX idx_transaction_date ON transactions (transaction_date);
CREATE INDEX idx_cust_id ON accounts (cust_id);
