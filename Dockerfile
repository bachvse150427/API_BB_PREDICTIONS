FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies and AWS CLI
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends awscli && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r requirements.txt

# Create the data directory
RUN mkdir -p Get_Data

# Copy the rest of the application
COPY . .

# Install the application
RUN pip install -e .

# Expose the port that the app runs on
EXPOSE 8000

# Set the entrypoint to run our main.py script
CMD ["python", "main.py"] 