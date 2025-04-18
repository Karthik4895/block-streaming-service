import os
import time
import json
import logging
from web3 import Web3, HTTPProvider
from web3.exceptions import BlockNotFound
from hexbytes import HexBytes

class BlockStreamingService:
    def __init__(self, providers, poll_interval=5, block_delay_threshold=60):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),              # Console
                logging.FileHandler("streaming.log")  # Log file
            ]
        )
        self.providers = self._init_providers(providers)
        self.current_provider_index = 0
        self.last_block = None
        self.last_block_time = None
        self.poll_interval = poll_interval
        self.block_delay_threshold = block_delay_threshold
        self.provider_failures = {}

    def _init_providers(self, providers):
        initialized = []
        for idx, prov in enumerate(providers):
            try:
                if isinstance(prov, str):
                    name = f"Provider{idx+1}"
                    web3 = Web3(HTTPProvider(prov, request_kwargs={"timeout": 10}))
                elif isinstance(prov, dict):
                    name = prov.get("name", f"Provider{idx+1}")
                    if "web3" in prov:
                        web3 = prov["web3"]
                    elif "url" in prov:
                        web3 = Web3(HTTPProvider(prov["url"], request_kwargs={"timeout": 10}))
                    else:
                        raise ValueError(f"Provider {name} must have either 'web3' or 'url'")

                else:
                    web3 = prov
                    name = getattr(prov, "name", f"Provider{idx+1}")
                
                # Test connection
                latest = web3.eth.block_number
                logging.info(f"Initialized provider {name} - latest block: {latest}")
                initialized.append({"name": name, "web3": web3})
            except Exception as e:
                logging.warning(f"Could not initialize provider {idx}: {str(e)}")
        
        if not initialized:
            raise ValueError("No working providers configured")
        return initialized

    def _log_block(self, block, provider_name):
        block_data = {
            "block_number": block["number"],
            "timestamp": block["timestamp"],
            "transaction_count": len(block["transactions"]),
            "provider": provider_name,
            "hash": block["hash"].hex()
        }
        logging.info(json.dumps(block_data))

    def _switch_provider(self):
        old_provider = self.providers[self.current_provider_index]['name']
        self.provider_failures[old_provider] = self.provider_failures.get(old_provider, 0) + 1

        wait_time = min(2 ** self.provider_failures[old_provider], 300)
        logging.warning(f"Waiting {wait_time}s before switching provider...")
        time.sleep(wait_time)

        self.current_provider_index = (self.current_provider_index + 1) % len(self.providers)
        new_provider = self.providers[self.current_provider_index]
        logging.warning(f"Switched from {old_provider} to {new_provider['name']}")

    def run(self):
        while True:
            provider = self.providers[self.current_provider_index]
            try:
                latest = provider["web3"].eth.block_number
                logging.info(f"Checked provider {provider['name']}, latest block: {latest}")

                if self.last_block is None:
                    self.last_block = latest - 1
                    self.last_block_time = time.time()

                if latest > self.last_block:
                    for block_num in range(self.last_block + 1, latest + 1):
                        try:
                            block = provider["web3"].eth.get_block(block_num)
                            self._log_block(block, provider["name"])
                            self.last_block = block_num
                            self.last_block_time = time.time()
                        except BlockNotFound:
                            logging.warning(f"Block {block_num} not found")
                            break
                        except Exception as e:
                            logging.error(f"Error getting block {block_num}: {str(e)}")
                            self._switch_provider()
                            break

                elif time.time() - self.last_block_time > self.block_delay_threshold:
                    logging.warning("No new blocks - possible provider stall")
                    self._switch_provider()

            except Exception as e:
                logging.error(f"Provider error: {str(e)}")
                self._switch_provider()

            time.sleep(self.poll_interval)

if __name__ == "__main__":
    providers = []

    # Load provider URLs (env, hardcoded, or config)
    chainstack_url = "https://nd-422-757-666.p2pify.com/0a9d79d93fb2f4a4b1e04695da2b77a7/"
    alchemy_url = "https://eth-mainnet.g.alchemy.com/v2/BY0_fsXr8ErdhC5q9tAqCezizLX2tCWR"

    if chainstack_url:
        providers.append({"name": "Chainstack", "url": chainstack_url})
    if alchemy_url:
        providers.append({"name": "Alchemy", "url": alchemy_url})
    if not providers:
        providers.append("https://cloudflare-eth.com")  # Fallback

    service = BlockStreamingService(providers)
    service.run()
