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

## WeasyPrint System Dependencies

The KYC module uses WeasyPrint for PDF generation, which requires system-level dependencies. If WeasyPrint fails to import, the system will automatically fall back to ReportLab.

### Ubuntu/Debian Installation

For Ubuntu 18.04+ or Debian 10+:
```bash
sudo apt-get update
sudo apt-get install build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

For newer versions (Ubuntu 20.04+):
```bash
sudo apt install python3-pip libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0
```

### CentOS/RHEL/Fedora Installation

```bash
sudo yum install gcc python3-devel python3-pip python3-cffi libffi-devel cairo-devel pango-devel gdk-pixbuf2-devel
```

### Alpine Linux Installation

```bash
apk add py3-pip gcc musl-dev python3-dev pango libffi-dev cairo-dev
```

### macOS Installation

Using Homebrew:
```bash
brew install python3 cairo pango gdk-pixbuf libffi
```

Using MacPorts:
```bash
sudo port install py-pip pango libffi
```

### Windows Installation

WeasyPrint on Windows requires GTK+ libraries. The easiest approach is to use conda:
```bash
conda install -c conda-forge weasyprint
```

Alternatively, install GTK+ manually and ensure it's in your PATH.

### Fallback Solution

If WeasyPrint cannot be installed due to system dependency issues, the application will automatically use ReportLab for PDF generation. ReportLab is already included in the project requirements and provides basic PDF functionality without requiring system dependencies.

### Troubleshooting

- **libpango error**: Install the libpango-1.0-0 package for your system
- **libcairo error**: Install cairo development libraries
- **libffi error**: Install libffi development packages
- **Permission errors**: Use virtual environments and avoid system-wide installations

For production deployments, consider using Docker with pre-installed system dependencies or cloud platforms that support WeasyPrint.

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