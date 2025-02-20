# Script to start the production server

# Commit to the production branch
# git commit -am "Auto-trigger - Production server started" && git push origin Production

# backup database
# /usr/local/bin/python /home/nova-api/api/backup_manager/main.py pre_prodpush

# Kill production server
fuser -k 2333/tcp

# Clear production directory
rm -rf /home/nova-prod/*

# Copy files to production
cp -r * /home/nova-prod

# Copy .prod.env file to production
cp env/.prod.env /home/nova-prod/.env

# Change directory
cd /home/nova-prod

# Start screen
screen -L -Logfile .z.log -S nova-api python run prod && sleep 5
