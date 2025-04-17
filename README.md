# Ethereum Block Streaming Service

This project provides a Python-based **Ethereum block streaming service** that continuously polls for new blocks and logs their details, with automatic failover across multiple blockchain node providers. It is built with [Web3.py](https://web3py.readthedocs.io/) and is configured to use a Chainstack Ethereum RPC endpoint by default (and optionally an Alchemy endpoint for redundancy).

## Features

- **Continuous Block Streaming:** Polls an Ethereum node for the latest block and retrieves any new blocks sequentially, ensuring no block is skipped.
- **Structured Logging:** Logs each block's number, timestamp, and transaction list in JSON format for easy ingestion by monitoring systems.
- **Provider Failover:** Supports multiple RPC providers. Monitors provider health (e.g., delays, errors, incomplete data) and automatically switches to a backup provider if the current one fails or lags behind.
- **Modular Configuration:** Easily add or remove providers via configuration. The service can work with any Ethereum JSON-RPC endpoint (Chainstack, Alchemy, Infura, etc.).
- **Graceful Recovery:** Processes blocks in order even after switching providers, so the block stream remains uninterrupted.

## Getting Started

### Prerequisites

- **Python 3.9+** and `pip` for local development (or Docker).
- An Ethereum RPC endpoint URL. You can use a Chainstack node (sign up at Chainstack and create an Ethereum node to get an endpoint URL). Optionally, you can have a second endpoint (e.g., Alchemy) for failover.

### Installation

1. **Clone the repository** (or copy the module code):
   ```bash
   git clone https://example.com/block-streaming-service.git
   cd block-streaming-service
