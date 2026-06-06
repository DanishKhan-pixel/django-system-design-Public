# Django Blog Backend

A clean, regular Django REST Framework blog backend. This baseline focuses on functional API features and beginner-friendly structure so it can later be extended in system design lessons.

## Features


- Custom user model with unique email addresses
- Signup, JWT login, token refresh, and authenticated profile endpoints
- Blog posts with draft/published status, slugs, category, tags, local cover image upload, and timestamps
- Public published-post listing and detail endpoints
- Authenticated owner post create, update, delete, and my-posts listing
- Public category and tag list endpoints
- Comments on published posts with owner-only update/delete
- Post likes with duplicate prevention and toggle behavior
- Post bookmarks with duplicate prevention and a personal bookmark list
- Frontend-friendly post responses with author, category, tags, like count, comment count, `is_liked`, and `is_bookmarked`

Detailed endpoint documentation lives in [clint_api_docs.md](clint_api_docs.md).

## Local Setup

Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Database

The project uses PostgreSQL for local development. Connection settings live in the ignored `.env` file:

```env
DB_NAME=django_blog_db
DB_USER=django_blog_user
DB_PASSWORD=your-local-password
DB_HOST=localhost
DB_PORT=5432
```

Apply migrations:

```powershell
python manage.py migrate
```

Create an admin user:

```powershell
python manage.py createsuperuser
```

The old `db.sqlite3` file is not used by Django after this switch and can stay in the project directory as a local backup.

## Run Locally

Start the development server:

```powershell
python manage.py runserver
```

Useful local URLs:

- Admin: `http://127.0.0.1:8000/admin/`
- API root prefix: `http://127.0.0.1:8000/api/`
- Auth prefix: `http://127.0.0.1:8000/api/auth/`

Uploaded post cover images are stored locally under `media/post_covers/` and served from `MEDIA_URL` while `DEBUG=True`.

## Testing

Run the full test suite:

```powershell
python manage.py test
```

Run Django's project check:

```powershell
python manage.py check
```

Check for pending model changes before creating migrations:

```powershell
python manage.py makemigrations --check --dry-run
```

## Baseline Scope

This project intentionally does not include Redis, Celery, rate limiting, CDN, cloud storage, load balancing, Docker, deployment architecture, or external search services at this stage.
