import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timezone
from azure.eventhub import EventData
from azure.eventhub.aio import EventHubProducerClient
from azure.identity import DefaultAzureCredential
import os
from typing import Dict, List, Optional
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EthereumDataCollector:
    def __init__(self, config: Dict):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.producer_client: Optional[EventHubProducerClient] = None
        self.credential = DefaultAzureCredential()
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100)
        )
        
        # Initialize Event Hub producer
        self.producer_client = EventHubProducerClient(
            fully_qualified_namespace=self.config["event_hub"]["namespace"],
            eventhub_name=self.config["event_hub"]["name"],
            credential=self.credential
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.producer_client:
            await self.producer_client.close()
    
    async def fetch_ethereum_data(self) -> Dict:
        """Fetch comprehensive Ethereum data from multiple sources"""
        tasks = [
            self.fetch_current_price(),
            self.fetch_network_stats(),
            self.fetch_recent_blocks(),
            self.fetch_gas_tracker(),
            self.fetch_defi_metrics()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine all data with metadata
        combined_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data_version": "1.0",
            "source": "ethereum_collector",
            "price_data": results[0] if not isinstance(results[0], Exception) else None,
            "network_stats": results[1] if not isinstance(results[1], Exception) else None,
            "recent_blocks": results[2] if not isinstance(results[2], Exception) else None,
            "gas_data": results[3] if not isinstance(results[3], Exception) else None,
            "defi_metrics": results[4] if not isinstance(results[4], Exception) else None,
            "errors": [str(r) for r in results if isinstance(r, Exception)]
        }
        
        return combined_data
    
    async def fetch_current_price(self) -> Dict:
        """Fetch current ETH price and market data"""
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "ethereum",
            "vs_currencies": "usd,btc",
            "include_market_cap": "true",
            "include_24hr_vol": "true",
            "include_24hr_change": "true"
        }
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "price_usd": data["ethereum"]["usd"],
                    "price_btc": data["ethereum"]["btc"],
                    "market_cap": data["ethereum"]["usd_market_cap"],
                    "volume_24h": data["ethereum"]["usd_24h_vol"],
                    "change_24h": data["ethereum"]["usd_24h_change"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            else:
                raise Exception(f"Price API error: {response.status}")
    
    async def fetch_network_stats(self) -> Dict:
        """Fetch Ethereum network statistics"""
        # Using Etherscan API
        api_key = self.config["apis"]["etherscan_key"]
        base_url = "https://api.etherscan.io/api"
        
        tasks = [
            self.session.get(f"{base_url}?module=stats&action=ethsupply&apikey={api_key}"),
            self.session.get(f"{base_url}?module=stats&action=ethprice&apikey={api_key}"),
            self.session.get(f"{base_url}?module=proxy&action=eth_blockNumber&apikey={api_key}")
        ]
        
        responses = await asyncio.gather(*tasks)
        results = []
        for response in responses:
            if response.status == 200:
                results.append(await response.json())
            else:
                results.append({"error": f"Status {response.status}"})
        
        return {
            "total_supply": results[0].get("result", "0"),
            "eth_price": results[1].get("result", {}),
            "latest_block": int(results[2].get("result", "0"), 16) if results[2].get("result") else 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def fetch_recent_blocks(self, count: int = 5) -> List[Dict]:
        """Fetch recent Ethereum blocks"""
        api_key = self.config["apis"]["etherscan_key"]
        base_url = "https://api.etherscan.io/api"
        
        # Get latest block number first
        response = await self.session.get(
            f"{base_url}?module=proxy&action=eth_blockNumber&apikey={api_key}"
        )
        
        if response.status != 200:
            raise Exception(f"Block number API error: {response.status}")
        
        data = await response.json()
        latest_block = int(data["result"], 16)
        
        # Fetch recent blocks
        blocks = []
        for i in range(count):
            block_number = latest_block - i
            block_response = await self.session.get(
                f"{base_url}?module=proxy&action=eth_getBlockByNumber&"
                f"tag=0x{block_number:x}&boolean=true&apikey={api_key}"
            )
            
            if block_response.status == 200:
                block_data = await block_response.json()
                if block_data.get("result"):
                    block = block_data["result"]
                    blocks.append({
                        "number": int(block["number"], 16),
                        "hash": block["hash"],
                        "timestamp": int(block["timestamp"], 16),
                        "transaction_count": len(block.get("transactions", [])),
                        "gas_used": int(block["gasUsed"], 16),
                        "gas_limit": int(block["gasLimit"], 16),
                        "miner": block["miner"],
                        "size": int(block["size"], 16)
                    })
        
        return blocks
    
    async def fetch_gas_tracker(self) -> Dict:
        """Fetch current gas prices"""
        api_key = self.config["apis"]["etherscan_key"]
        url = f"https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey={api_key}"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                result = data.get("result", {})
                return {
                    "safe_gas_price": int(result.get("SafeGasPrice", 0)),
                    "standard_gas_price": int(result.get("StandardGasPrice", 0)),
                    "fast_gas_price": int(result.get("FastGasPrice", 0)),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            else:
                raise Exception(f"Gas tracker API error: {response.status}")
    
    async def fetch_defi_metrics(self) -> Dict:
        """Fetch DeFi metrics from DeFiPulse API"""
        try:
            url = "https://api.defipulse.com/v1/egs"
            headers = {"Api-Key": self.config["apis"].get("defipulse_key", "")}
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "total_value_locked": data.get("total", 0),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                else:
                    return {"total_value_locked": 0, "error": f"Status {response.status}"}
        except Exception as e:
            return {"total_value_locked": 0, "error": str(e)}
    
    async def send_to_event_hub(self, data: Dict):
        """Send data to Azure Event Hub"""
        try:
            # Add partition key for better distribution
            partition_key = str(hash(data["timestamp"]) % 10)
            
            event_data = EventData(json.dumps(data))
            event_data.properties = {
                "source": "ethereum_collector",
                "version": "1.0",
                "data_type": "ethereum_metrics"
            }
            
            async with self.producer_client:
                await self.producer_client.send_batch([event_data], partition_key=partition_key)
            
            logger.info(f"Data sent to Event Hub successfully at {data['timestamp']}")
            
        except Exception as e:
            logger.error(f"Failed to send data to Event Hub: {str(e)}")
            raise
    
    async def run_collection_loop(self, interval_seconds: int = 10):
        """Main collection loop"""
        logger.info(f"Starting Ethereum data collection with {interval_seconds}s interval")
        
        while True:
            try:
                start_time = time.time()
                
                # Collect data
                data = await self.fetch_ethereum_data()
                
                # Send to Event Hub
                await self.send_to_event_hub(data)
                
                # Calculate processing time
                processing_time = time.time() - start_time
                logger.info(f"Collection cycle completed in {processing_time:.2f}s")
                
                # Wait for next interval
                sleep_time = max(0, interval_seconds - processing_time)
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in collection loop: {str(e)}")
                await asyncio.sleep(5)  # Short delay before retry

# Configuration
config = {
    "event_hub": {
        "namespace": os.getenv("EVENT_HUB_NAMESPACE"),
        "name": os.getenv("EVENT_HUB_NAME")
    },
    "apis": {
        "etherscan_key": os.getenv("ETHERSCAN_API_KEY"),
        "defipulse_key": os.getenv("DEFIPULSE_API_KEY")
    }
}

# Main execution
async def main():
    async with EthereumDataCollector(config) as collector:
        await collector.run_collection_loop(interval_seconds=10)

if __name__ == "__main__":
    asyncio.run(main())