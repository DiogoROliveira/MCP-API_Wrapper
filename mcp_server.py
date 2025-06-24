from mcp.server.fastmcp import FastMCP

# Inicializa o MCP
mcp = FastMCP("Fitness & Nutrition API", dependencies=["httpx"])

def initialize_tools():
    """Inicializa as ferramentas de forma lazy"""
    try:
        import nutritionix
        import wger
        import combined
        import resources
        print("Tools loaded successfully")
    except Exception as e:
        print(f"Error loading tools: {e}")

if __name__ == "__main__":
    initialize_tools()
    mcp.run()