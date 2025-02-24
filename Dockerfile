FROM python:3.12

# Create directory
RUN mkdir -p /home/FundPayment

# Set work directory
WORKDIR /home/FundPayment

# Install cron and dependencies
RUN apt-get update && apt-get install -y cron

# Install dependencies
ADD requirements.txt /home/FundPayment
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
ADD . /home/FundPayment

# Create directories and set permissions
RUN mkdir -p /home/FundPayment/staticfiles && \
    mkdir -p /home/FundPayment/payment/cron_job && \
    touch /home/FundPayment/payment/cron_job/log.log && \
    chmod 666 /home/FundPayment/payment/cron_job/log.log

# Add shell permission
RUN chmod -R +x /home/FundPayment/shell

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]