# BNP Django REST API

A Django REST API project for document OCR, face recognition, and restricted list checking using AWS services.

## Features

- OCR document processing using AWS Textract
- Face comparison and recognition using AWS Rekognition
- Restricted list checking with fuzzy matching
- PostgreSQL database support
- RESTful API endpoints

## Requirements

- Python 3.8+
- PostgreSQL 12+
- AWS Account with Rekognition and S3 access

## Setup Instructions

### 1. Environment Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd bnp-main
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 2. Database Setup (PostgreSQL)

1. Install PostgreSQL and create a database:
   ```sql
   CREATE DATABASE bnp;
   CREATE USER your_db_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE bnp TO your_db_user;
   ```

### 3. Environment Configuration

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Update `.env` file with your actual values:
   - Database credentials
   - AWS credentials
   - Secret key (generate a new one for production)

### 4. Django Setup

1. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. Create superuser:
   ```bash
   python manage.py createsuperuser
   ```

3. Collect static files:
   ```bash
   python manage.py collectstatic
   ```

### 5. AWS Configuration

1. Set up AWS S3 buckets:
   - Main bucket for file storage
   - Face bucket for face recognition
   - Image bucket for image processing

2. Configure AWS IAM with necessary permissions:
   - S3 read/write access
   - Rekognition access
   - Textract access

## API Endpoints

- `/lists/` - POST - Restricted list checking
- `/ocr/` - POST - OCR document processing
- `/face/` - POST - Face comparison
- `/login/` - POST - User authentication
- `/admin/` - Django admin interface

## Deployment

### Development
```bash
python manage.py runserver
```

### Production
```bash
gunicorn apibase.wsgi:application
```

## Migration from MySQL to PostgreSQL

If migrating from an existing MySQL database:

1. Export data from MySQL:
   ```bash
   python manage.py dumpdata > data.json
   ```

2. Update database settings in `.env`

3. Run migrations:
   ```bash
   python manage.py migrate
   ```

4. Load data:
   ```bash
   python manage.py loaddata data.json
   ```

## Security Notes

- Never commit `.env` file to version control
- Use strong passwords for database and secret keys
- Rotate AWS credentials regularly
- Enable HTTPS in production
- Update allowed hosts for production domains

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Debug mode | `False` |
| `SECRET_KEY` | Django secret key | Required |
| `DB_NAME` | Database name | `bnp` |
| `DB_USER` | Database user | `postgres` |
| `DB_PASSWORD` | Database password | Required |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `AWS_ACCESS_KEY_ID` | AWS access key | Required |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Required |
| `AWS_DEFAULT_REGION` | AWS region | `us-east-1` |
| `ALLOWED_HOSTS` | Comma-separated hosts | `localhost` |

## Support

For deployment issues or questions, check the Django documentation or AWS service documentation.
