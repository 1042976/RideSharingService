#!/bin/bash
python manage.py makemigrations
python manage.py migrate
while [ "1"=="1" ]
do
    python3 manage.py runserver 0.0.0.0:8000
    sleep 1
done
