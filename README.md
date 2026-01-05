# MCP Research Agent

A powerful research assistant built with the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) and [Pydantic AI](https://ai.pydantic.dev/). This project demonstrates how to integrate multiple MCP servers with an AI agent to create an intelligent research tool that can search academic papers, access file systems, and fetch web content.

## 🌟 Features

### Core Features
- **Multi-Server MCP Integration**: Connect to multiple MCP servers simultaneously
- **Research Capabilities**: Search and analyze academic papers from arXiv
- **File System Access**: Read and write files through MCP filesystem server
- **Web Fetching**: Retrieve content from the web using MCP fetch server
- **Prompts & Resources**: Leverage MCP prompts and resources for enhanced workflows
- **Conversation History**: Maintains context across multiple interactions

### Interfaces
- **Rich CLI Interface**: Beautiful terminal interface with markdown rendering and streaming responses
- **REST API**: Complete REST API for programmatic access
- **WebSocket API**: Real-time streaming responses via WebSocket
- **Session Management**: Maintain conversation context across requests

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
git clone <your-repo-url>
cd MCP_exploration
```

2. **Install dependencies using uv**:
```bash
uv sync
```

3. **Create a `.env` file** with your LLM configuration:
```bash
# LLM Configuration
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=your-api-key-here
LLM_BASE_URL=https://api.openai.com/v1  # Optional, for custom endpoints
LLM_TEMPERATURE=0.0
LLM_MAX_TOKENS=16384

# Research Directory
RESEARCH_DIR=src/papers
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

### Option 1: CLI Interface

Run the interactive research agent:

```bash
uv run main.py
# or
uv run python main.py
# or directly
uv run src/clients/agent.py
```

### Option 2: REST/WebSocket API

Start the API server:

```bash
# Using the convenience script
python scripts/start_api.py

# Or using uvicorn directly
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

Then access:
- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Quick test:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

See [API Documentation](README_API.md) for complete API reference.

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

## 💡 Use Cases

### Academic Research
```
Search for 5 papers on transformer architectures and summarize their key contributions
```

### Research with Resources
```
/read-resource research/papers://folders
Tell me more about the papers in the machine_learning folder
```

### Using Prompts
```
/use-prompt research/generate_search_prompt
```
Then copy the prompt and customize it for your research needs.

### File Operations
```
Read the file at ./data/notes.txt and summarize it
Write these research findings to ./results/summary.md
```

### Web Research
```
Fetch the content from https://arxiv.org/abs/2301.00001 and summarize it
```

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

## 📚 Key Dependencies

- **[mcp](https://pypi.org/project/mcp/)**: Model Context Protocol SDK
- **[pydantic-ai](https://ai.pydantic.dev/)**: Type-safe AI agent framework
- **[arxiv](https://pypi.org/project/arxiv/)**: Python wrapper for arXiv API
- **[rich](https://rich.readthedocs.io/)**: Beautiful terminal formatting
- **[openai](https://platform.openai.com/docs/)**: OpenAI API client
- **[pydantic](https://docs.pydantic.dev/)**: Data validation and settings

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📚 Additional Documentation

### General
- **[EXAMPLES.md](docs/EXAMPLES.md)** - Practical usage examples and real-world scenarios
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Detailed technical architecture and design patterns

### Examples
- **CLI**: Run `uv run src/agent.py`

## 🔌 API Endpoints

Quick reference for the REST API:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check and system info |
| `/chat` | POST | Send message and get response |
| `/ws/chat/{session_id}` | WebSocket | Streaming chat |
| `/prompts` | GET | List available prompts |
| `/prompts/get` | POST | Get specific prompt |
| `/resources` | GET | List available resources |
| `/resources/{key}` | GET | Read resource content |
| `/sessions` | GET | List active sessions |
| `/sessions/{id}` | DELETE | Delete session |

See [API Documentation](README_API.md) for details.
