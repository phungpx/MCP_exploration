# MCP Message Format

All MCP communication happens through JSON messages. Each message type serves a specific purpose - whether it's calling a tool, listing available resources, or sending notifications about system events.


# MCP Specification

The message types are written in `TypeScript` for convenience - not because they're executed as TypeScript code, but because `TypeScript provides a clear way to describe data structures and types`.

# Notification Messages
These are one-way messages that inform about events but don't require a response:

- Progress Notification - Updates on long-running operations
- Logging Message Notification - System log messages
- Tool List Changed Notification - When available tools change
- Resource Updated Notification - When resources are modified
