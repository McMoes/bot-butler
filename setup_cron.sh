#!/bin/bash
CRON_JOB="0 2 * * * docker exec bot_butler-web-1 python manage.py autoclose_tickets >> /var/log/bot_butler_autoclose.log 2>&1"

# Check if the cron job already exists
crontab -l | grep -q "autoclose_tickets"
if [ $? -eq 0 ]; then
    echo "Cronjob already exists."
else
    # Append the new cronjob
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "Cronjob installed successfully."
fi
