#!/bin/bash
# Snow Deep DB Deployment Script for AWS EC2
# Usage: ./deploy.sh [environment]
# Environment: development, staging, production (default: production)

set -e  # Exit on any error

# Configuration
PROJECT_DIR="/home/ec2-user/snow_deep"
VENV_DIR="/home/ec2-user/snow_deep_env"
ENVIRONMENT=${1:-production}
SERVICE_NAME="snow-deep"

echo "=========================================="
echo "Snow Deep DB Deployment Script"
echo "Environment: $ENVIRONMENT"
echo "Project Directory: $PROJECT_DIR"
echo "=========================================="

# Function to print colored output
print_status() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

# Check if we're in the correct directory
if [ ! -f "manage.py" ]; then
    print_error "manage.py not found. Please run this script from the project root directory."
    exit 1
fi

# Backup current deployment (if exists)
if [ -d "$PROJECT_DIR" ]; then
    print_status "Creating backup of current deployment..."
    sudo cp -r $PROJECT_DIR ${PROJECT_DIR}_backup_$(date +%Y%m%d_%H%M%S) || true
fi

# Update code from Git
print_status "Updating code from Git repository..."
git fetch origin
git reset --hard origin/main
git clean -fd

# Set up virtual environment
print_status "Setting up Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv $VENV_DIR
fi

source $VENV_DIR/bin/activate

# Install/update dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements_production.txt

# Load environment variables
if [ -f ".env" ]; then
    print_status "Loading environment variables..."
    export $(grep -v '^#' .env | xargs)
else
    print_error "Environment file .env not found!"
    exit 1
fi

# Set Django settings module
export DJANGO_SETTINGS_MODULE="snow_predict.settings_production"

# Database operations
print_status "Running database migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Setup initial data (ski resorts)
print_status "Setting up initial ski resort data..."
python manage.py setup_resorts

# Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create log directories
print_status "Creating log directories..."
sudo mkdir -p /var/log/django
sudo mkdir -p /var/log/gunicorn
sudo mkdir -p /var/run/gunicorn
sudo chown ec2-user:ec2-user /var/log/django
sudo chown ec2-user:ec2-user /var/log/gunicorn
sudo chown ec2-user:ec2-user /var/run/gunicorn

# Set file permissions
print_status "Setting file permissions..."
sudo chown -R ec2-user:ec2-user $PROJECT_DIR
sudo chmod +x deploy.sh

# Test Django application
print_status "Testing Django application..."
python manage.py check --deploy

# Restart services
print_status "Restarting application services..."
sudo systemctl daemon-reload
sudo systemctl restart $SERVICE_NAME
sudo systemctl restart nginx

# Wait for service to start
sleep 5

# Check service status
print_status "Checking service status..."
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    print_success "Service $SERVICE_NAME is running"
else
    print_error "Service $SERVICE_NAME failed to start"
    sudo systemctl status $SERVICE_NAME
    exit 1
fi

if sudo systemctl is-active --quiet nginx; then
    print_success "Nginx is running"
else
    print_error "Nginx failed to start"
    sudo systemctl status nginx
    exit 1
fi

# Health check
print_status "Performing health check..."
if curl -f -s http://localhost/health/ > /dev/null; then
    print_success "Health check passed"
else
    print_error "Health check failed"
    exit 1
fi

# Cleanup old backups (keep last 3)
print_status "Cleaning up old backups..."
ls -dt ${PROJECT_DIR}_backup_* 2>/dev/null | tail -n +4 | xargs sudo rm -rf 2>/dev/null || true

print_success "=========================================="
print_success "Deployment completed successfully!"
print_success "Environment: $ENVIRONMENT"
print_success "Timestamp: $(date)"
print_success "=========================================="

# Display service URLs
echo ""
echo "Service URLs:"
echo "  Health Check: http://localhost/health/"
echo "  Admin Panel:  http://localhost/admin/"
echo "  Application:  http://localhost/"
echo ""

# Deactivate virtual environment
deactivate

