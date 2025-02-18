FROM python:3.9

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /app/logs
EXPOSE 5000

CMD ["flask", "run"]
