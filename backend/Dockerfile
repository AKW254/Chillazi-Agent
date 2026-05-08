FROM python:3.9-slim

#Environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory inside the container
WORKDIR /backend
# Install system packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*
# copy requirements file
COPY requirements.txt /app/
# Install dependencies
RUN  pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
# copy Backend code
COPY  . .
# Expose the port the app runs on
EXPOSE 8000
#Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]