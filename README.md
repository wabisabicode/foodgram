# Foodgram

A social network for food lovers and everyone who enjoys cooking and eating with soul. 🧑‍🍳

Visit the website at [foodgram.fintracker.de](https://foodgram.fintracker.de), register, and add recipes to your favorites, subscribe to other authors, and get your personalized shopping list from the recipes you like.

-----

## Technology Stack

[![Django](https://img.shields.io/badge/-Django-092E20?style=flat&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/-Django%20REST%20Framework-092E20?style=flat&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-336791?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/-Docker-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![Docker Compose](https://img.shields.io/badge/-Docker--compose-2496ED?style=flat&logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![Nginx](https://img.shields.io/badge/-Nginx-009639?style=flat&logo=nginx&logoColor=white)](https://www.nginx.com/)
[![Gunicorn](https://img.shields.io/badge/-Gunicorn-499848?style=flat&logo=gunicorn&logoColor=white)](https://gunicorn.org/)
[![GitHub Actions](https://img.shields.io/badge/-GitHub%20Actions-2088FF?style=flat&logo=githubactions&logoColor=white)](https://github.com/features/actions)

-----

## CI/CD

The project is built from four containers:
backend, frontend, postgresql, nginx.

Automatic testing is included when commits are added to the main project branch, along with deployment to the server. You can find more details on the project's [GitHub](https://github.com/wabisabicode/foodgram).

-----

## Local Deployment

Developers can deploy the project locally. To do this, navigate to the `infra` directory and run docker compose:

```
cd infra && sudo docker compose up --build -d
```

The project will be available at the local address [http://127.0.0.1](http://127.0.0.1)

For a successful launch, you need a `backend/.env` file. Here is a template for the file:

```
# secret key for Django
SECRET_KEY=
# debug mode True/False
DEBUG_MODE=
# database name
POSTGRES_DB=
# DB username
POSTGRES_USER=
# DB user password
POSTGRES_PASSWORD=
# DB hostname - must match the DB service name in docker-compose.yml
DB_HOST=
# DB connection port
DB_PORT=5432
```

After the containers have started successfully, you need to manually run Django migrations and collect static files in the `backend` container.

```
sudo docker compose exec backend python manage.py migrate
sudo docker compose exec backend python manage.py collectstatic
sudo docker compose exec backend cp -r /app/foodgram_backend/collected_static/. /backend_static/static/
```

After this, the project is ready for local work and testing.
