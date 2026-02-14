#!/bin/bash

# Naviger vers le répertoire source
cd src

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Appliquer les migrations
python manage.py migrate --noinput

# Démarrer Gunicorn
gunicorn tropicalcorner.wsgi:application --bind=0.0.0.0:8000 --timeout 600
