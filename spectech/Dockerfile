FROM python:3.10.9


ENV PYTHONUNBUFFERED 1
WORKDIR /spectech

EXPOSE 8000

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt


WORKDIR /spectech

RUN mkdir /spectech/static && mkdir /spectech/media

RUN chmod -R 755 /spectech/static



COPY spectech . ./

ENV PYTHONPATH /spectech
RUN chmod +x manage.py

CMD ["gunicorn", "-b", "0.0.0.0:8000", "spectech.wsgi:application"]
