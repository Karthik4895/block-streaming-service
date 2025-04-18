import time
from block_stream_service import BlockStreamingService

class DummyProvider:
    def __init__(self, blocks):
        self.blocks = blocks
        self.name = "DummyProvider"
        self.current_block = max(blocks.keys()) if blocks else 0
    
    @property
    def eth(self):
        return self
    
    @property
    def block_number(self):
        return self.current_block
    
    def get_block(self, number, full_transactions=False):
        return self.blocks.get(number)

def test_sequential_block_processing_no_gaps():
    dummy_blocks = {
        1: {"number": 1, "timestamp": 1000, "transactions": ["0xaaa"]},
        2: {"number": 2, "timestamp": 1015, "transactions": ["0xbbb"]},
        3: {"number": 3, "timestamp": 1030, "transactions": ["0xccc"]},
        4: {"number": 4, "timestamp": 1045, "transactions": ["0xddd"]},
        5: {"number": 5, "timestamp": 1060, "transactions": ["0xeee"]}
    }
    provider = DummyProvider(dummy_blocks)
    service = BlockStreamingService([{"name": "DummyPrimary", "web3": provider}], poll_interval=0.1)
    service.last_block = 0
    service.last_block_time = time.time()
    captured_blocks = []
    service._log_block = lambda block, pname: captured_blocks.append(block["number"])
    
    service.run = lambda max_iterations=1: BlockStreamingService.run(service)  # monkey-patch run to allow param
    service.run(max_iterations=1)
    
    assert captured_blocks == [1, 2, 3, 4, 5]
