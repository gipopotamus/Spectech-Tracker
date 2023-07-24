FROM python:3.10.9


ENV PYTHONUNBUFFERED 1
WORKDIR /spectech


COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt


WORKDIR /spectech

RUN mkdir /spectech/static && mkdir /spectech/media


COPY spectech . .

ENV PYTHONPATH /spectech

CMD ["gunicorn", "-b", "0.0.0.0:8000", "spectech.wsgi:application"]