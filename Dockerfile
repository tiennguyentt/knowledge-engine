FROM python:3.13-slim
WORKDIR /app
COPY webapp/requirements.txt /app/webapp/requirements.txt
RUN pip install --no-cache-dir -r webapp/requirements.txt
COPY . /app
EXPOSE 7860
CMD uvicorn webapp.main:app --host 0.0.0.0 --port ${PORT:-7860}
