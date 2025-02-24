#!/bin/sh

echo "Installing Gunicorn..."
pip install gunicorn==23.0.0

echo "Running migrations..."
python manage.py makemigrations
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput --no-post-process

echo "Setting permissions for static files..."
chown -R www-data:www-data /home/FundPayment/staticfiles

echo "Creating superuser and site..."
python create_superuser_and_site.py

echo "Creating users ..."
python manage.py shell < import_data.py

echo "Setting up cron jobs..."
service cron start
python manage.py crontab remove
python manage.py crontab add
python manage.py crontab show

echo "Starting Gunicorn server..."
gunicorn FundPayment.wsgi:application --workers 3 --bind 0.0.0.0:8000