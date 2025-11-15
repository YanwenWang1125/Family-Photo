#!/bin/bash
# Initial setup script for development environment

set -e

echo "==========================="
echo "Family Photo Hub Setup"
echo "==========================="

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js is required but not installed."; exit 1; }

# Backend setup
echo ""
echo "Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate || source venv/Scripts/activate
pip install -e ".[dev]"
cd ..

# Frontend setup
echo ""
echo "Setting up frontend..."
cd frontend
npm install
cd ..

# Copy environment files
echo ""
echo "Creating environment files..."
if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "Created backend/.env - Please configure it!"
fi

if [ ! -f frontend/.env.local ]; then
    cp frontend/.env.local.example frontend/.env.local
    echo "Created frontend/.env.local - Please configure it!"
fi

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env - Please configure it!"
fi

echo ""
echo "==========================="
echo "Setup complete!"
echo "==========================="
echo ""
echo "Next steps:"
echo "1. Configure environment variables in:"
echo "   - backend/.env"
echo "   - frontend/.env.local"
echo "   - .env"
echo ""
echo "2. Start PostgreSQL (or use docker-compose)"
echo "3. Run database migrations:"
echo "   cd backend && alembic upgrade head"
echo ""
echo "4. Start development servers:"
echo "   make dev-up"
echo ""
