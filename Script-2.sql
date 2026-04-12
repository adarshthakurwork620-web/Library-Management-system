CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT,
    email TEXT UNIQUE,
    password BYTEA,
    role TEXT DEFAULT 'student'
);

CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    title TEXT,
    author TEXT,
    quantity INT DEFAULT 1
);

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id INT,
    book_id INT,
    issue_date DATE,
    due_date DATE,
    return_date DATE,
    status TEXT,
    fine INT DEFAULT 0
);

SELECT * FROM users;

SELECT * FROM books;

SELECT * FROM transactions;



INSERT INTO users (name, email, password, role)
VALUES ('Admin', 'admin@gmail.com', '$2b$12$KIXQ9wHc3GZ8q3WfQ8eZ5u1zQm6Zz5K0Q6QmFhV3bXGzRz7F1Yh2G', 'admin');
