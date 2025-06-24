from mcp.server.fastmcp import FastMCP

# Inicializa o MCP
mcp = FastMCP("Fitness & Nutrition API", dependencies=["httpx"])

from nutritionix import *
from wger import *
from combined import *
from resources import *

if __name__ == "__main__":
    mcp.run()