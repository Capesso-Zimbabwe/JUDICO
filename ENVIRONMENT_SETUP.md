# Environment Variables Setup

This project uses `python-decouple` to manage environment variables for better security and configuration management.

## Setup Instructions

1. **Install python-decouple** (already included in requirements.txt):
   ```bash
   pip install python-decouple==3.8
   ```

2. **Create your .env file**:
   Copy the `.env.example` file to `.env` and update the values:
   ```bash
   cp .env.example .env
   ```

3. **Configure your environment variables**:
   Edit the `.env` file with your actual values:
   ```env
   SECRET_KEY=your-actual-secret-key-here
   DEBUG=True
   DB_NAME=your_actual_database_name
   DB_USER=your_actual_database_user
   DB_PASSWORD=your_actual_database_password
   ```

## Environment Variables

### Required Variables
- `SECRET_KEY`: Django secret key for cryptographic signing
- `DB_NAME`: Database name
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password

### Optional Variables (with defaults)
- `DEBUG`: Debug mode (default: False)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts (default: empty)
- `DB_ENGINE`: Database engine (default: django.db.backends.postgresql)
- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 5432)
- `NPM_BIN_PATH`: Path to npm binary (default: C:/Program Files/nodejs/npm.cmd)
- `PAGINATE_BY`: Default pagination count (default: 10)
- `LOGIN_URL`: Login URL (default: /auth/login/)
- `LOGIN_REDIRECT_URL`: Post-login redirect (default: /)
- `LOGOUT_REDIRECT_URL`: Post-logout redirect (default: /auth/login/)
- `LANGUAGE_CODE`: Language code (default: en-us)
- `TIME_ZONE`: Time zone (default: UTC)

## Security Notes

- The `.env` file is already included in `.gitignore` to prevent committing sensitive data
- Never commit your actual `.env` file to version control
- Use `.env.example` as a template for other developers
- In production, set environment variables through your hosting platform's configuration

## Usage in Code

The `decouple` library is used in `settings.py` like this:
```python
from decouple import config, Csv

# String values
SECRET_KEY = config('SECRET_KEY')

# Boolean values
DEBUG = config('DEBUG', default=False, cast=bool)

# Integer values
PAGINATE_BY = config('PAGINATE_BY', default=10, cast=int)

# CSV values (for lists)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=Csv())
```