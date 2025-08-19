# This file defines the input variables for the Terraform configuration.

variable "project_name" {
  description = "A unique name for the project, used to create resource names."
  type        = string
  default     = "ethereumdashboard"
}

variable "location" {
  description = "The Azure region to deploy resources in."
  type        = string
  default     = "eastus"
}
