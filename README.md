# MCP Research Agent

A powerful research assistant built with the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) and [Pydantic AI](https://ai.pydantic.dev/). This project demonstrates how to integrate multiple MCP servers with an AI agent to create an intelligent research tool that can search academic papers, access file systems, and fetch web content.


## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Pydantic AI Agent                       │
│                    (with OpenAI/LLM)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Tools, Prompts, Resources
                       │
┌──────────────────────┴──────────────────────────────────────┐
│                      MCP Client                             │
│  (manages multiple MCP servers and provides unified access) │
└───────┬──────────────────┬─────────────────┬────────────────┘
        │                  │                 │
        │                  │                 │
┌───────┴────────┐ ┌───────┴────────┐ ┌──────┴─────────┐
│   Research     │ │   Filesystem   │ │     Fetch      │
│     Server     │ │     Server     │ │     Server     │
│   (Custom)     │ │    (MCP npm)   │ │   (MCP pip)    │
└────────────────┘ └────────────────┘ └────────────────┘
```

### Key Components

1. **MCP Client** (`src/clients/client.py`): Manages connections to multiple MCP servers and provides a unified interface for tools, prompts, and resources
2. **Pydantic AI Agent** (`src/clients/agent.py`): Interactive chat agent that uses MCP tools to perform research and other tasks
3. **Research Server** (`src/servers/research.py`): Custom MCP server for searching and managing academic papers from arXiv

## 📦 Installation

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js and npm (for filesystem server)

### Setup

1. **Clone the repository**:
```bash
git clone https://github.com/phungpx/MCP_exploration.git
cd MCP_exploration
```

2. **Install dependencies using uv**:
```bash
uv sync
```

3. **Create a `.env` file** with your LLM configuration:
```bash
LLM_MODEL=gemini-2.5-flash
LLM_API_KEY=
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/

LANGFUSE_SECRET_KEY=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_BASE_URL=
```

## ⚙️ Configuration

### MCP Servers Configuration

Edit `server_config.json` to configure your MCP servers:

```json
{
    "mcpServers": {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
        },
        "research": {
            "command": "uv",
            "args": ["run", "src/servers/research.py"],
            "cwd": "."
        },
        "fetch": {
            "command": "uvx",
            "args": ["mcp-server-fetch"]
        }
    }
}
```

### MCP Inspector

1. research servers

```bash
npx @modelcontextprotocol/inspector python -m src.servers.research
```

2. [`fetch` server](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch)

```bash
npx @modelcontextprotocol/inspector uvx mcp-server-fetch
```

3. [`file system` server](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)

```bash
npx @modelcontextprotocol/inspector npx -y @modelcontextprotocol/server-filesystem <directory-path>
```

4. [`git` server](https://github.com/modelcontextprotocol/servers/tree/main/src/git)

```bash
npx @modelcontextprotocol/inspector uvx mcp-server-git --repository .git
```

5. [`time` server](https://github.com/modelcontextprotocol/servers/tree/main/src/time)

```bash
npx @modelcontextprotocol/inspector uvx mcp-server-time
```

### Settings

Application settings are managed through `src/settings.py` using Pydantic Settings:

- **LLM Settings**: Model name, API key, base URL, temperature, max tokens
- **Research Directory**: Where to store downloaded papers

## 📁 Project Structure

```
MCP_exploration/
├── main.py                      # CLI entry point
├── pyproject.toml               # Project dependencies
├── server_config.json           # MCP servers configuration
├── .env                         # Environment variables (not in repo)
├── README.md                    # This file
├── docs/
│   ├── ARCHITECTURE.md          # Technical architecture
│   └── EXAMPLES.md              # Usage examples
├── tests/
│   └── test_api.py              # API tests
└── src/
    ├── client.py                # MCP client implementation
    └── agent.py                 # Pydantic AI agent with CLI
    ├── servers/
    │   └── research.py          # Custom research MCP server
    ├── papers/                  # Research papers storage
    └── settings.py              # Application settings
```

## 🚀 Usage

Run the interactive research agent:

```bash
uv run main.py
# or
uv run python main.py
# or directly
uv run src/clients/agent.py
```

### Interactive Commands

Once the agent starts, you'll see available prompts and resources. Use these commands:

#### General Commands
- `exit`, `quit`, `bye`, `goodbye` - Exit the chat

#### MCP-Specific Commands
- `/prompts` - List all available prompts with descriptions
- `/resources` - List all available resources with descriptions
- `/use-prompt <key>` - Display a specific prompt
- `/read-resource <key>` - Read and display a specific resource

#### Example Session

```
=== MCP Client Started ===

📝 Available Prompts: 1
  - research/generate_search_prompt

📚 Available Resources: 2
  - research/papers://folders
  - research/papers://{topic}

💡 Commands:
  /prompts - List all available prompts
  /resources - List all available resources
  /use-prompt <key> - Use a specific prompt
  /read-resource <key> - Read a specific resource
  exit/quit - Exit the chat
==================================================

[You] Search for recent papers on quantum computing

[Assistant] I'll search for recent papers on quantum computing...
[Agent uses search_papers tool and provides results]

[You] /read-resource research/papers://folders

📚 Resource 'research/papers://folders':
# Available Topics
- quantum_computing
- machine_learning

Use @quantum_computing to access papers in that topic.
```

## 🛠️ MCP Servers

### 1. Research Server (Custom)

Located at `src/servers/research.py` - A custom MCP server for academic research.

#### Tools
- **`search_papers(topic, max_results)`**: Search arXiv for papers on a topic
- **`extract_info(paper_id)`**: Get detailed information about a specific paper

#### Resources
- **`papers://folders`**: List all available research topic folders
- **`papers://{topic}`**: Get all papers for a specific topic with full details

#### Prompts
- **`generate_search_prompt(topic, num_papers)`**: Generate a comprehensive research prompt for Claude

### 2. Filesystem Server (MCP Official)

Provides file system access capabilities.

#### Tools
- `read_file(path)`: Read file contents
- `write_file(path, content)`: Write content to a file
- `list_directory(path)`: List directory contents
- And more...

### 3. Fetch Server (MCP Official)

Fetches content from the web.

#### Tools
- `fetch(url)`: Fetch content from a URL
- And more...

## 🔧 Development

### Creating Custom MCP Servers

You can create custom MCP servers using FastMCP:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my_server")

@mcp.tool()
def my_tool(param: str) -> str:
    """Tool description"""
    return f"Result: {param}"

@mcp.resource("myresource://{id}")
def my_resource(id: str) -> str:
    """Resource description"""
    return f"Resource content for {id}"

@mcp.prompt()
def my_prompt(param: str) -> str:
    """Prompt description"""
    return f"Generated prompt with {param}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### Adding New MCP Servers

1. Add server configuration to `server_config.json`
2. The client will automatically discover tools, prompts, and resources
3. Restart the agent to load the new server
