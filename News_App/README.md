# News App
## Overview
News App is a Django-based news publishing platform that supports three different user roles:
* Readers
* Journalists
* Editors
The platform allows journalists to create articles and newsletters, editors to approve and manage content, and readers to subscribe to publishers and journalists.
Django REST Framework included.
---
# Features
## Authentication System
* Custom user model
* User registration and login
* Role-based access control
* Logout functionality
## Reader Features
* View approved articles
* View newsletters
* Subscribe to publishers
* Subscribe to journalists
* Manage subscriptions
## Journalist Features
* Create articles
* Update articles
* Delete articles
* Create newsletters
* Update newsletters
* Delete newsletters
* Create publishers
## Editor Features
* Approve articles
* Edit articles
* Delete articles
* Edit newsletters
* Delete newsletters
## API Features
* Token authentication
* Article API endpoints
* Newsletter API endpoints
* Approval API endpoints
* Subscription-based article filtering
---
# Permissions System
The application uses:
* Django Groups
* Custom Permissions
* Role-based access control
* Django authentication mixins
Custom permissions include:
* can_view_article
* can_create_article
* can_update_article
* can_delete_article
* can_view_newsletter
* can_create_newsletter
* can_update_newsletter
* can_delete_newsletter
---
# Technologies Used
* Python
* Django
* Django REST Framework
* MariaDB
* PyMySQL
* HTML
* CSS
---
# Installation
## 1. Clone the Repository
```bash
git clone <your-repository-url>
```
## 2. Enter the Project Folder
```bash
cd News_App
```
## 3. Create a Virtual Environment
### Windows
```bash
py -m venv venv
```
## 4. Activate the Virtual Environment
### Windows
```bash
venv\Scripts\activate
```
---
# Install Dependencies
Install all required packages:
```bash
pip install -r requirements.txt
```
---
# Database Setup

This project uses MariaDB. Make sure MariaDB is installed and running before continuing.

## Start the MariaDB Shell

### Windows
Navigate to your MariaDB bin folder and open the shell as root:
```bash
cd "C:\Program Files\MariaDB 12.2\bin"
.\mysql -u root -p
```

## Create the Database and User

Run the following commands inside the MariaDB shell:
```sql
CREATE DATABASE news_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'news_app_user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON news_db.* TO 'news_app_user'@'localhost';
FLUSH PRIVILEGES;
```

## Apply Migrations
```bash
cd News_App
py manage.py migrate
```
---
# Create Superuser
Create an admin account:
```bash
py manage.py createsuperuser
```
---
# Run the Development Server
```bash
py manage.py runserver
```
Open the application in your browser:
```text
http://127.0.0.1:8000/
```
---
# Admin Panel
Access the Django admin panel:
```text
http://127.0.0.1:8000/admin/
```
---
# API Endpoints
## Authentication
### Login
```text
/api/login/
```
### Logout
```text
/api/logout/
```
### Token
```text
/api/token/
```
---
## Article Endpoints
### Get All Articles
```text
/api/articles/
```
### Get Single Article
```text
/api/articles/<id>/
```
### Approve Article
```text
/api/articles/<id>/approve/
```
### Get Subscribed Articles
```text
/api/articles/subscribed/
```
---
# Project Structure
```text
News_App/
│
├── News_App/
├── NewsApp/
│   ├── migrations/
│   ├── templates/
│   ├── static/
│   ├── models.py
│   ├── views.py
│   ├── tests.py
│   ├── forms.py
│   ├── serializers.py
│   ├── urls.py
│   └── admin.py
│
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```
---
# Sphinx
* Find Sphinx Html page at
```text
docs/build/html/index.html
```
---
# Docker Setup
### Run with Docker Compose
Make sure Docker Desktop is installed and running.
* Clone the repository:
* Build and start the containers:
```bash
docker compose up --build
```
* The application will be available at:
http://127.0.0.1:8000
* Stop the containers:
```bash
docker compose down
```
* The project image is available on Docker Hub:
```bash
docker pull joshjb27/newsapp
```
Run the image directly:
```bash
docker run -p 8000:8000 joshjb27/newsapp
```
Then open:
http://127.0.0.1:8000
---
# Author
Joshua Busby
