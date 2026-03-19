# Project Management App - Django

A simple and efficient web application for managing projects and tasks. Built with Django and Django REST Framework, it allows users to create accounts, organize groups/teams, manage projects, assign and track tasks.

Great for learning full Django development: authentication, models & relations, CRUD operations, templates + API endpoints.

## Features

- **User Authentication** — Register, login, profile management (via `accounts` app)
- **Groups / Teams** — Create and manage teams for collaboration (`groups` app)
- **Projects** — Create projects, set details, statuses (`projects` app)
- **Tasks** — Add tasks to projects, assign to users, track progress & deadlines (`tasks` app)
- **REST API** — Built with Django REST Framework (DRF) for programmatic access
- **Responsive Templates** — Basic HTML templates for web interface
- Clean & modular structure following Django best practices

## Tech Stack

- **Backend**: Python, Django
- **API**: Django REST Framework
- **Database**: SQLite (for development)

## Installation & Setup

### Prerequisites
- Python 3.10+
- pip
- PostgreSQL (optional but recommended)

### Steps

1. Clone the repository
   ```bash
   git clone https://github.com/ayberkozcan/project-management-app-django.git
   cd project-management-app-django

2. Create and activate virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   
3. Install dependencies
   ```bash
   pip install -r requirements.txt
   
4. Apply migrations & create superuser
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser

5. Run the development server
   ```bash
   python manage.py runserver

Open http://127.0.0.1:8000/ in your browser.

Admin panel: http://127.0.0.1:8000/admin/

## Roadmap / Future Improvements

This project is primarily **backend-focused**, emphasizing clean Django architecture, modular apps, RESTful APIs (via DRF), and scalable patterns.

Planned features and enhancements (in progress or upcoming):

- **Activity Log** — Track project/task changes, user actions, and history (e.g., who created/updated what, timestamps)
- **Comments System** — Allow users to add threaded comments on tasks or projects for better collaboration
- **User Profile** — Detailed profiles with bio, avatar, assigned tasks overview, and activity summary
- **Docker Containerization** — Add Dockerfile and docker-compose.yml for easy local/dev setup (PostgreSQL + Redis-ready for future Celery)
- **Celery + Redis Integration** — Background tasks (e.g., email notifications, deadline reminders, retry logic)
- **CI/CD Pipeline** — Basic GitHub Actions workflow for tests, linting, and Docker build
- **Task Priorities & Attachments** — Add priority levels, due date reminders, file uploads

## License
MIT License – feel free to use for learning or personal projects.
