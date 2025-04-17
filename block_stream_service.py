import os
import time
import json
import logging
from web3 import Web3, HTTPProvider
from hexbytes import HexBytes

class BlockStreamingService:
    """
    A service to continuously stream Ethereum blocks using multiple RPC providers.
    It polls for the latest block and logs structured block data, with automatic 
    failover between providers to ensure no blocks are missed.
    """
    def __init__(self, providers, poll_interval=5, block_delay_threshold=60):
        """
        Initialize the block streaming service.
        
        :param providers: List of provider endpoints or Web3 provider objects. 
                          Endpoints can be given as URLs or dicts {"name": ..., "url": ...}.
        :param poll_interval: How often to poll for new blocks (in seconds).
        :param block_delay_threshold: Time (in seconds) with no new block before considering 
                                      the provider unhealthy (stuck/lagging) and switching.
        """
        # Configure logging to output structured info and warnings/errors
        logging.basicConfig(level=logging.INFO, 
                            format="%(asctime)s - %(levelname)s - %(message)s")
        self.providers = []
        for idx, prov in enumerate(providers):
            # Accept various provider representations for flexibility
            if isinstance(prov, str):
                # prov is a URL string
                name = f"Provider{idx+1}"
                url = prov
                web3_obj = Web3(HTTPProvider(url, request_kwargs={"timeout": 10}))
            elif isinstance(prov, dict):
                # prov is a dict potentially with 'name', 'url', or a ready 'web3'
                name = prov.get("name", f"Provider{idx+1}")
                if "web3" in prov:
                    web3_obj = prov["web3"]
                else:
                    url = prov.get("url")
                    web3_obj = Web3(HTTPProvider(url, request_kwargs={"timeout": 10}))
            else:
                # prov is already a Web3-like object
                web3_obj = prov
                name = getattr(prov, "name", f"Provider{idx+1}")
            self.providers.append({"name": name, "web3": web3_obj})
        if not self.providers:
            raise ValueError("No providers configured for BlockStreamingService")
        self.current_provider_index = 0  # start with the first provider in the list
        self.last_block = None          # last block number processed
        self.last_block_time = None     # time when last block was processed
        self.poll_interval = poll_interval                   
        self.block_delay_threshold = block_delay_threshold
    
    def _log_block(self, block, provider_name):
        # Convert transaction hashes from HexBytes to hex strings
        txs = block["transactions"]
        if isinstance(txs[0], HexBytes):
            txs = [tx.hex() for tx in txs]

        block_data = {
            "block_number": int(block["number"]),
            "timestamp": int(block["timestamp"]),
            "transactions": txs,
            "provider": provider_name
        }

        logging.info(json.dumps(block_data))
    
    def _switch_provider(self):
        """
        Switch to the next provider in the list (for failover).
        Called when the current provider is deemed unhealthy or fails.
        """
        old_index = self.current_provider_index
        self.current_provider_index = (old_index + 1) % len(self.providers)
        new_provider = self.providers[self.current_provider_index]
        logging.warning(f"Switching provider from {self.providers[old_index]['name']} to {new_provider['name']}")
        # Note: If we cycle back to a previously failing provider, ideally implement backoff to avoid rapid flips.
    
    def run(self):
        """
        Start the block streaming loop. This will continuously poll for new blocks 
        and log them, switching providers on failure or delay.
        """
        # If starting fresh, initialize last_block to current latest block (no history replay)
        provider = self.providers[self.current_provider_index]
        try:
            current_latest = provider["web3"].eth.block_number
        except Exception as e:
            logging.error(f"Initial provider {provider['name']} unavailable: {e}")
            self._switch_provider()
            # Try once to get initial latest from the next provider
            provider = self.providers[self.current_provider_index]
            current_latest = provider["web3"].eth.block_number
        self.last_block = current_latest
        self.last_block_time = time.time()
        logging.info(f"Starting block streaming at block {self.last_block} (provider: {provider['name']})")
        
        # Continuous polling loop
        while True:
            provider = self.providers[self.current_provider_index]
            provider_name = provider["name"]
            web3 = provider["web3"]
            try:
                latest_block_number = web3.eth.block_number
            except Exception as e:
                # Provider connection or HTTP error
                logging.error(f"Failed to fetch latest block from {provider_name}: {e}")
                self._switch_provider()
                continue  # retry loop with next provider immediately
            
            if latest_block_number > self.last_block:
                # New blocks have arrived since last processed block
                for next_block_num in range(self.last_block + 1, latest_block_number + 1):
                    try:
                        block = web3.eth.get_block(next_block_num, full_transactions=False)
                    except Exception as e:
                        logging.error(f"Error retrieving block {next_block_num} from {provider_name}: {e}")
                        # On error (e.g., provider could not deliver the block), switch provider
                        self._switch_provider()
                        break  # break out of for-loop, will continue with new provider in next iteration
                    if block is None:
                        logging.error(f"Block {next_block_num} missing from {provider_name} (possible sync issue)")
                        # Provider returned no data for a block that should exist (integrity issue)&#8203;:contentReference[oaicite:0]{index=0}
                        self._switch_provider()
                        break
                    # Log the fetched block
                    self._log_block(block, provider_name)
                    self.last_block = next_block_num
                    self.last_block_time = time.time()
                else:
                    # Only reach here if the for-loop did NOT break (i.e., all blocks processed successfully)
                    # Continue normally to next iteration after sleeping.
                    pass
            else:
                # No new block found
                if time.time() - self.last_block_time >= self.block_delay_threshold:
                    # No new block in a while – consider the provider lagging or stuck&#8203;:contentReference[oaicite:1]{index=1}
                    logging.warning(f"No new block for {self.block_delay_threshold}s from {provider_name}. Triggering failover.")
                    self._switch_provider()
                    # After switching, immediately check the new provider on next loop (no sleep)
                    continue
            # Wait for a short interval before polling again
            time.sleep(self.poll_interval)

# If run as a script, set up providers and start the service
if __name__ == "__main__":
    # Read provider URLs from environment (Chainstack and optionally Alchemy)
    chainstack_url = "https://nd-422-757-666.p2pify.com/0a9d79d93fb2f4a4b1e04695da2b77a7/"
    alchemy_url = "https://eth-mainnet.g.alchemy.com/v2/BY0_fsXr8ErdhC5q9tAqCezizLX2tCWR"
    providers = []
    if chainstack_url:
        providers.append({"name": "Chainstack", "url": chainstack_url})
    else:
        # Use a public fallback (note: limited reliability without API key)
        fallback_url = "https://cloudflare-eth.com"
        logging.warning("CHAINSTACK_URL not set. Using public fallback RPC (Cloudflare Ethereum).")
        providers.append({"name": "PublicRPC", "url": fallback_url})
    if alchemy_url:
        providers.append({"name": "Alchemy", "url": alchemy_url})
    
    service = BlockStreamingService(providers)
    service.run()
