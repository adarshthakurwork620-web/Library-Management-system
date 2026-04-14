from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import psycopg2.extras
import os
from datetime import date, timedelta
from datetime import date

app = Flask(__name__)
app.secret_key = "secret123"

# ------------------ DB CONNECTION ------------------
def get_db_connection():
    return psycopg2.connect(
        "postgresql://library_db_9qy8_user:NRKVSQafCs3F4AGbuWsR8SJcEpzOfHK3@dpg-d7do5vd7vvec73etufb0-a.ohio-postgres.render.com/library_db_9qy8",
        sslmode='require'
    )

# ------------------ HOME ------------------
@app.route('/')
def home():
    return render_template("index.html")
# ------------------ DASHBOARD ------------------
@app.route('/dashboard')
def dashboard():

    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    # ---------------- ADMIN ----------------
    if session.get('role') == 'admin':

        # All transactions
        cur.execute("""
            SELECT users.name, books.title, transactions.issue_date, 
                   transactions.due_date, transactions.status, transactions.fine
            FROM transactions
            JOIN users ON users.id = transactions.user_id
            JOIN books ON books.id = transactions.book_id
            ORDER BY transactions.issue_date DESC
        """)
        all_transactions = cur.fetchall()

        # Most issued book
        cur.execute("""
            SELECT books.title, COUNT(*) as total
            FROM transactions
            JOIN books ON books.id = transactions.book_id
            GROUP BY books.title
            ORDER BY total DESC
            LIMIT 1
        """)
        most_book = cur.fetchone()

        # Total fine
        cur.execute("SELECT SUM(fine) FROM transactions")
        total_fine = cur.fetchone()[0] or 0

        # Stats
        cur.execute("SELECT COUNT(*) FROM books")
        total_books = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM users WHERE role='student'")
        total_users = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM transactions")
        total_transactions = cur.fetchone()[0]

        cur.close()
        conn.close()

        return render_template(
            "dashboard.html",
            role="admin",
            total_books=total_books,
            total_users=total_users,
            total_transactions=total_transactions,
            most_book=most_book,
            total_fine=total_fine,
            all_transactions=all_transactions
        )

    # ---------------- STUDENT ----------------
    else:
        cur.execute("SELECT id FROM users WHERE email=%s", (session['user'],))
        user = cur.fetchone()
        user_id = user[0]

        # Total books
        cur.execute("SELECT COUNT(*) FROM books")
        total_books = cur.fetchone()[0]

        # Issued books
        cur.execute("""
            SELECT COUNT(*) FROM transactions 
            WHERE user_id=%s AND status='issued'
        """, (user_id,))
        issued_books = cur.fetchone()[0]

        # Returned books
        cur.execute("""
            SELECT COUNT(*) FROM transactions 
            WHERE user_id=%s AND status='returned'
        """, (user_id,))
        returned_books = cur.fetchone()[0]

        cur.close()
        conn.close()

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

        if not name or not email or not password:
            return "All fields required ❌"

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, password, "student")   # ✅ plain password
        )

        conn.commit()
        cur.close()
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

        cur.execute("SELECT email, password, role FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            db_email, db_password, db_role = user    
            # FIX memory issue
            db_password = bytes(db_password).decode('utf-8')       
            if password.strip() == db_password.strip():
                session['user'] = db_email
                session['role'] = db_role
                return redirect('/view_books')
            else:
                return "Invalid Password ❌"

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

    cur.close()
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
            "INSERT INTO books (title, author, quantity) VALUES (%s, %s, %s)",
            (title, author, quantity)
        )

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('view_books'))

    return render_template("add_book.html")

# ------------------ ISSUE BOOK ------------------
@app.route('/issue/<int:book_id>')
def issue_book(book_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # user fetch
    cur.execute("SELECT id FROM users WHERE email=%s", (session['user'],))
    user = cur.fetchone()

    if not user:
        return "User not found ❌"

    user_id = user["id"]

    # check already issued
    cur.execute("""
        SELECT * FROM transactions
        WHERE user_id=%s AND status='issued'
    """, (user_id,))
    
    if cur.fetchone():
        return "Already have a book ❌"

    # book fetch
    cur.execute("SELECT * FROM books WHERE id=%s", (book_id,))
    book = cur.fetchone()

    if not book:
        return "Book not found ❌"

    if book["quantity"] <= 0:
        return "Not available ❌"

    # issue
    due_date = date.today() + timedelta(days=7)

    cur.execute("""
        INSERT INTO transactions 
        (user_id, book_id, issue_date, due_date, status) 
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, book_id, date.today(), due_date, "issued"))

    cur.execute("UPDATE books SET quantity = quantity - 1 WHERE id=%s", (book_id,))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('view_books'))

# ------------------ RETURN BOOK ------------------
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
        SELECT id, due_date FROM transactions 
        WHERE user_id=%s AND book_id=%s AND status='issued'
    """, (user_id, book_id))

    trans = cur.fetchone()

    if not trans:
        return "No book issued ❌"

    due_date = trans[1]
    days_late = (date.today() - due_date).days
    fine = max(0, days_late * 5)

    cur.execute(
        "UPDATE transactions SET status='returned', return_date=%s, fine=%s WHERE id=%s",
        (date.today(), fine, trans[0])
    )

    cur.execute("UPDATE books SET quantity = quantity + 1 WHERE id=%s", (book_id,))

    conn.commit()
    cur.close()
    conn.close()

    return f"Returned ✅ Fine: ₹{fine}"

# ------------------ MY BOOKS ------------------

@app.route('/my_books')
def my_books():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT books.title, transactions.issue_date, transactions.due_date,
               transactions.status, transactions.fine, transactions.book_id
        FROM transactions
        JOIN books ON transactions.book_id = books.id
        JOIN users ON transactions.user_id = users.id
        WHERE users.email=%s
        ORDER BY transactions.issue_date DESC
    """, (session['user'],))

    data = cur.fetchall()

    fixed_data = []
    for row in data:
        row = list(row)

        # 🔥 FIX: agar due_date NULL hai → safe value de
        if row[2] is None:
            row[2] = date.today()  # crash avoid

        # 🔥 fine bhi None ho sakta hai
        if row[4] is None:
            row[4] = 0

        fixed_data.append(row)

    cur.close()
    conn.close()

    return render_template(
        "my_books.html",
        my_books=fixed_data,
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

    cur.close()
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

    # -------- UPDATE --------
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        quantity = request.form.get('quantity')

        cur.execute(
            "UPDATE books SET title=%s, author=%s, quantity=%s WHERE id=%s",
            (title, author, quantity, id)
        )

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('view_books'))

    # -------- FETCH --------
    cur.execute("SELECT * FROM books WHERE id=%s", (id,))
    book = cur.fetchone()

    cur.close()
    conn.close()

    return render_template("edit_book.html", book=book)

# ------------------ RUN ------------------
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)