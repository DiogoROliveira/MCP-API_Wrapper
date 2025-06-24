from mcp.server.fastmcp import FastMCP

# Inicializa o MCP
mcp = FastMCP("Fitness & Nutrition API", dependencies=["httpx"])

# Importa e regista as ferramentas
from server.nutritionix import *
from server.wger import *
from server.combined import *
from server.resources import *

if __name__ == "__main__":
    mcp.run()