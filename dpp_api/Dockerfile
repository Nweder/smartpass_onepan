# Use an official Python runtime as the base image
FROM python:3.9.13

# Set the working directory in the container to /app
WORKDIR /dpp_api

# Copy the current directory (our Flask app) into the container at /app
COPY . .

# Install Flask and other dependencies
RUN pip install -r requirements.txt

# Make port 5000 available for the app
EXPOSE 5000

# Run the command to start the Flask app
CMD ["flask", "run", "--host=0.0.0.0"]