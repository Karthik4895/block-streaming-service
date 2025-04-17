from block_stream_service import BlockStreamingService, time

class DummyProvider:
    def __init__(self, name, block_data, fail_on_block=None):
        self.name = name
        # block_data: dict of block number -> block info
        self.blocks = block_data
        self.fail_on_block = fail_on_block
        # Latest block number this provider knows (could simulate lag)
        self.latest_block = max(block_data.keys()) if block_data else 0
    
    @property
    def eth(self):
        return self
    
    @property
    def block_number(self):
        # Return what this provider considers the latest block
        return self.latest_block
    
    def get_block(self, number, full_transactions=False):
        # If this provider is supposed to fail on a specific block number, simulate missing block
        if self.fail_on_block is not None and number == self.fail_on_block:
            return None
        return self.blocks.get(number)

def test_failover_and_catch_up():
    # Provider A has blocks 1 and 2, but will "fail" on block 3
    provider_a_data = {
        1: {"number": 1, "timestamp": 1000, "transactions": ["0x1"]},
        2: {"number": 2, "timestamp": 1010, "transactions": ["0x2"]}
        # block 3 is intentionally missing to simulate a failure to provide it
    }
    provider_a = DummyProvider("ProviderA", provider_a_data, fail_on_block=3)
    provider_a.latest_block = 3  # Provider A believes block 3 should exist (but it can't retrieve it)
    # Provider B has blocks 1,2,3,4 (so it can provide block 3 and beyond)
    provider_b_data = {
        1: {"number": 1, "timestamp": 1000, "transactions": ["0x1"]},
        2: {"number": 2, "timestamp": 1010, "transactions": ["0x2"]},
        3: {"number": 3, "timestamp": 1020, "transactions": ["0x3"]},
        4: {"number": 4, "timestamp": 1030, "transactions": ["0x4"]}
    }
    provider_b = DummyProvider("ProviderB", provider_b_data)
    provider_b.latest_block = 4
    
    service = BlockStreamingService([{"name": "ProviderA", "web3": provider_a},
                                     {"name": "ProviderB", "web3": provider_b}], 
                                    poll_interval=0.1)
    service.last_block = 0  # start before the first block
    service.last_block_time = time.time()
    processed_blocks = []
    service._log_block = lambda block, src: processed_blocks.append((block["block_number"], src))
    
    # Run the service for a few iterations to allow switch-over
    service.run = lambda max_iterations=3: BlockStreamingService.run(service)  # limit iterations
    service.run(max_iterations=3)
    
    # The service should process blocks 1 and 2 from ProviderA, then fail on 3, switch to ProviderB,
    # and then process block 3 and 4 from ProviderB.
    expected = [(1, "ProviderA"), (2, "ProviderA"), (3, "ProviderB"), (4, "ProviderB")]
    assert processed_blocks == expected
