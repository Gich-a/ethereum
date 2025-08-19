import os
from azure.kusto.data import KustoClient
from azure.kusto.data.helpers import ConnectionStringBuilder

def setup_kusto_tables_and_policies(kusto_cluster_uri, kusto_database_name):
    """
    Sets up the necessary tables and update policies in the Kusto database.
    This script is run after the Kusto cluster and database have been provisioned.
    """
    kcsb = ConnectionStringBuilder.with_az_cli_authentication(kusto_cluster_uri)
    client = KustoClient(kcsb)
    
    # Commands to create the tables
    commands = [
        # Table for raw events from Event Hub
        f".create table EthereumEvents (Timestamp:datetime, EventType:string, Data:dynamic)",
        # Table for transformed Ethereum price data
        f".create table EthereumPrices (Timestamp:datetime, Price:real)",
        # Table for transformed Ethereum gas data
        f".create table EthereumGas (Timestamp:datetime, GasPrice:real)"
    ]

    for command in commands:
        try:
            response = client.execute_mgmt(kusto_database_name, command)
            print(f"Executed command: {command}")
        except Exception as e:
            print(f"Failed to execute command '{command}': {e}")
            
    # Commands to create the update policies
    policy_commands = [
        # Policy to transform and ingest price data
        f".alter table EthereumPrices policy update @'[{{\"Source\": \"EthereumEvents\", \"Kind\": \"UpdatePolicy\", \"Query\": \"EthereumEvents | where EventType == \\\"EthereumPrice\\\" | project Timestamp, Price = toreal(Data.price)\", \"IsEnabled\": \"true\"}}]'",
        # Policy to transform and ingest gas data
        f".alter table EthereumGas policy update @'[{{\"Source\": \"EthereumEvents\", \"Kind\": \"UpdatePolicy\", \"Query\": \"EthereumEvents | where EventType == \\\"GasPrice\\\" | project Timestamp, GasPrice = toreal(Data.gas_price_gwei)\", \"IsEnabled\": \"true\"}}]'"
    ]
    
    for command in policy_commands:
        try:
            response = client.execute_mgmt(kusto_database_name, command)
            print(f"Executed policy command: {command}")
        except Exception as e:
            print(f"Failed to execute policy command '{command}': {e}")
