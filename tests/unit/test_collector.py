import pytest
import asyncio
from unittest.mock import AsyncMock
from aiohttp import web
from data_collector.collector import EthereumCollector

@pytest.mark.asyncio
async def test_fetch_ethereum_price_success(aiohttp_client, monkeypatch):
    """
    Tests that the collector can successfully fetch Ethereum price from a mocked API.
    """
    # Mock the aiohttp server
    async def handler(request):
        data = {"result": "100"}
        return web.json_response(data)

    app = web.Application()
    app.router.add_get("/", handler)
    client = await aiohttp_client(app)

    # Mock the Event Hub client
    mock_event_hub_client = AsyncMock()
    monkeypatch.setattr("azure.eventhub.aio.EventHubProducerClient", AsyncMock(return_value=mock_event_hub_client))
    
    collector = EthereumCollector(
        api_url=str(client.server.make_url('/')),
        eventhub_conn_str="",
        eventhub_name=""
    )

    # Run the test
    await collector.fetch_ethereum_price()

    # Assertions
    # Check if the event was sent to Event Hub
    mock_event_hub_client.send_batch.assert_called_once()
    
    # Assert that the correct data was processed
    args, kwargs = mock_event_hub_client.send_batch.call_args
    batch = args[0]
    assert len(batch) == 1
    assert "100" in batch[0].body_as_str()

@pytest.mark.asyncio
async def test_fetch_ethereum_price_failure(aiohttp_client, monkeypatch):
    """
    Tests that the collector handles API failures gracefully.
    """
    # Mock a failed API response
    async def handler(request):
        return web.Response(status=500, text="Internal Server Error")
        
    app = web.Application()
    app.router.add_get("/", handler)
    client = await aiohttp_client(app)

    # Mock the Event Hub client
    mock_event_hub_client = AsyncMock()
    monkeypatch.setattr("azure.eventhub.aio.EventHubProducerClient", AsyncMock(return_value=mock_event_hub_client))

    collector = EthereumCollector(
        api_url=str(client.server.make_url('/')),
        eventhub_conn_str="",
        eventhub_name=""
    )

    # Run the test and assert it raises an exception or handles the error
    with pytest.raises(Exception):
        await collector.fetch_ethereum_price()
    
    # Assert that no event was sent to Event Hub on failure
    mock_event_hub_client.send_batch.assert_not_called()
