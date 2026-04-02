# 📚 BookNest - Advanced Library Management System

## 🔍 Overview
BookNest is a web-based Library Management System built using Flask and MongoDB.  
It allows users to register, search books, request books, and return them.  
Admins can manage books, users, and approve/reject requests efficiently.

---

## 🚀 Key Features

### 👤 User Features
- User Registration & Login
- Search books by title or author
- Request books for issue
- Request return of books
- Cancel book requests
- View issued books
- Track request status (pending / approved / rejected)

---

### 🛠️ Admin Features
- Admin login system
- View all users and books
- Search users and books
- Add new books
- Update book stock (increase/decrease)
- Delete books
- Delete users (with username confirmation for safety)
- Approve or reject book issue/return requests

---

## 🔄 Request Management System
- Users send **issue/return requests**
- Admin reviews requests
- System updates:
  - Stock automatically increases/decreases
  - Book assigned or removed from user
  - Request status updated

---

## 🧑‍💻 Technologies Used
- Python (Flask Framework)
- MongoDB (Database)
- PyMongo
- HTML, CSS
- Jinja2 (Template Engine)

---

## 📂 Project Structure
