FROM python:3

# Directory for the app
# Sets the Working dir and location in one command
WORKDIR /opt/lumina

# Copy the contents of server
# to the container
COPY lumina .
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose this port number
EXPOSE 8443

# Run this ComManD
CMD ["python", "./lumina/lumina_server.py"]

