import arxiv
import json
import logging
import sys
from pathlib import Path
from mcp.server.fastmcp import FastMCP, Context
from src.settings import settings

# Initialize Path object immediately
RESEARCH_DIR = Path(settings.research_dir)

mcp = FastMCP("research_server")

# Configure logging to stderr to avoid interfering with JSON-RPC on stdout
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


@mcp.tool()
async def search_papers(
    topic: str, max_results: int = 5, ctx: Context[None, None] = None
) -> list[str]:
    """Search for papers on arXiv based on a topic and store their information.
    Args:
        topic: The topic to search for
        max_results: Maximum number of results to retrieve (default: 5)
    Returns:
        List of paper IDs found in the search
    """

    await ctx.info(
        f"[Paper Searching] Searching for {max_results} papers on topic: {topic}"
    )
    await ctx.report_progress(50, 100, "Searching for papers")
    # Use arxiv to find the papers
    client = arxiv.Client()
    # Search for the most relevant articles matching the queried topic
    search = arxiv.Search(
        query=topic,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    papers = client.results(search)

    await ctx.info(f"[Paper Searching] Postprocessing papers for topic: {topic}")
    await ctx.report_progress(75, 100, "Postprocessing papers")
    # Create directory for this topic
    # Pathlib handles path joining with /
    topic_path = RESEARCH_DIR / topic.lower().replace(" ", "_")
    topic_path.mkdir(parents=True, exist_ok=True)

    file_path = topic_path / "papers_info.json"

    # Try to load existing papers info
    papers_info = {}
    if file_path.exists():
        try:
            with file_path.open(mode="r", encoding="utf-8") as json_file:
                papers_info = json.load(json_file)
        except json.JSONDecodeError:
            papers_info = {}

    # Process each paper and add to papers_info
    paper_ids = []
    for paper in papers:
        paper_ids.append(paper.get_short_id())
        paper_info = {
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "summary": paper.summary,
            "pdf_url": paper.pdf_url,
            "published": str(paper.published.date()),
        }
        papers_info[paper.get_short_id()] = paper_info

    await ctx.info(f"[Paper Searching] Saving papers for topic: {topic}")
    await ctx.report_progress(100, 100, f"Saving papers for topic: {topic}")
    # Save updated papers_info to json file
    with file_path.open(mode="w", encoding="utf-8") as json_file:
        json.dump(papers_info, json_file, indent=4, ensure_ascii=False)

    logging.info(f"Results are saved in: {file_path}")

    return paper_ids


@mcp.tool()
def extract_paper_content(paper_id: str) -> str:
    """Search for information about a specific paper across all topic directories.
    Args:
        paper_id: The ID of the paper to look for
    Returns:
        JSON string with paper information if found, error message if not found
    """
    if not RESEARCH_DIR.exists():
        return f"Research directory {RESEARCH_DIR} does not exist."

    # iterdir yields Path objects directly
    for topic_dir in RESEARCH_DIR.iterdir():
        if topic_dir.is_dir():
            file_path = topic_dir / "papers_info.json"
            if file_path.is_file():
                try:
                    with file_path.open(mode="r", encoding="utf-8") as json_file:
                        papers_info = json.load(json_file)
                        if paper_id in papers_info:
                            return json.dumps(
                                papers_info[paper_id], indent=4, ensure_ascii=False
                            )
                except (json.JSONDecodeError, OSError) as e:
                    logging.error(f"Error reading {file_path}: {str(e)}")
                    continue

    return f"There's no saved information related to paper {paper_id}."


# Directed Resource
@mcp.resource("papers://folders", mime_type="text/markdown")
def get_available_folders() -> str:
    """List all available topic folders in the papers directory. This resource provides a simple list of all available topic folders."""
    folders = []

    # Get all topic directories
    if RESEARCH_DIR.exists():
        for topic_dir in RESEARCH_DIR.iterdir():
            if topic_dir.is_dir():
                papers_file = topic_dir / "papers_info.json"
                if papers_file.exists():
                    folders.append(topic_dir.name)

    # Create a simple markdown list
    content = "# Available Topics\n\n"
    if folders:
        for folder in folders:
            content += f"- {folder}\n"
        content += f"\nUse @{folder} to access papers in that topic.\n"
    else:
        content += "No topics found.\n"

    return content


# Templated Resource
@mcp.resource("papers://{topic}", mime_type="text/markdown")
def get_topic_papers(topic: str) -> str:
    """Get detailed information about papers on a specific topic.
    Args:
        topic: The research topic to retrieve papers for
    """
    topic_dir_name = topic.lower().replace(" ", "_")
    papers_file = RESEARCH_DIR / topic_dir_name / "papers_info.json"

    if not papers_file.exists():
        return f"# No papers found for topic: {topic}\n\nTry searching for papers on this topic first."

    try:
        with papers_file.open(mode="r", encoding="utf-8") as f:
            papers_data = json.load(f)

        # Create markdown content with paper details
        content = f"# Papers on {topic.replace('_', ' ').title()}\n\n"
        content += f"Total papers: {len(papers_data)}\n\n"

        for paper_id, paper_info in papers_data.items():
            content += f"## {paper_info['title']}\n"
            content += f"- **Paper ID**: {paper_id}\n"
            content += f"- **Authors**: {', '.join(paper_info['authors'])}\n"
            content += f"- **Published**: {paper_info['published']}\n"
            content += (
                f"- **PDF URL**: [{paper_info['pdf_url']}]({paper_info['pdf_url']})\n\n"
            )
            content += f"### Summary\n{paper_info['summary'][:500]}...\n"
            content += "----------\n"

        return content
    except json.JSONDecodeError:
        return f"# Error reading papers data for {topic}\n\nThe papers data file is corrupted."


@mcp.prompt()
def generate_search_prompt(topic: str, num_papers: int = 5) -> str:
    """Generate a prompt for Claude to find and discuss academic papers on a specific topic."""
    return f"""Search for {num_papers} academic papers about '{topic}' using the search_papers tool. 

Follow these instructions:
1. First, search for papers using search_papers(topic='{topic}', max_results={num_papers})
2. For each paper found, extract and organize the following information:
   - Paper title
   - Authors
   - Publication date
   - Brief summary of the key findings
   - Main contributions or innovations
   - Methodologies used
   - Relevance to the topic '{topic}'

3. Provide a comprehensive summary that includes:
   - Overview of the current state of research in '{topic}'
   - Common themes and trends across the papers
   - Key research gaps or areas for future investigation
   - Most impactful or influential papers in this area

4. Organize your findings in a clear, structured format with headings and bullet points for easy readability.

Please present both detailed information about each paper and a high-level synthesis of the research landscape in {topic}."""


if __name__ == "__main__":
    mcp.run(transport="stdio")
