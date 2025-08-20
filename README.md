# 💰 Expense Split Tracker (Django + PostgreSQL)

A backend-only project to manage expense groups, split costs, and settle debts (like Splitwise).  
All interactions are via REST API, tested using Postman.

---

## ✅ Features Implemented
- Create Users
- Create Groups with base currency
- Add members to groups
- Add expenses with **Equal, Exact, and Percentage split**
- Track balances per group
- Allow settlements between users
- Simplify debts (reduce redundant transactions)
- Audit trail for expenses & settlements
- Ready-to-import **Postman Collection** for testing

---

## ⚙️ Tech Stack
- Python 3.12
- Django 5
- Django REST Framework
- PostgreSQL 15

---

## 📂 Setup Instructions

### 1. Clone repo & setup virtual environment
```bash
git clone <your-repo-url>
cd expense-tracker
python -m venv .venv
.venv\Scripts\activate   # (Windows)
```
### 2. Install Dependencies
```bash
pip install -r requirements.txt
```
### 3. Configure PostgreSQL

Inside ```psql```:
```sql
CREATE DATABASE expenseDB;
CREATE USER expense_user WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE expenseDB TO expense_user;
```
### 4. Update .env
```env
DB_NAME=expenseDB
DB_USER=expense_user
DB_PASS=password
DB_HOST=localhost
DB_PORT=5432
```

### 5. Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```
### 6. Start server
```bash
python manage.py runserver
```

## 📬 API Endpoints
Base URL: ```http://127.0.0.1:8000/api/v1/```
- ###  Users
  -  ``` POST /users``` → Create user
  -  ```GET /users``` → List users
- ### Groups
  - ```POST /groups``` → Create group
  - ```POST /groups/{id}/members``` → Add member
 
- ### Expenses
  - ```POST /groups/{id}/expenses``` → Add expense (equal/exact/percentage)
- ### Balances
  - ```GET /groups/{id}/balances``` → View balances

- ### Settlements
  - ```POST /groups/{id}/settlements``` → Create settlement

- ### Simplify
  - ```POST /groups/{id}/simplify``` → Simplify debts
 
## 🧪 Testing with Postman
1. Import the provided collection:
👉 ```postman_collection.json```

2. Run APIs step by step:
     - Create users
     - Create a group
     - Add members
     - Add expenses
     - Check balances
     - Settle debts
     - Simplify debts
