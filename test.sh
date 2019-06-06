#!/bin/bash
echo "Starting python server.."
source venv/bin/activate
export FLASK_APP=file_upload.py
export DEPLOY_ENV=PROD #PROD
export DATABASE_URL="mysql://sshcyber:Iut8iefa9aigah9Oo9eDai0vuz0Taed5queichePhut2eh0lae\`die2Yei~Rocho@mysql.science.uoit.ca:3306/sshcyber" #PROD
flask run
echo "Python listening on http://localhost:5000"
