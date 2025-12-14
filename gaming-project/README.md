# Gaming Analytics Project

A Django-based gaming analytics platform with user authentication and a modern dashboard UI.

## Features

- User authentication (signup, login, logout)
- Modern dashboard with Volt UI kit
- Profile management
- Responsive design
- Ready for gaming analytics features

## Setup

1. Create a virtual environment:

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On macOS/Linux
    ```

2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Create `.env` file from example and update your credentials:

    ```bash
    cp .env.example .env
    # Edit .env and set your MySQL password: DB_PASSWORD=your_password
    ```

4. Set up MySQL database:

    ```bash
    # Log into MySQL
    mysql -u root -p
    
    # Create database
    CREATE DATABASE gaming_analytics CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    EXIT;
    ```

5. Run migrations:

    ```bash
    python manage.py migrate
    ```

6. Create a superuser:

    ```bash
    python manage.py createsuperuser
    ```

7. Run the development server:

    ```bash
    python manage.py runserver
    ```

8. Visit <http://localhost:8000>

## Project Structure

- `gaming_project/` - Main project settings
- `accounts/` - User authentication app
- `dashboard/` - Dashboard and main views
- `templates/` - HTML templates
- `static/` - CSS, JavaScript, and images
- `media/` - User uploaded files

## Technologies

- Django 6.0
- django-allauth (authentication)
- Volt UI Kit (Bootstrap 5 based theme)
- Font Awesome icons
- WhiteNoise (static file serving)
