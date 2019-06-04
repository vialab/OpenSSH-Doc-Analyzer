#!/bin/bash
echo "Starting python server.."
source venv/bin/activate
export FLASK_APP=file_upload.py
export DEPLOY_ENV=TEST #PROD
flask run
echo "Python listening on http://localhost:5431"
