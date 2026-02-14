#!/bin/bash
set -e  # Arrêter si une commande échoue

echo "Starting Tropical Corner backend..."

# Naviger vers le répertoire source
cd src

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Appliquer les migrations (critique - doit réussir)
echo "Running database migrations..."
python manage.py migrate --noinput

# Démarrer Gunicorn
echo "Starting Gunicorn..."
gunicorn tropicalcorner.wsgi:application --bind=0.0.0.0:8000 --timeout 600
