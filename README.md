
 Library Management System (LMS)


A full-stack web-based **Library Management System** built using **Flask + PostgreSQL**, designed with real-world constraints and production-level logic.

---

 Live Demo
🌐 https://library-management-system-8brx.onrender.com

---

 Key Highlights

   Role-Based Authentication (Admin / Student)
   
   Book Issue & Return System
   
   One Active Book Per User (Real-world constraint)
   
   Auto Due Date (7 Days)
   
   Fine Calculation (₹5/day)
   
   Real-time Validation & Error Handling
   
   PostgreSQL Cloud Database (Render)
   
   Modern UI (Tailwind CSS)

---

 Tech Stack

| Layer      | Technology |
|------------|-----------|
| Frontend   | HTML, Tailwind CSS |
| Backend    | Flask (Python) |
| Database   | PostgreSQL (Render Cloud) |
| Deployment | Render |
| Tools      | VS Code, GitHub |
---

 System Architecture

User (Browser)
↓
Frontend (HTML + Tailwind)
↓
Flask Backend (Routing + Logic)
↓
PostgreSQL Database


---

  Features

  Admin
  
- Add / Edit / Delete Books
  
- View All Transactions
 
- Monitor Users
  
- Dashboard Analytics  

 Student
 
- View Books
 
- Issue Book (only 1 at a time)
   
- Return Book
 
- View Personal Records (My Books)  

---

 Business Logic (Important)

 A user can issue **only one book at a time**
 
 Book cannot be issued if quantity = 0
 
 Duplicate issue is prevented
 
 Due date = Issue Date + 7 Days
 
 Fine = ₹5 per day after due date
 
 Safe handling of NULL values (no crashes)

---

 Database Schema

 Users

 id | name | email | password | role

Books

id | title | author | quantity


Transactions

id | user_id | book_id | issue_date | due_date | return_date | status | fine



---

## 🔄 Workflow

### 📌 Issue Book
1. Check user login  
2. Check existing issued book  
3. Check book availability  
4. Insert transaction  
5. Reduce book quantity  

 📌 Return Book
1. Fetch issued record  
2. Calculate delay  
3. Calculate fine  
4. Update transaction  
5. Increase book quantity  

---

🚀 Setup Instructions

```bash
git clone https://github.com/adarshthakurwork620-web/library-management-system.git
cd library-management-system

pip install -r requirements.txt

python app.py

---

🌍 Deployment

Deployed on Render Cloud Platform using:

Gunicorn
PostgreSQL managed DB
Environment variables


Future Improvements

 Email notifications (due reminders)
 Mobile App Version
 Online Fine Payment
 Advanced Analytics Dashboard
 Multi-book issue system

Conclusion

This project demonstrates:

 backend logic
 Database management
 Real-world constraints implementation
 Full-stack development


