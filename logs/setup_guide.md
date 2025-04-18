# Setup Guide: Blockchain Block Streaming Service

This guide explains how to set up and run the Ethereum block streaming service both locally and with Docker.

---

##  Prerequisites

- Python 3.9 or above
- Docker (optional, for container-based execution)
- `pip` installed (Python package manager)

---

##  Local Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/block-streaming-service.git
cd block-streaming-service


## 2. Create Virtual Environment
python3 -m venv venv
source venv/bin/activate

## 3. Install Dependencies
pip install -r requirements.txt



## 4. Run the Service
python block_stream_service.py



🐳 Docker Setup

1. Build the Docker Image
docker build -t block-streamer .

2. Run the Docker Container
docker run -e CHAINSTACK_URL="https://nd-422-757-666.p2pify.com/0a9d79d93fb2f4a4b1e04695da2b77a7/" \
           -e ALCHEMY_URL="https://eth-mainnet.g.alchemy.com/v2/BY0_fsXr8ErdhC5q9tAqCezizLX2tCWR" \
           block-streamer

Running Tests

Run unit and integration tests using:

pytest tests/