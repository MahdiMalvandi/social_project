FROM python:alpine

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYCODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SUPERUSER_PASSWORD admin

COPY . .

COPY ./requirements.txt .
RUN pip install -r requirements.txt



RUN python3 manage.py collectstatic --noinput
RUN python manage.py migrate
CMD python manage.py runserver