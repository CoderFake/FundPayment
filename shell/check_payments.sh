#!/bin/bash
echo "===== Bắt đầu kiểm tra thanh toán đang chờ xử lý ====="
date

export DJANGO_SETTINGS_MODULE=FundPayment.settings
export PYTHONPATH=/home/FundPayment

cd /home/FundPayment
python manage.py check_pending_payments

echo "===== Kết thúc kiểm tra thanh toán ====="
date