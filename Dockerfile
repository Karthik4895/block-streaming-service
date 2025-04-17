# Use a lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install required Python packages
# Web3.py is required for Ethereum interactions
RUN pip install web3

# Copy the service code into the container
COPY block_stream_service.py ./block_stream_service.py

# The service will run as a simple Python application
CMD ["python", "block_stream_service.py"]
