# data-collector/collector.py
import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
from azure.kusto.data.exceptions import KustoServiceError
from azure.identity import DefaultAzureCredential
import time

class EthereumDataCollector:
    """Collects Ethereum blockchain data from various APIs"""
    
    def __init__(self, config_path: str = None):
        import os
        if config_path is None:
            # Always resolve path relative to this script's directory
            config_path = os.path.join(os.path.dirname(__file__), "config.json")
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.logger = self._setup_logger()
        self.kusto_client = self._setup_kusto_client()
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("ethereum_collector")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    
    def _setup_kusto_client(self) -> KustoClient:
        """Setup Azure Data Explorer (Kusto) client"""
        cluster_uri = self.config["kusto"]["cluster_uri"]
        kcsb = KustoConnectionStringBuilder.with_az_cli_authentication(cluster_uri)
        return KustoClient(kcsb)
    
    async def collect_eth_price_data(self, session: aiohttp.ClientSession) -> Dict:
        """Collect Ethereum price data from CoinGecko API"""
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "ethereum",
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_market_cap": "true",
            "include_24hr_vol": "true"
        }
        
        try:
            async with session.get(url, params=params) as response:
                data = await response.json()
                
                price_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "price_usd": data["ethereum"]["usd"],
                    "market_cap": data["ethereum"]["usd_market_cap"],
                    "volume_24h": data["ethereum"]["usd_24h_vol"],
                    "change_24h": data["ethereum"]["usd_24h_change"]
                }
                
                self.logger.info(f"Collected ETH price: ${price_data['price_usd']}")
                return price_data
                
        except Exception as e:
            self.logger.error(f"Error collecting price data: {e}")
            raise
    
    async def collect_gas_data(self, session: aiohttp.ClientSession) -> Dict:
        """Collect Ethereum gas price data"""
        url = f"https://api.etherscan.io/api"
        params = {
            "module": "gastracker",
            "action": "gasoracle",
            "apikey": self.config["etherscan"]["api_key"]
        }
        
        try:
            async with session.get(url, params=params) as response:
                data = await response.json()
                
                gas_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "safe_gas_price": int(data["result"]["SafeGasPrice"]),
                    "standard_gas_price": int(data["result"]["StandardGasPrice"]),
                    "fast_gas_price": int(data["result"]["FastGasPrice"])
                }
                
                self.logger.info(f"Collected gas data - Fast: {gas_data['fast_gas_price']} gwei")
                return gas_data
                
        except Exception as e:
            self.logger.error(f"Error collecting gas data: {e}")
            raise
    
    async def collect_erc20_transfers(self, session: aiohttp.ClientSession, 
                                    contract_address: str, 
                                    from_block: int = None) -> List[Dict]:
        """Collect ERC20 transfer events"""
        if from_block is None:
            from_block = await self.get_latest_block(session) - 100
        
        url = f"https://api.etherscan.io/api"
        params = {
            "module": "logs",
            "action": "getLogs",
            "address": contract_address,
            "topic0": "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",  # Transfer event
            "fromBlock": from_block,
            "toBlock": "latest",
            "apikey": self.config["etherscan"]["api_key"]
        }
        
        try:
            async with session.get(url, params=params) as response:
                data = await response.json()
                
                transfers = []
                for log in data.get("result", []):
                    transfer = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "transaction_hash": log["transactionHash"],
                        "block_number": int(log["blockNumber"], 16),
                        "contract_address": log["address"],
                        "from_address": "0x" + log["topics"][1][-40:],
                        "to_address": "0x" + log["topics"][2][-40:],
                        "value": int(log["data"], 16),
                        "gas_price": int(log["gasPrice"], 16) if log.get("gasPrice") else None,
                        "gas_used": int(log["gasUsed"], 16) if log.get("gasUsed") else None
                    }
                    transfers.append(transfer)
                
                self.logger.info(f"Collected {len(transfers)} ERC20 transfers")
                return transfers
                
        except Exception as e:
            self.logger.error(f"Error collecting ERC20 transfers: {e}")
            raise
    
    async def get_latest_block(self, session: aiohttp.ClientSession) -> int:
        """Get latest block number"""
        url = f"https://api.etherscan.io/api"
        params = {
            "module": "proxy",
            "action": "eth_blockNumber",
            "apikey": self.config["etherscan"]["api_key"]
        }
        
        async with session.get(url, params=params) as response:
            data = await response.json()
            return int(data["result"], 16)
    
    def ingest_to_kusto(self, data: List[Dict], table_name: str):
        """Ingest data to Azure Data Explorer"""
        try:
            df = pd.DataFrame(data)
            
            # Create ingestion command
            ingestion_command = f"""
            .ingest inline into table {table_name} <|
            {df.to_csv(index=False, header=False)}
            """
            
            database = self.config["kusto"]["database"]
            self.kusto_client.execute(database, ingestion_command)
            
            self.logger.info(f"Ingested {len(data)} records to {table_name}")
            
        except KustoServiceError as e:
            self.logger.error(f"Kusto ingestion error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error ingesting data: {e}")
            raise
    
    async def run_collection_cycle(self):
        """Run a single collection cycle"""
        async with aiohttp.ClientSession() as session:
            try:
                # Collect price data
                price_data = await self.collect_eth_price_data(session)
                self.ingest_to_kusto([price_data], "eth_price_raw")
                
                # Collect gas data
                gas_data = await self.collect_gas_data(session)
                self.ingest_to_kusto([gas_data], "eth_gas_raw")
                
                # Collect ERC20 transfers for major tokens
                for contract in self.config.get("erc20_contracts", []):
                    transfers = await self.collect_erc20_transfers(
                        session, 
                        contract["address"]
                    )
                    if transfers:
                        self.ingest_to_kusto(transfers, "erc20_transfers_raw")
                
                self.logger.info("Collection cycle completed successfully")
                
            except Exception as e:
                self.logger.error(f"Collection cycle failed: {e}")
                raise
    
    async def run_continuous(self, interval_seconds: int = 300):
        """Run continuous data collection"""
        self.logger.info(f"Starting continuous collection (interval: {interval_seconds}s)")
        
        while True:
            try:
                await self.run_collection_cycle()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                self.logger.error(f"Error in continuous collection: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

def main():
    collector = EthereumDataCollector()
    
    # Run based on config
    if collector.config.get("mode") == "continuous":
        interval = collector.config.get("collection_interval", 300)
        asyncio.run(collector.run_continuous(interval))
    else:
        # Single collection cycle
        asyncio.run(collector.run_collection_cycle())

if __name__ == "__main__":
    main()