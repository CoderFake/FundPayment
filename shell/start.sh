#!/bin/sh

echo "Installing Gunicorn..."
pip install gunicorn==23.0.0 pytz==2025.1

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

echo "Setting timezone to Asia/Ho_Chi_Minh"
echo "TZ=Asia/Ho_Chi_Minh" > /etc/environment
ln -sf /usr/share/zoneinfo/Asia/Ho_Chi_Minh /etc/localtime
echo "Asia/Ho_Chi_Minh" > /etc/timezone

mkdir -p /home/FundPayment/payment/cron_job
touch /home/FundPayment/payment/cron_job/log.log
chmod 666 /home/FundPayment/payment/cron_job/log.log

service cron stop
service cron start
crontab -r || true
python manage.py crontab add
python manage.py crontab show

echo "Starting Gunicorn server..."
gunicorn FundPayment.wsgi:application \
    --workers 3 \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --log-level debug \
    --access-logfile - \
    --error-logfile - \
    --capture-output