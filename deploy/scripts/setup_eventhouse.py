import os
from azure.kusto.data import KustoClient
from azure.kusto.data.helpers import ConnectionStringBuilder

def setup_kusto_tables_and_policies(kusto_cluster_uri, kusto_database_name):
    """
    Sets up the necessary tables and update policies in the Kusto database.
    This script is run after the Kusto cluster and database have been provisioned.
    """
    # Use Azure CLI authentication to connect to the Kusto cluster
    kcsb = ConnectionStringBuilder.with_az_cli_authentication(kusto_cluster_uri)
    client = KustoClient(kcsb)
    
    # List of KQL commands to create the tables for raw and transformed data
    commands = [
        # Table for raw events from Event Hub
        f".create table EthereumEvents (Timestamp:datetime, EventType:string, Data:dynamic)",
        # Table for transformed Ethereum price data
        f".create table EthereumPrices (Timestamp:datetime, Price:real)",
        # Table for transformed Ethereum gas data
        f".create table EthereumGas (Timestamp:datetime, GasPrice:real)"
    ]

    print("Creating tables...")
    for command in commands:
        try:
            # Execute the management command to create the table
            client.execute_mgmt(kusto_database_name, command)
            print(f"Executed command: {command}")
        except Exception as e:
            print(f"Failed to execute command '{command}': {e}")
            
    # List of KQL commands to create the update policies
    # These policies will automatically transform data from EthereumEvents into the
    # dedicated Price and Gas tables as new data arrives.
    policy_commands = [
        # Policy to transform and ingest price data
        f".alter table EthereumPrices policy update @'[{{\"Source\": \"EthereumEvents\", \"Kind\": \"UpdatePolicy\", \"Query\": \"EthereumEvents | where EventType == \\\"EthereumPrice\\\" | project Timestamp, Price = toreal(Data.price)\", \"IsEnabled\": \"true\"}}]'",
        # Policy to transform and ingest gas data
        f".alter table EthereumGas policy update @'[{{\"Source\": \"EthereumEvents\", \"Kind\": \"UpdatePolicy\", \"Query\": \"EthereumEvents | where EventType == \\\"GasPrice\\\" | project Timestamp, GasPrice = toreal(Data.gas_price_gwei)\", \"IsEnabled\": \"true\"}}]'"
    ]
    
    print("\nCreating update policies...")
    for command in policy_commands:
        try:
            # Execute the management command to create the update policy
            client.execute_mgmt(kusto_database_name, command)
            print(f"Executed policy command: {command}")
        except Exception as e:
            print(f"Failed to execute policy command '{command}': {e}")

if __name__ == '__main__':
    # This block is for local testing or manual execution.
    # Replace these with your actual Kusto cluster URI and database name.
    # In a real-world scenario, these would be passed via command-line arguments or environment variables.
    cluster_uri = "https://your-kusto-cluster.eastus.kusto.windows.net"
    database_name = "your-database-name"
    
    # You must be logged in via Azure CLI (`az login`) for this to work.
    setup_kusto_tables_and_policies(cluster_uri, database_name)
