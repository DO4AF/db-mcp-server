# server_instance.py
"""
MCP server instance - shared across modules
"""

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from config import ALLOWED_HOSTS

# Create the MCP server instance
mcp = FastMCP(
    "deutschebahn_mcp_server",
    instructions="A server providing tools to access Deutsche Bahn (DB) and related mobility APIs for train schedules, station information, and parking.",
    transport_security=TransportSecuritySettings(
        allowed_hosts=[
            value
            for host in ALLOWED_HOSTS
            for value in (host, f"{host}:*")
        ],
        allowed_origins=["https://claude.ai"] + [
            value
            for host in ALLOWED_HOSTS
            for scheme in ("http", "https")
            for value in (f"{scheme}://{host}", f"{scheme}://{host}:*")
        ],
    ),
)