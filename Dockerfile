FROM python:3.12-slim

COPY . /sijac/

WORKDIR /sijac

RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt gunicorn

RUN mkdir -p /sijac

# CMD ["uvicorn", "src:app", "--host", "0.0.0.0", "--port", "8000"]
ENV NEW_RELIC_CONFIG_FILE=/sijac/newrelic.ini
ENV NEW_RELIC_ENVIRONMENT=production

# CMD para producción con New Relic + Gunicorn + Uvicorn
CMD ["newrelic-admin", "run-program", "gunicorn", "src:app", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]