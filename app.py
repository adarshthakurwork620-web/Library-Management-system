from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from datetime import date
import bcrypt
from datetime import timedelta
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = "secret123"

# ------------------ DB CONNECTION ------------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="adarsh10",
        database="library_db"
    )

# ------------------ HOME ------------------
@app.route('/')
def home():
    return render_template("index.html")

# ------------------ DASHBOARD ------------------
@app.route('/dashboard')
def dashboard():
    # print("SESSION ROLE:", session.get('role'))
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()
   
    # ADMIN DASHBOARD 👑
    if session.get('role') == 'admin':


        # all transactions with user + book
        cur.execute("""
            SELECT users.name, books.title, transactions.issue_date,
                   transactions.due_date, transactions.status, transactions.fine
            FROM transactions
            JOIN users ON users.id = transactions.user_id
            JOIN books ON books.id = transactions.book_id
            ORDER BY transactions.issue_date DESC
        """)
        
        all_transactions = cur.fetchall()

    
        # most issued book
        cur.execute("""
            SELECT books.title, COUNT(transactions.book_id) as total
            FROM transactions
            JOIN books ON books.id = transactions.book_id
            GROUP BY transactions.book_id
            ORDER BY total DESC
            LIMIT 1
        """)
        
        most_book = cur.fetchone()

        # total fine collected
        cur.execute("SELECT SUM(fine) FROM transactions")
        total_fine = cur.fetchone()[0]
        
        if total_fine is None:
            total_fine = 0

        cur.execute("SELECT COUNT(*) FROM books")
        total_books = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM users WHERE role='student'")
        total_users = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM transactions")
        total_transactions = cur.fetchone()[0]

        conn.close()

        return render_template(
            "dashboard.html",
            role="admin",
            total_books=total_books,
            total_users=total_users,
            total_transactions=total_transactions,
            most_book=most_book,
            total_fine=total_fine,
            all_transactions=all_transactions   # 👈 add this
        )

    # STUDENT DASHBOARD 👤
    else:
        # get user_id
        cur.execute("SELECT id FROM users WHERE email=%s", (session['user'],))
        user = cur.fetchone()
        user_id = user[0]
        
        # total books
        cur.execute("SELECT COUNT(*) FROM books")
        total_books = cur.fetchone()[0]
        
        # issued by this user
        cur.execute("""
            SELECT COUNT(*) FROM transactions 
            WHERE user_id=%s AND status='issued'
        """, (user_id,))
        issued_books = cur.fetchone()[0]
        
        # returned by this user
        cur.execute("""
            SELECT COUNT(*) FROM transactions 
            WHERE user_id=%s AND status='returned'
        """, (user_id,))
        returned_books = cur.fetchone()[0]

        return render_template(
            "dashboard.html",
            role="student",
            total_books=total_books,
            issued_books=issued_books,
            returned_books=returned_books
        )

# ------------------ REGISTER ------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # validation
        if not name or not email or not password:
            return "All fields are required ❌"
        
        if len(password) < 4:
            return "Password must be at least 4 characters ❌"
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email,hashed_password, "student")
        )

        conn.commit()
        conn.close()

        return "User Registered Successfully ✅"

    return render_template("register.html")

# ------------------ LOGIN (UPDATED WITH ROLE) ------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # validation
        if not email or not password:
            return "Enter all fields ❌"

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        
        if user:
            stored_password = user[3]
        
            # 🔐 verify password
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                session['user'] = user[2]
                session['role'] = user[4]
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

# ------------------ ADD BOOK (ADMIN ONLY) ------------------
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != 'admin':
        return "Access Denied ❌"

    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        quantity = request.form.get('quantity')

        # validation
        if not title or not author or not quantity:
            return "All fields are required ❌"
        
        if not quantity.isdigit():
            return "Quantity must be a number ❌"
        
        if int(quantity) < 0:
            return "Quantity cannot be negative ❌"

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO books (title, author, quantity) VALUES (%s, %s, %s)",
            (title, author, quantity)
        )

        conn.commit()
        conn.close()

        return redirect(url_for('view_books'))

    return render_template("add_book.html")

