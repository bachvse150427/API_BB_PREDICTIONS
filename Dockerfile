FROM python:3.10-slim-buster
WORKDIR /app
COPY . /app

RUN apt update -y && apt install awscli -y

RUN apt-get update && pip install -r requirements.txt

# Set the entrypoint to run our main.py script
CMD ["python", "main.py"] 