# Base image
FROM python:3.12

# Create directory
RUN mkdir -p /home/FundPayment

# Set work directory
WORKDIR /home/FundPayment

# Install dependencies
ADD requirements.txt /home/FundPayment
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
ADD . /home/FundPayment

# Collect static files
RUN mkdir -p /home/FundPayment/staticfiles

# Add shell permission
RUN chmod -R +x /home/FundPayment/shell

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
