# Theatre API

RESTful API service for managing theatre repertoire, halls, performances, and ticket reservations, built with Django REST Framework.

## Features

* **Custom User & JWT Authentication:** Email-based user registration and authentication powered by `djangorestframework-simplejwt`.
* **Role-Based Access Control:** Custom `IsAdminOrIfAuthenticatedReadOnly` permission — administrators manage plays, actors, genres, halls, and performances, while authenticated users browse the schedule and book tickets.
* **Play Poster Uploads:** Dedicated endpoint (`/api/theatre/plays/<id>/upload-image/`) for uploading and storing play posters with UUID-based filenames.
* **Advanced Filtering:** Filter plays by `title`, `genres`, and `actors`, and filter performances by `date` and `play`.
* **Real-Time Seat Availability:** Dynamic calculation of `tickets_available` in the performance list and `taken_places` in the performance detail view.
* **Atomic Ticket Booking:** Nested creation of reservations and tickets wrapped in `transaction.atomic()` with validation for hall row/seat boundaries and duplicate bookings.
* **Interactive API Documentation:** Auto-generated OpenAPI 3.0 schema available via Swagger UI and ReDoc.
* **Containerized Environment:** Ready-to-run `Dockerfile` and `docker-compose.yml` with PostgreSQL and database readiness check (`wait_for_db`).

## Database Architecture

The project uses a relational schema connecting `User`, `Play`, `Genre`, `Actor`, `TheatreHall`, `Performance`, `Reservation`, and `Ticket` (including custom `User` email authentication and poster `image` storage on `Play`).

## Local Setup (without Docker)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/AndrewGalynin/theatre-api.git
   cd theatre-api
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Copy `.env.sample` to `.env` and set your `SECRET_KEY` (leave `POSTGRES_HOST=` empty to use local SQLite):
   ```bash
   cp .env.sample .env
   ```

5. **Apply migrations, create a superuser, and load sample data:**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py loaddata sample_theatre_db_data.json
   ```

6. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

## Running with Docker

1. **Configure environment variables:**
   Copy `.env.sample` to `.env` and fill in the database credentials and `SECRET_KEY`:
   ```bash
   cp .env.sample .env
   ```

2. **Build and start containers:**
   ```bash
   docker-compose up --build
   ```

3. **Create a superuser and load sample data inside the container:**
   ```bash
   docker-compose exec app python manage.py createsuperuser
   docker-compose exec app python manage.py loaddata sample_theatre_db_data.json
   ```

## Getting Access & Key Endpoints

1. **Register a new user:** `POST /api/user/register/` with `{"email": "user@example.com", "password": "yourpassword"}`.
2. **Obtain JWT tokens:** `POST /api/user/token/` with your credentials to receive `access` and `refresh` tokens.
3. **Authorize requests:** Pass the header `Authorization: Bearer <your_access_token>` (or log in via the Browsable API / Swagger UI).

* **Swagger UI:** `/api/doc/swagger/`
* **ReDoc:** `/api/doc/redoc/`
* **User Profile:** `/api/user/me/`
* **Plays:** `/api/theatre/plays/`
* **Performances:** `/api/theatre/performances/`
* **Reservations:** `/api/theatre/reservations/`
* **Theatre Halls:** `/api/theatre/theatre-halls/`
* **Genres & Actors:** `/api/theatre/genres/`, `/api/theatre/actors/`