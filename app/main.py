"""
weather-mcp-server
FastAPI application exposing an MCP endpoint over Streamable HTTP.
Transport: POST /mcp  (MCP Streamable HTTP — stateless, Cloud Run-friendly)
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from mcp.server import Server
from mcp.server.streamable_http import StreamableHTTPServerTransport

from app.tools import register_tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MCP server setup
# ---------------------------------------------------------------------------

mcp_server = Server("weather-mcp-server")
register_tools(mcp_server)


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("weather-mcp-server starting up!")
    yield
    logger.info("weather-mcp-server shutting down!")


app = FastAPI(
    title="Weather MCP Server",
    description="Open-Meteo MCP server over Streamable HTTP",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict:
    """Health-check endpoint for Cloud Run."""
    return {"status": "ok", "service": "weather-mcp-server"}


@app.post("/mcp")
async def mcp_endpoint(request_body: dict):
    """
    MCP Streamable HTTP endpoint.
    Accepts JSON-RPC 2.0 messages and returns MCP responses.
    """
    transport = StreamableHTTPServerTransport()
    response = await transport.handle_request(mcp_server, request_body)
    return response
