# Scripts

This directory contains utility scripts for development and deployment.

## Setup Scripts

- **setup.sh** - Initial project setup (installs dependencies, creates .env files)

## Development Scripts

- **consistency_check.py** - Runs linting, type checking, and formatting checks on backend code
- **init_db.py** - Initializes database with migrations
- **create_admin.py** - Creates an admin user

## Usage

### Initial Setup
```bash
bash scripts/setup.sh
```

### Check Code Consistency
```bash
python scripts/consistency_check.py
```

### Initialize Database
```bash
python scripts/init_db.py
```

### Create Admin User
```bash
python scripts/create_admin.py --email admin@example.com --password yourpassword
```
