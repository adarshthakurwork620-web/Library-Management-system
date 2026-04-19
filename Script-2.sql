DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS users;

-- USERS TABLE
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT DEFAULT 'student'
);

-- BOOKS TABLE
CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    title TEXT,
    author TEXT,
    quantity INT DEFAULT 1
);

-- TRANSACTIONS TABLE
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INT,
    book_id INT,
    issue_date DATE,
    due_date DATE,
    return_date DATE,
    status TEXT,
    fine INT DEFAULT 0
);

-- CHECK
SELECT * FROM users;

delete  from transactions;

SELECT * FROM books;

SELECT * FROM transactions;

SELECT id, email, password FROM users;

-- ADMIN INSERT
INSERT INTO users (id,name, email, password, role)
VALUES ('1','Admin', '********', '****', 'admin');
