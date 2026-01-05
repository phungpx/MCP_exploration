# Architecture Documentation

This document provides a detailed technical overview of the MCP Research Agent architecture.

## Table of Contents
1. [System Overview](#system-overview)
2. [Component Details](#component-details)
3. [Data Flow](#data-flow)
4. [MCP Protocol Integration](#mcp-protocol-integration)
5. [Design Patterns](#design-patterns)
6. [Extension Points](#extension-points)

## System Overview

The MCP Research Agent is built on a modular architecture that separates concerns between:
- **Client Layer**: Manages MCP server connections and provides a unified interface
- **Agent Layer**: Orchestrates AI interactions and user interface
- **Server Layer**: Implements custom MCP servers with specialized capabilities

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                    (Rich CLI with Markdown)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Layer                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Pydantic AI Agent (agent.py)                   │  │
│  │  - Message history management                            │  │
│  │  - Streaming response handling                           │  │
│  │  - Command routing (/prompts, /resources, etc.)          │  │
│  │  - LLM integration (OpenAI compatible)                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Client Layer                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              MCPClient (client.py)                       │  │
│  │  - Multi-server management                               │  │
│  │  - Tool aggregation                                      │  │
│  │  - Prompt & resource discovery                           │  │
│  │  - Lifecycle management                                  │  │
│  └────────────┬──────────────┬──────────────┬────────────────┘  │
│               │              │              │                   │
│  ┌────────────┴─────┐ ┌──────┴──────┐ ┌────┴─────────────────┐ │
│  │   MCPServer      │ │ MCPServer   │ │   MCPServer         │ │
│  │   (research)     │ │ (filesystem)│ │   (fetch)           │ │
│  └──────────────────┘ └─────────────┘ └─────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Server Layer                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │     Custom MCP Server (research.py)                      │  │
│  │  - FastMCP framework                                     │  │
│  │  - Tools: search_papers, extract_info                    │  │
│  │  - Resources: papers://folders, papers://{topic}         │  │
│  │  - Prompts: generate_search_prompt                       │  │
│  │  - Storage: JSON-based paper database                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. MCPClient (`src/clients/client.py`)

**Purpose**: Manages connections to multiple MCP servers and provides a unified interface.

**Key Responsibilities**:
- Load server configurations from JSON
- Initialize and manage multiple MCP server connections
- Aggregate tools from all servers
- Discover and expose prompts and resources
- Handle cleanup and resource management

**Key Methods**:
```python
async def start() -> List[PydanticTool]
    # Initializes all servers and returns aggregated tools

async def get_prompt(prompt_key: str, arguments: dict) -> str
    # Retrieves and processes a prompt from a server

async def read_resource(resource_key: str) -> str
    # Reads a resource from a server

def list_available_prompts() -> List[str]
    # Lists all prompts from all servers

def list_available_resources() -> List[str]
    # Lists all resources from all servers

async def cleanup()
    # Properly closes all server connections
```

**Design Decisions**:
- Uses `AsyncExitStack` for proper async resource management
- Namespaces tools/prompts/resources with server name to avoid collisions
- Implements graceful error handling to prevent cascade failures

### 2. MCPServer (`src/clients/client.py`)

**Purpose**: Represents a single MCP server connection.

**Key Responsibilities**:
- Establish stdio-based communication with MCP server process
- Initialize MCP session
- Convert MCP tools to Pydantic AI tools
- List and provide access to prompts and resources
- Manage cleanup of server connection

**Key Methods**:
```python
async def initialize()
    # Starts server process and establishes session

async def create_pydantic_ai_tools() -> list[PydanticTool]
    # Converts MCP tools to Pydantic AI format

def create_tool_instance(tool: MCPTool) -> PydanticTool
    # Creates a Pydantic AI tool wrapper for an MCP tool

async def list_prompts() -> list[Any]
    # Retrieves available prompts

async def list_resources() -> list[Any]
    # Retrieves available resources

async def cleanup()
    # Closes server connection
```

**Tool Conversion Process**:
1. MCP tool is received with `inputSchema` (JSON Schema)
2. Pydantic AI tool is created with async execution wrapper
3. `prepare` hook sets the JSON schema for parameter validation
4. Tool is registered with Pydantic AI agent

### 3. Pydantic AI Agent (`src/clients/agent.py`)

**Purpose**: Provides the interactive chat interface and orchestrates AI interactions.

**Key Responsibilities**:
- Initialize MCP client and load tools
- Manage conversation history
- Handle user commands and special operations
- Stream AI responses with rich formatting
- Coordinate between user, LLM, and MCP tools

**Key Features**:
- **Streaming**: Real-time response streaming with markdown rendering
- **Command System**: Special commands for prompts/resources (e.g., `/prompts`)
- **Rich UI**: Beautiful terminal output using the Rich library
- **Message History**: Maintains context across conversation turns
- **Error Handling**: Graceful error reporting and recovery

**Command Flow**:
```python
User Input → Command Router → Handler → Response
                           ↓
                   Regular Query → Agent → LLM → Tools → Response
```

### 4. Research Server (`src/servers/research.py`)

**Purpose**: Custom MCP server for academic research capabilities.

**Key Responsibilities**:
- Search arXiv for academic papers
- Store and manage paper metadata
- Provide access to papers via resources
- Generate research prompts

**Architecture**:
```
Research Server
├── Tools
│   ├── search_papers(topic, max_results)
│   └── extract_info(paper_id)
├── Resources
│   ├── papers://folders
│   └── papers://{topic}
└── Prompts
    └── generate_search_prompt(topic, num_papers)

Data Storage
└── src/papers/
    └── {topic}/
        └── papers_info.json
```

**Data Schema**:
```json
{
  "paper_id": {
    "title": "Paper Title",
    "authors": ["Author 1", "Author 2"],
    "summary": "Abstract text...",
    "pdf_url": "https://arxiv.org/pdf/...",
    "published": "2024-01-01"
  }
}
```

## Data Flow

### Tool Execution Flow

```
1. User makes request → Agent receives input
2. Agent sends to LLM with available tools
3. LLM decides to use tool → Returns tool call
4. Agent routes tool call → MCPClient → Specific MCPServer
5. MCPServer executes tool → Returns result
6. Result sent to LLM → LLM generates response
7. Response streamed to user
```

### Resource Access Flow

```
1. User: /read-resource research/papers://folders
2. Agent extracts resource key → Calls mcp_client.read_resource()
3. MCPClient parses key → Identifies server (research)
4. Routes to MCPServer → Calls session.read_resource()
5. MCP protocol request → Research server processes
6. Returns resource content → Rendered to user
```

### Prompt Usage Flow

```
1. User: /use-prompt research/generate_search_prompt
2. Agent calls mcp_client.get_prompt()
3. MCPClient routes to research server
4. Server generates prompt with parameters
5. Prompt text returned → Displayed to user
6. User can copy and customize prompt
```

## MCP Protocol Integration

### Stdio Communication

The client communicates with MCP servers via stdio (standard input/output):

```python
# Server process started with stdio
server_params = StdioServerParameters(
    command="uv",
    args=["run", "src/servers/research.py"],
    env=None
)

# Stdio transport established
stdio_transport = stdio_client(server_params)
read, write = stdio_transport

# Client session created
session = ClientSession(read, write)
await session.initialize()
```

### Message Exchange

MCP uses JSON-RPC 2.0 for message exchange:

```json
// Tool call request
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "search_papers",
    "arguments": {
      "topic": "quantum computing",
      "max_results": 5
    }
  },
  "id": 1
}

// Tool call response
{
  "jsonrpc": "2.0",
  "result": {
    "content": ["2301.00001", "2301.00002", ...]
  },
  "id": 1
}
```

## Design Patterns

### 1. Adapter Pattern
- **Where**: `create_pydantic_ai_tools()` method
- **Purpose**: Converts MCP tools to Pydantic AI tools
- **Benefit**: Allows seamless integration between different frameworks

### 2. Facade Pattern
- **Where**: `MCPClient` class
- **Purpose**: Provides simple interface to complex MCP multi-server system
- **Benefit**: Hides complexity from agent layer

### 3. Strategy Pattern
- **Where**: Command handling in agent
- **Purpose**: Different handlers for different command types
- **Benefit**: Easy to add new commands

### 4. Resource Management Pattern
- **Where**: `AsyncExitStack` usage
- **Purpose**: Ensures proper cleanup of async resources
- **Benefit**: Prevents resource leaks

## Extension Points

### Adding New MCP Servers

1. **Update Configuration**:
```json
// server_config.json
{
  "mcpServers": {
    "myserver": {
      "command": "python",
      "args": ["src/servers/myserver.py"]
    }
  }
}
```

2. **Server Auto-Discovery**:
- Tools are automatically discovered via `list_tools()`
- Prompts via `list_prompts()`
- Resources via `list_resources()`

### Creating Custom Tools

```python
@mcp.tool()
def my_custom_tool(param1: str, param2: int) -> str:
    """Tool description for LLM"""
    # Implementation
    return result
```

### Creating Custom Resources

```python
@mcp.resource("myresource://{id}")
def my_resource(id: str) -> str:
    """Resource description"""
    # Generate resource content
    return content
```

### Creating Custom Prompts

```python
@mcp.prompt()
def my_prompt(param: str) -> str:
    """Prompt description"""
    return f"Generated prompt: {param}"
```

### Extending the Agent

Add new commands in `agent.py`:

```python
if user_input.startswith("/mycommand"):
    # Handle custom command
    result = await handle_my_command()
    print(result)
    continue
```

## Performance Considerations

1. **Concurrent Server Initialization**: Servers are initialized sequentially to avoid resource contention
2. **Streaming Responses**: Reduces perceived latency for long responses
3. **Lazy Resource Loading**: Resources loaded only when accessed
4. **Connection Pooling**: MCP sessions maintained for reuse

## Security Considerations

1. **Sandboxed Execution**: Each MCP server runs in its own process
2. **API Key Management**: Credentials stored in `.env` (not in repo)
3. **File Access Control**: Filesystem server scope defined in config
4. **Input Validation**: Pydantic models validate all inputs

## Testing Strategy

### Unit Tests
- Test individual components (MCPClient, MCPServer)
- Mock MCP protocol responses

### Integration Tests
- Test full flow from user input to tool execution
- Use test MCP servers

### End-to-End Tests
- Test with real MCP servers
- Validate complete workflows

## Future Enhancements

1. **Multi-Modal Support**: Add image and file handling
2. **Persistent Sessions**: Save and restore conversation history
3. **Server Health Monitoring**: Track server status and auto-restart
4. **Tool Composition**: Chain multiple tools automatically
5. **Resource Caching**: Cache frequently accessed resources
6. **Parallel Tool Execution**: Execute independent tools concurrently

---

**Last Updated**: January 2026
