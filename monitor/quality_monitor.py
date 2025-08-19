import logging
from azure.kusto.data import KustoClient
from azure.kusto.ingest import KustoIngestClient, IngestionProperties
from datetime import datetime, timedelta

# Assuming a Kusto client is set up elsewhere, this script will be imported
# The following is a placeholder for demonstration.
kusto_client = None

def run_quality_checks():
    """Execute all data quality checks."""
    logging.info("Starting data quality checks.")
    results = []
    
    try:
        results.append(check_data_freshness())
        results.append(check_data_completeness())
        results.extend(check_data_consistency())
        
        return results
    except Exception as e:
        logging.error(f"Error during quality checks: {str(e)}")
        return [{"check": "quality_monitor", "status": "ERROR", "message": str(e)}]

def check_data_freshness():
    """
    Checks if the data is fresh enough (e.g., within the last 5 minutes).
    """
    query = "EthereumEvents | top 1 by Timestamp desc"
    try:
        response = kusto_client.execute(query)
        latest_timestamp = response.primary_results[0][0]["Timestamp"]
        
        minutes_old = (datetime.utcnow() - latest_timestamp).total_seconds() / 60
        status = "PASS" if minutes_old <= 5 else "FAIL"
        
        return {
            "check": "freshness",
            "status": status,
            "message": f"Data is {minutes_old:.2f} minutes old."
        }
    except Exception as e:
        logging.error(f"Freshness check failed: {str(e)}")
        return {"check": "freshness", "status": "ERROR", "message": str(e)}

def check_data_completeness():
    """
    Checks for missing records over the last hour.
    """
    query = """
    let expected_count = 60 / 15; // Assuming 1 price event every 15 minutes
    EthereumEvents
    | where EventType == "EthereumPrice" and Timestamp > ago(1h)
    | summarize actual_count = count()
    """
    try:
        response = kusto_client.execute(query)
        actual_count = response.primary_results[0][0]["actual_count"]
        
        status = "PASS" if actual_count >= 1 else "FAIL" # Simplified check
        
        return {
            "check": "completeness",
            "status": status,
            "message": f"Expected at least 1 price record in the last hour, found {actual_count}."
        }
    except Exception as e:
        logging.error(f"Completeness check failed: {str(e)}")
        return {"check": "completeness", "status": "ERROR", "message": str(e)}

def check_data_consistency():
    """
    Checks for any sudden, significant price changes.
    """
    query = """
    EthereumPrices
    | where Timestamp > ago(15m)
    | order by Timestamp desc
    | serialize
    | extend price_change = Price - prev(Price, 1)
    | where abs(price_change) > Price * 0.1 // Check for >10% change
    | project Timestamp, Price, price_change
    """
    try:
        response = kusto_client.execute(query)
        anomalies = [row for row in response.primary_results[0]]
        
        status = "PASS" if not anomalies else "FAIL"
        
        return {
            "check": "consistency",
            "status": status,
            "message": f"Found {len(anomalies)} price anomalies in the last 15 minutes."
        }
    except Exception as e:
        logging.error(f"Consistency check failed: {str(e)}")
        return {"check": "consistency", "status": "ERROR", "message": str(e)}
