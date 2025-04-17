import time
from block_stream_service import BlockStreamingService

# Dummy provider to simulate an Ethereum node for testing block processing
class DummyProvider:
    def __init__(self, blocks):
        # `blocks` is a dict mapping block number to a block data dict
        self.blocks = blocks
        self.name = "DummyProvider"
        # Simulate the latest block number this provider knows
        self.current_block = max(blocks.keys()) if blocks else 0
    
    @property
    def eth(self):
        # Return self as the eth interface
        return self
    
    @property
    def block_number(self):
        # Return the latest block number "mined"
        return self.current_block
    
    def get_block(self, number, full_transactions=False):
        # Return the block data if available
        return self.blocks.get(number)

def test_sequential_block_processing_no_gaps():
    # Set up dummy blockchain data with 5 sequential blocks
    dummy_blocks = {
        1: {"number": 1, "timestamp": 1000, "transactions": ["0xaaa"]},
        2: {"number": 2, "timestamp": 1015, "transactions": ["0xbbb"]},
        3: {"number": 3, "timestamp": 1030, "transactions": ["0xccc"]},
        4: {"number": 4, "timestamp": 1045, "transactions": ["0xddd"]},
        5: {"number": 5, "timestamp": 1060, "transactions": ["0xeee"]}
    }
    provider = DummyProvider(dummy_blocks)
    service = BlockStreamingService([{"name": "DummyPrimary", "web3": provider}], poll_interval=0.1)
    # Start from before the first block to capture all
    service.last_block = 0
    service.last_block_time = time.time()
    captured_blocks = []
    # Use a custom block handler to collect processed block numbers
    service._log_block = lambda block, pname: captured_blocks.append(block["number"])
    
    # Run one iteration of the loop (since one poll will capture all 5 blocks)
    service.run = lambda max_iterations=1: BlockStreamingService.run(service)  # monkey-patch run to allow param
    service.run(max_iterations=1)
    
    # Verify that all block numbers 1 through 5 were processed in order with no gaps
    assert captured_blocks == [1, 2, 3, 4, 5]
