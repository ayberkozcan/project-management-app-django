# Project Management App

A collaborative Django application for managing projects, groups, members, comments, and tasks in one place.

It started as a CRUD-style project, but now includes role-based authorization, activity tracking, rate limiting, automated tests, CI, and Docker-based local infrastructure with PostgreSQL and Redis.

## Preview

### Dashboard
<img width="1858" height="946" alt="dashboard" src="https://github.com/user-attachments/assets/1fff2f47-028f-4bca-908b-feb1395960bb" />

### Project Details
<img width="1840" height="952" alt="project_detail" src="https://github.com/user-attachments/assets/73a3c5bf-cb56-4f4f-8098-3d74c74e6270" />

### Group Details
<img width="1832" height="949" alt="group_detail" src="https://github.com/user-attachments/assets/03e1a27b-d7c8-4c73-9dce-ed3a8ba44165" />

## Features

- User authentication with signup, login, and profile management
- Project, group, member, and task management
- Role-based permissions for owners, admins, and regular members
- Project and group comments
- Activity log tracking for key actions
- Rate limiting for authentication, list, and mutation endpoints
- Automated tests for deletion cascades, authorization, and throttling
- Dockerized setup with PostgreSQL, Redis, and Gunicorn
- GitHub Actions CI pipeline for checks and tests

## Authorization Rules

- Only the project owner can edit or delete a project
- Project owners and project admins can manage project members and tasks
- Only project owners and admins can delete project comments
- Only the group owner can edit or delete a group
- Group owners and group admins can invite or remove group members
- Users who are not assigned to a project or group cannot access related protected pages

## Tech Stack

- Python
- Django
- Django REST Framework
- PostgreSQL
- Redis
- Gunicorn
- Docker
- GitHub Actions

## CI

The project includes a GitHub Actions workflow that runs on `push` and `pull_request`.

It currently performs:

- Ruff checks for critical Python errors
- Django migration consistency check
- Python compile check
- `python manage.py check`
- Automated test suite

## Docker Setup

The project is configured to run with:

- `web` service for Django + Gunicorn
- `db` service for PostgreSQL
- `redis` service for caching and rate limiting

### 1. Clone the repository

```bash
git clone https://github.com/ayberkozcan/project-management-app-django.git
cd project-management-app-django
```

### 2. Create a local environment file

```bash
cp .env.example .env
```

### 3. Run with Docker

```bash
docker compose up --build
```

The app will be available at:

```bash
http://localhost:8000
```

## Environment Variables

Create a local `.env` file based on `.env.example`.

Main variables:

```env
DJANGO_SECRET_KEY=change-me-in-production
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

DB_ENGINE=postgres
POSTGRES_DB=project_management
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432

REDIS_URL=redis://redis:6379/1
```

## Local Development Without Docker

### 1. Clone the repository

```bash
git clone https://github.com/ayberkozcan/project-management-app-django.git
cd project-management-app-django
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

macOS / Linux:

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. Create a superuser

```bash
python manage.py createsuperuser
```

### 6. Run the server

```bash
python manage.py runserver
```

## Testing

Run the current automated test suite with:

```bash
python manage.py test accounts.tests projects.tests groups.tests
```

## Project Highlights

This project demonstrates more than basic CRUD:

- relational modeling across multiple Django apps
- role-based access control
- defensive deletion and cascade validation
- request throttling
- containerized development workflow
- CI-based quality checks

## Possible Future Improvements

- background jobs with Celery
- email notifications
- attachment uploads for tasks
- staging/production deployment pipeline
- better dashboards and analytics
- live demo deployment

## Third-Party Resources

- Bootstrap
- Bootstrap Icons
- Google Fonts - Plus Jakarta Sans

## License

MIT License
