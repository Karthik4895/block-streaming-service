import time
from block_stream_service import BlockStreamingService

class DummyProvider:
    def __init__(self, latest_block, fail_on_block=None, fail_on_latest=False):
        self.name = "DummyProvider"
        self.latest_block = latest_block
        self.fail_on_block = fail_on_block
        self.fail_on_latest = fail_on_latest
        self.blocks = {n: {"number": n, "timestamp": 1000 + 15*n, "transactions": []} 
                       for n in range(1, latest_block + 1)}
    
    @property
    def eth(self):
        return self
    
    @property
    def block_number(self):
        if self.fail_on_latest:
            raise Exception("Latest block fetch failed")
        return self.latest_block
    
    def get_block(self, number, full_transactions=False):
        if self.fail_on_block is not None and number == self.fail_on_block:
            return None
        return self.blocks.get(number)

def test_switch_on_stalled_provider():
    provider_a = DummyProvider(latest_block=5)
    provider_b = DummyProvider(latest_block=5)
    service = BlockStreamingService([{"name": "ProviderA", "web3": provider_a},
                                     {"name": "ProviderB", "web3": provider_b}], 
                                    poll_interval=0.1, block_delay_threshold=1.0)
    service.last_block = 5
    service.last_block_time = time.time() - 5  # 5 seconds ago
    initial_provider = service.current_provider_index
    
    service.run = lambda max_iterations=1: BlockStreamingService.run(service)  # allow breaking after one loop
    service.run(max_iterations=1)
    
    assert service.current_provider_index != initial_provider
    assert service.current_provider_index == 1  # switched to second provider
