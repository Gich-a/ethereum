# This file defines the output values that are displayed after a 'terraform apply'.
# These values are essential for connecting other services and applications to the
# resources provisioned by this Terraform configuration.

# Output the Resource Group name
output "resource_group_name" {
  description = "The name of the created resource group."
  value       = azurerm_resource_group.rg.name
}

# Output the Event Hubs connection string
output "eventhub_namespace_connection_string" {
  description = "The primary connection string for the Event Hubs Namespace."
  value       = azurerm_eventhub_namespace.eventhub_namespace.default_primary_connection_string
  sensitive   = true
}

# Output the Event Hub name
output "eventhub_name" {
  description = "The name of the dedicated Event Hub for Ethereum data."
  value       = azurerm_eventhub.eth_eventhub.name
}

# Output the Azure Data Explorer (Kusto) cluster URI
output "kusto_cluster_uri" {
  description = "The URI of the Kusto cluster to use with clients."
  value       = azurerm_kusto_cluster.kusto_cluster.uri
}

# Output the Kusto database name
output "kusto_database_name" {
  description = "The name of the Kusto database."
  value       = azurerm_kusto_database.kusto_db.name
}

# Output the Data Lake Storage account name
output "lakehouse_storage_account_name" {
  description = "The name of the Data Lake Storage Gen2 account."
  value       = azurerm_storage_account.lakehouse_storage.name
}

# Output the Data Lake container name
output "lakehouse_container_name" {
  description = "The name of the container within the Lakehouse storage account."
  value       = azurerm_storage_container.lakehouse_container.name
}
