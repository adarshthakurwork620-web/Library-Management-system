from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import os
import bcrypt
from datetime import date, datetime, timedelta

app = Flask(__name__)
app.secret_key = "secret123"

# ------------------ DB CONNECTION ------------------
import psycopg2
import os

def get_db_connection():
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    return conn

# ------------------ HOME ------------------
@app.route('/')
def home():
    return render_template("index.html")

# ------------------ REGISTER ------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        if not name or not email or not password:
            return "All fields required ❌"

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            (name, email, hashed_password, "student")
        )

        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template("register.html")

# ------------------ LOGIN ------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cur.fetchone()

        if user:
            stored_password = user["password"]

            if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                session['user'] = user["email"]
                session['role'] = user["role"]
                return redirect(url_for('view_books'))
            else:
                return "Invalid Password ❌"
        else:
            return "User not found ❌"

    return render_template("login.html")

# ------------------ LOGOUT ------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ------------------ VIEW BOOKS ------------------
@app.route('/view_books')
def view_books():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM books")
    books = cur.fetchall()

    conn.close()

    return render_template("view_books.html", books=books, role=session.get('role'))

# ------------------ ADD BOOK ------------------
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if 'user' not in session or session.get('role') != 'admin':
        return "Access Denied ❌"

    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        quantity = request.form.get('quantity')

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO books (title, author, quantity) VALUES (?, ?, ?)",
            (title, author, quantity)
        )

        conn.commit()
        conn.close()

        return redirect(url_for('view_books'))

    return render_template("add_book.html")

# ------------------ ISSUE BOOK ------------------
@app.route('/issue/<int:book_id>')
def issue_book(book_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE email=?", (session['user'],))
    user = cur.fetchone()
    user_id = user["id"]

    cur.execute("SELECT quantity FROM books WHERE id=?", (book_id,))
    book = cur.fetchone()

    if book["quantity"] <= 0:
        return "Not available ❌"

    due_date = date.today() + timedelta(days=7)

    cur.execute(
        "INSERT INTO transactions (user_id, book_id, issue_date, due_date, status) VALUES (?, ?, ?, ?, ?)",
        (user_id, book_id, date.today(), due_date, "issued")
    )

    cur.execute("UPDATE books SET quantity = quantity - 1 WHERE id=?", (book_id,))

    conn.commit()
    conn.close()

    return redirect(url_for('view_books'))

# ------------------ RETURN BOOK ------------------
@app.route('/return/<int:book_id>')
def return_book(book_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE email=?", (session['user'],))
    user = cur.fetchone()
    user_id = user["id"]

    cur.execute("""
        SELECT id, due_date FROM transactions 
        WHERE user_id=? AND book_id=? AND status='issued'
    """, (user_id, book_id))

    trans = cur.fetchone()

    if not trans:
        return "No book issued ❌"

    due_date = datetime.strptime(trans["due_date"], "%Y-%m-%d").date()
    days_late = (date.today() - due_date).days
    fine = max(0, days_late * 5)

    cur.execute(
        "UPDATE transactions SET status='returned', return_date=?, fine=? WHERE id=?",
        (date.today(), fine, trans["id"])
    )

    cur.execute("UPDATE books SET quantity = quantity + 1 WHERE id=?", (book_id,))

    conn.commit()
    conn.close()

    return f"Returned ✅ Fine: ₹{fine}"

# ------------------ RUN ------------------
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)