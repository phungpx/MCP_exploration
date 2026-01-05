# Usage Examples

This document provides practical examples of using the MCP Research Agent for various tasks.

## Table of Contents
1. [Basic Research](#basic-research)
2. [Advanced Research Workflows](#advanced-research-workflows)
3. [File Operations](#file-operations)
4. [Web Content Fetching](#web-content-fetching)
5. [Using Prompts and Resources](#using-prompts-and-resources)
6. [Programmatic Usage](#programmatic-usage)

## Basic Research

### Example 1: Simple Paper Search

```
[You] Search for 5 papers on transformer neural networks

[Assistant] I'll search for papers on transformer neural networks...
*Uses search_papers tool*

I found 5 papers on transformer neural networks:
1. "Attention Is All You Need" (2017.00001)
2. "BERT: Pre-training of Deep Bidirectional Transformers..." (2018.00234)
...
```

### Example 2: Get Paper Details

```
[You] Tell me more about paper 2017.00001

[Assistant] *Uses extract_info tool*

Here are the details for paper 2017.00001:

**Title**: Attention Is All You Need
**Authors**: Vaswani et al.
**Published**: 2017-06-12
**Summary**: This paper introduces the Transformer architecture...
**PDF**: https://arxiv.org/pdf/2017.00001.pdf
```

### Example 3: Comparative Analysis

```
[You] Search for papers on "attention mechanisms" and "self-attention" and compare their approaches

[Assistant] *Searches both topics and analyzes*

I've found papers on both topics. Here's a comparison:

**Attention Mechanisms (5 papers found)**
- Focus on general attention concepts...

**Self-Attention (5 papers found)**  
- Specific to self-referential attention...

**Key Differences**:
1. Scope: ...
2. Applications: ...
```

## Advanced Research Workflows

### Example 4: Literature Review

```
[You] I need to do a literature review on "federated learning". 
Search for 10 papers, organize them by year, and summarize the key trends.

[Assistant] *Performs comprehensive search and analysis*

# Literature Review: Federated Learning

## Overview
I found 10 papers spanning 2019-2024...

## Papers by Year

### 2024 (2 papers)
1. **Title**: Recent Advances in Federated Learning
   - Key contribution: ...
   
### 2023 (3 papers)
...

## Key Trends
1. Privacy-preserving techniques...
2. Communication efficiency...
3. Non-IID data handling...

## Research Gaps
...
```

### Example 5: Using Research Prompts

```
[You] /use-prompt research/generate_search_prompt

📝 Prompt 'research/generate_search_prompt':

Search for 5 academic papers about 'transformers' using the search_papers tool.

Follow these instructions:
1. First, search for papers using search_papers(topic='transformers', max_results=5)
2. For each paper found, extract and organize...
...

[You] *Copy and customize the prompt*
Search for 5 academic papers about 'quantum computing' using the search_papers tool...

[Assistant] *Follows the detailed prompt structure*
```

### Example 6: Topic Deep Dive

```
[You] I want to deeply understand vision transformers. 
Search for papers, read them, and create a comprehensive guide covering:
1. Core concepts
2. Key innovations
3. Practical applications
4. Implementation challenges

[Assistant] *Multi-step research process*

I'll help you create a comprehensive guide on vision transformers.

Step 1: Searching for papers...
*Uses search_papers*

Step 2: Analyzing papers...
*Uses extract_info multiple times*

Step 3: Creating comprehensive guide...
*Writes detailed guide to file*

# Vision Transformers: A Comprehensive Guide
...
```

## File Operations

### Example 7: Save Research Notes

```
[You] Save a summary of the transformer papers to ./research/transformers_summary.md

[Assistant] *Uses filesystem write_file tool*

I've created a summary and saved it to ./research/transformers_summary.md

Summary includes:
- Overview of 5 papers
- Key concepts and innovations
- Timeline of developments
- References with links

Would you like me to add anything else to the summary?
```

### Example 8: Read and Analyze Files

```
[You] Read the file ./data/research_questions.txt and help me find papers that address each question

[Assistant] *Uses read_file tool*

I've read your research questions. Let me search for papers addressing each:

**Question 1**: "How do transformers handle long sequences?"
*Searches and provides papers*

**Question 2**: "What are efficient alternatives to attention?"
*Searches and provides papers*
...
```

### Example 9: Organize Research

```
[You] Create a folder structure for my research on "neural architecture search" with:
- papers/
- notes/
- code_examples/
- results/

Then create a README.md in each folder explaining its purpose.

[Assistant] *Uses filesystem tools to create structure*

I've created the folder structure:

📁 neural_architecture_search/
  📁 papers/ - README.md created
  📁 notes/ - README.md created  
  📁 code_examples/ - README.md created
  📁 results/ - README.md created

Each README explains the folder's purpose and suggested organization.
```

## Web Content Fetching

### Example 10: Fetch Paper Abstract

```
[You] Fetch the content from https://arxiv.org/abs/1706.03762 and summarize it

[Assistant] *Uses fetch tool*

I've fetched the paper "Attention Is All You Need" from arXiv.

**Summary**: This landmark paper introduces the Transformer architecture...

**Key Points**:
- Eliminates recurrence in sequence modeling
- Uses only attention mechanisms
- Achieves state-of-the-art results on translation
...
```

### Example 11: Research from Blog Posts

```
[You] Fetch content from https://ai.googleblog.com/2021/01/reformer-efficient-transformer.html 
and search for related papers

[Assistant] *Fetches blog content, then searches papers*

Based on the blog post about Reformer, I found 5 related papers:
1. "Reformer: The Efficient Transformer" (original paper)
2. "Linformer: Self-Attention with Linear Complexity"
...

Would you like me to compare these approaches?
```

## Using Prompts and Resources

### Example 12: List Available Research Topics

```
[You] /read-resource research/papers://folders

📚 Resource 'research/papers://folders':

# Available Topics

- quantum_computing
- transformer_architectures  
- federated_learning
- neural_architecture_search

Use @quantum_computing to access papers in that topic.
```

### Example 13: Access Topic Papers

```
[You] /read-resource research/papers://quantum_computing

📚 Resource 'research/papers://quantum_computing':

# Papers on Quantum Computing

Total papers: 5

## Quantum Machine Learning: What Quantum Computing Means to Data Mining
- **Paper ID**: 2301.00001
- **Authors**: Smith, J., et al.
- **Published**: 2023-01-01
- **PDF URL**: https://arxiv.org/pdf/2301.00001.pdf

### Summary
This paper explores the intersection of quantum computing...

---

## [Next paper...]
```

### Example 14: Workflow with Resources

```
[You] Show me all my research topics, then give me a detailed summary 
of papers in the "transformer_architectures" topic

[Assistant] 
*Reads papers://folders resource*

You have 4 research topics:
1. quantum_computing (5 papers)
2. transformer_architectures (8 papers)
3. federated_learning (3 papers)
4. neural_architecture_search (6 papers)

*Reads papers://transformer_architectures resource*

Here's a detailed summary of the 8 papers in transformer_architectures:

# Transformer Architectures Research Summary

## Foundational Papers
1. "Attention Is All You Need" - The original transformer...
...
```

## Programmatic Usage

### Example 15: Using MCP Client in Your Code

```python
# examples/custom_research.py
import asyncio
from src.clients.client import MCPClient

async def main():
    # Initialize client
    client = MCPClient()
    client.load_servers("server_config.json")
    tools = await client.start()
    
    print(f"Loaded {len(tools)} tools")
    
    # List prompts
    prompts = client.list_available_prompts()
    print(f"Available prompts: {prompts}")
    
    # Get a prompt
    prompt = await client.get_prompt(
        "research/generate_search_prompt",
        arguments={"topic": "quantum computing", "num_papers": 5}
    )
    print(f"Prompt: {prompt}")
    
    # List resources
    resources = client.list_available_resources()
    print(f"Available resources: {resources}")
    
    # Read a resource
    folders = await client.read_resource("research/papers://folders")
    print(f"Research folders:\n{folders}")
    
    # Cleanup
    await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 16: Custom Agent with MCP

```python
# examples/custom_agent.py
import asyncio
from pydantic_ai import Agent
from src.clients.client import MCPClient
from src.clients.agent import get_model

async def research_workflow(topic: str):
    """Custom research workflow."""
    # Setup
    client = MCPClient()
    client.load_servers("server_config.json")
    tools = await client.start()
    
    agent = Agent(model=get_model(), tools=tools)
    
    # Research workflow
    tasks = [
        f"Search for 10 papers on {topic}",
        f"Summarize the key themes in {topic} research",
        f"Identify research gaps in {topic}",
        f"Write findings to ./research/{topic}_analysis.md"
    ]
    
    results = []
    for task in tasks:
        print(f"\n📝 Task: {task}")
        result = await agent.run(task)
        results.append(result.data)
        print(f"✅ Completed: {task[:50]}...")
    
    # Cleanup
    await client.cleanup()
    return results

async def main():
    topic = "vision transformers"
    results = await research_workflow(topic)
    print(f"\n🎉 Research workflow completed for '{topic}'")
    print(f"Generated {len(results)} outputs")

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 17: Batch Processing

```python
# examples/batch_research.py
import asyncio
from src.clients.agent import get_pydantic_ai_agent

async def batch_search(topics: list[str]):
    """Search multiple topics in batch."""
    client, agent = await get_pydantic_ai_agent()
    
    try:
        for i, topic in enumerate(topics, 1):
            print(f"\n[{i}/{len(topics)}] Researching: {topic}")
            
            result = await agent.run(
                f"Search for 5 papers on '{topic}' and save summary to ./research/{topic}.md"
            )
            
            print(f"✅ Completed: {topic}")
            
    finally:
        await client.cleanup()

async def main():
    topics = [
        "quantum computing",
        "federated learning",
        "neural architecture search",
        "vision transformers"
    ]
    
    await batch_search(topics)
    print("\n🎉 Batch research completed!")

if __name__ == "__main__":
    asyncio.run(main())
```

## Real-World Scenarios

### Scenario 1: PhD Literature Review

```
Goal: Comprehensive literature review for thesis on "privacy-preserving machine learning"

Commands:
1. Search for 20 papers on "privacy-preserving machine learning"
2. /read-resource research/papers://privacy_preserving_machine_learning
3. Organize papers by approach: differential privacy, federated learning, secure multi-party computation
4. Create comparison table and save to ./thesis/literature_review.md
5. Generate bibliography in BibTeX format
```

### Scenario 2: Research Paper Writing

```
Goal: Write a related work section for paper on attention mechanisms

Commands:
1. Search for 15 papers on "attention mechanisms in neural networks"
2. Extract key innovations from each paper
3. Group papers by year to show evolution
4. Write a 2-page related work section highlighting:
   - Historical development
   - Key innovations
   - Current state-of-the-art
5. Save to ./paper/related_work.tex
```

### Scenario 3: Conference Preparation

```
Goal: Prepare for presenting at a conference on transformers

Commands:
1. Search for latest papers (2023-2024) on transformer architectures
2. Identify trending topics and innovations
3. Find papers citing my work (by author name)
4. Prepare talking points about current directions
5. Generate FAQ based on common questions in papers
```

## Tips and Tricks

### Tip 1: Chaining Operations
Instead of multiple commands, chain them:
```
Search for papers on X, then for each paper, extract key findings 
and save all to ./research/X_findings.md
```

### Tip 2: Using Context
The agent maintains context:
```
[You] Search for papers on quantum computing
[Assistant] *Finds papers*

[You] Now compare the first and third papers
[Assistant] *Compares without needing IDs*
```

### Tip 3: Structured Output
Request specific formats:
```
Search for papers on X and create a markdown table with:
| Title | Authors | Year | Key Contribution |
```

### Tip 4: Iterative Refinement
```
[You] Search for papers on GANs
[Assistant] *Searches*

[You] Focus only on papers from 2020 onwards
[Assistant] *Refines results*

[You] Now only show papers about image generation
[Assistant] *Further refines*
```

---

**More examples coming soon! Contribute your examples via PR.**

