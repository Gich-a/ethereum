# This is the main Terraform configuration file for your project.
# It defines the Azure resources required for the Ethereum dashboard.

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    azapi = {
      source  = "azure/azapi"
      version = "~> 1.0"
    }
  }
}

# Configure the Azure Provider
provider "azurerm" {
  features {}
}

# Create a resource group
resource "azurerm_resource_group" "rg" {
  name     = "rg-ethereum-dashboard"
  location = var.location
}

# Create an Event Hubs Namespace
resource "azurerm_eventhub_namespace" "eventhub_namespace" {
  name                = "evhns-${var.project_name}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "Standard"
}

# Create a dedicated Event Hub for Ethereum data
resource "azurerm_eventhub" "eth_eventhub" {
  name                = "eth-eventhub"
  namespace_name      = azurerm_eventhub_namespace.eventhub_namespace.name
  resource_group_name = azurerm_resource_group.rg.name
  partition_count     = 2
  message_retention_in_days = 1
}

# Create an Azure Data Explorer Cluster (Kusto DB)
resource "azurerm_kusto_cluster" "kusto_cluster" {
  name                = "kusto-cluster-${var.project_name}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku {
    name     = "Standard_D11_v2"
    capacity = 2
  }
}

# Create a Kusto database
resource "azurerm_kusto_database" "kusto_db" {
  name                = "ethereum_events_db"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_kusto_cluster.kusto_cluster.location
  cluster_name        = azurerm_kusto_cluster.kusto_cluster.name
  hot_cache_period    = "P7D"
}

# Create an Azure Data Lake Storage Gen2 Account
resource "azurerm_storage_account" "lakehouse_storage" {
  name                     = "dls${var.project_name}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  is_hns_enabled           = true
}

# Create a container within the Data Lake account
resource "azurerm_storage_container" "lakehouse_container" {
  name                  = "lakehouse"
  storage_account_name  = azurerm_storage_account.lakehouse_storage.name
}
