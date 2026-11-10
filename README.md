# Personalized Medical Assistant (PMA)

PMA is a Django web application for patient and doctor management, appointments,
medical records, messaging, health metrics, and machine-learning disease
predictions.

> **Medical disclaimer:** This project is for educational and informational
> purposes. It is not a substitute for professional medical advice, diagnosis,
> or treatment.

## Features

### Patients

- Register and manage a patient profile
- Calculate BMI and track health information
- Browse doctors and book appointments
- Upload and view medical records
- Create medicine reminders
- Submit symptoms for disease prediction
- View prediction results and recommendations
- Message doctors

### Doctors

- Create a professional profile
- Configure consultation availability
- View and manage appointments
- Review patient records
- Communicate with patients

### Machine learning

- Symptom analysis and disease prediction
- Decision Tree, Random Forest, enhanced, and custom prediction engines
- Medicine, diet, and food-avoidance recommendations
- Excel dataset support through `ml_prediction/data/Disease.xlsx`

## Project structure

The repository contains one Django project. The `config` directory is the
Django configuration package; the application directories contain the product
features.

```text
PMA/
├── personalized_medicine_assistant/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── db.sqlite3                         # Local fallback database
│   ├── config/                            # Django configuration package
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   ├── patients/                          # Patient application
│   ├── doctors/                            # Doctor application
│   ├── ml_prediction/                      # Prediction engines and datasets
│   ├── templates/                          # HTML templates
│   ├── static/                             # CSS and image assets
│   ├── media/                              # Uploaded medical records
│   └── tests/                              # Integration and API tests
├── .vscode/                                # Local development tasks
├── database/
└── docs/
```

## Technology stack

- Python 3.13 or newer
- Django 5.2.6
- PostgreSQL with `psycopg`
- SQLite as an explicit local fallback
- pandas, NumPy, SciPy, scikit-learn, and joblib
- Pillow and openpyxl
- Django templates, Tailwind CSS CDN, and Boxicons CDN

Exact dependency versions are listed in
[`personalized_medicine_assistant/requirements.txt`](personalized_medicine_assistant/requirements.txt).

## Requirements

- Python 3.13 or newer
- pip
- PostgreSQL
- Git (optional)

## Installation

From the repository root, create and activate a virtual environment:

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Windows Command Prompt

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

Install the dependencies:

```powershell
cd personalized_medicine_assistant
python -m pip install -r requirements.txt
```

## PostgreSQL configuration

The application is configured to use PostgreSQL by default. Copy the example
environment file and update it with your local credentials:

```powershell
Copy-Item .env.example .env
```

The expected settings are:

```text
DB_ENGINE=django.db.backends.postgresql
DB_NAME=pma_db
DB_USER=postgres
DB_PASSWORD=<your-postgresql-password>
DB_HOST=localhost
DB_PORT=5432
```

Create the `pma_db` database in PostgreSQL if it does not already
exist. Do not commit `.env` or real credentials.

Check the database connection and apply migrations:

```powershell
python manage.py check
python manage.py migrate
```

Create an administrator when needed:

```powershell
python manage.py createsuperuser
```

## Run the application

Start the development server from the
`personalized_medicine_assistant` directory:

```powershell
python manage.py runserver
```

Or, on Windows, run:

```bat
run_server.bat
```

Open:

- Application: <http://127.0.0.1:8000/>
- Admin: <http://127.0.0.1:8000/admin/>

The server uses PostgreSQL when `DB_ENGINE=django.db.backends.postgresql`. To explicitly use the preserved
SQLite database for local fallback testing, set `USE_MYSQL=False` before
starting Django:

```powershell
$env:DB_ENGINE = "django.db.backends.sqlite3"
python manage.py runserver
```

## Testing

Run the complete test suite:

```powershell
python manage.py test
```

Run tests for a specific application:

```powershell
python manage.py test patients
python manage.py test doctors
python manage.py test ml_prediction
```

Run Django's configuration check:

```powershell
python manage.py check
```

## Static files and media

In development, Django serves static files from:

```text
personalized_medicine_assistant/static/
```

Uploaded medical records are stored in:

```text
personalized_medicine_assistant/media/
```

For production, collect static files and serve them through a web server:

```powershell
python manage.py collectstatic
```

## Database settings

The database configuration is defined in
[`config/settings.py`](personalized_medicine_assistant/config/settings.py).

PostgreSQL is selected when:

```text
DB_ENGINE=django.db.backends.postgresql
```

SQLite is selected only when:

```text
DB_ENGINE=django.db.backends.sqlite3
```

The SQLite fallback database is
`personalized_medicine_assistant/db.sqlite3`.

## Important security settings

Before production deployment:

1. Set a strong, private `SECRET_KEY`.
2. Set `DEBUG=False`.
3. Configure `ALLOWED_HOSTS` for the deployment domain.
4. Use HTTPS.
5. Keep database passwords and `.env` files out of source control.
6. Configure secure media storage and upload validation.
7. Back up the PostgreSQL database and uploaded media.

## Application URLs

- `/` - Home page
- `/login/` - Login
- `/register/` - Registration
- `/logout/` - Logout
- `/patients/` - Patient features
- `/doctors/` - Doctor features
- `/predict/` - Disease prediction
- `/admin/` - Django administration

## Development notes

- Run commands from `personalized_medicine_assistant/`.
- `manage.py` is the only Django command entry point.
- `config/` contains configuration only; feature logic belongs in the
  `patients/`, `doctors/`, and `ml_prediction/` applications.
- Empty `__init__.py` files are intentional Python package markers.
- Generated `__pycache__` and `.pyc` files are ignored by Git.