# ------------------ VIEW BOOKS ------------------
@app.route('/view_books')
def view_books():
    if 'user' not in session:
        return redirect(url_for('login'))

    search = request.args.get('search')

    conn = get_db_connection()
    cur = conn.cursor()

    if search:
        query = """
            SELECT * FROM books 
            WHERE title LIKE %s OR author LIKE %s
        """
        value = f"%{search}%"
        cur.execute(query, (value, value))
    else:
        cur.execute("SELECT * FROM books")

    books = cur.fetchall()
    conn.close()
    
    return render_template(
    "view_books.html",
    books=books,
    role=session.get('role')
    )
# ------------------ ISSUE BOOK ------------------
@app.route('/issue/<int:book_id>')
def issue_book(book_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE email=%s", (session['user'],))
    user = cur.fetchone()
    user_id = user[0]

    # check if already issued
    cur.execute("""
        SELECT * FROM transactions 
        WHERE user_id=%s AND book_id=%s AND status='issued'
    """, (user_id, book_id))
    
    already_issued = cur.fetchone()
    
    if already_issued:
        conn.close()
        return "You already issued this book ❌"

    cur.execute("SELECT quantity FROM books WHERE id=%s", (book_id,))
    book = cur.fetchone()

    if book[0] <= 0:
        conn.close()
        return "Book not available ❌"

    due_date = date.today() + timedelta(days=7)
    
    cur.execute(
        "INSERT INTO transactions (user_id, book_id, issue_date, due_date, status) VALUES (%s, %s, CURDATE(), %s, %s)",
        (user_id, book_id, due_date, "issued")
    )
    
    cur.execute("UPDATE books SET quantity = quantity - 1 WHERE id=%s", (book_id,))

    conn.commit()
    conn.close()

    return redirect(url_for('view_books'))

# ------------------ RETURN BOOK (WITH FINE) ------------------
@app.route('/return/<int:book_id>')
def return_book(book_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE email=%s", (session['user'],))
    user = cur.fetchone()
    user_id = user[0]

    cur.execute("""
    SELECT id, issue_date, due_date FROM transactions 
    WHERE user_id=%s AND book_id=%s AND status='issued'
    LIMIT 1
    """, (user_id, book_id))

    transaction = cur.fetchone()

    if not transaction:
        conn.close()
        return "No issued book found ❌"

    trans_id = transaction[0]
    issue_date = transaction[1]
    due_date = transaction[2]

    # fix date format
    # convert if needed
    if isinstance(due_date, str):
        due_date = date.fromisoformat(due_date)
    
    days_late = (date.today() - due_date).days
    
    fine = 0
    if days_late > 0:
        fine = days_late * 5
    cur.execute("""
        UPDATE transactions 
        SET status='returned', return_date=CURDATE(), fine=%s
        WHERE id=%s
    """, (fine, trans_id))

    cur.execute("UPDATE books SET quantity = quantity + 1 WHERE id=%s", (book_id,))

    conn.commit()
    conn.close()

    return f"Book Returned ✅ | Fine = ₹{fine}"

# ------------------ MY BOOKS ------------------
@app.route('/my_books')
def my_books():
        
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT books.title, transactions.issue_date, transactions.return_date, transactions.status, transactions.fine
        FROM transactions
        JOIN books ON transactions.book_id = books.id
        JOIN users ON transactions.user_id = users.id
        WHERE users.email=%s
    """, (session['user'],))

    data = cur.fetchall()
    
    new_data = []
    
    for row in data:
        row = list(row)
    
        # convert due_date to date
        if isinstance(row[2], str):
            row[2] = datetime.strptime(row[2], "%Y-%m-%d").date()
    
        new_data.append(row)
    
    data = new_data
    conn.close()

    return render_template(
        "my_books.html",
        my_books=data,
        current_date=date.today()
    )

# ------------------ DELETE BOOK (ADMIN ONLY) ------------------
@app.route('/delete/<int:id>')
def delete_book(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != 'admin':
        return "Access Denied ❌"

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM books WHERE id=%s", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for('view_books'))

# ------------------ EDIT BOOK (ADMIN ONLY) ------------------
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_book(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != 'admin':
        return "Access Denied ❌"

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        quantity = request.form.get('quantity')

        cur.execute(
            "UPDATE books SET title=%s, author=%s, quantity=%s WHERE id=%s",
            (title, author, quantity, id)
        )

        conn.commit()
        conn.close()

        return redirect(url_for('view_books'))

    cur.execute("SELECT * FROM books WHERE id=%s", (id,))
    book = cur.fetchone()
    conn.close()

    return render_template("edit_book.html", book=book)

# ------------------ RUN ------------------
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)