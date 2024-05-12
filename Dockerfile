# Use the official Python image as base
FROM python:3.12.3

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container at /app
COPY . .

ENV DISPLAY=host.docker.internal:0.0

# Command to run the application
CMD ["python", "src/main.py"]
