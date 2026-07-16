FROM python:3.11-slim
WORKDIR /app
COPY proxy/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY proxy/ .
EXPOSE 9000
CMD ["python", "run.py"]
