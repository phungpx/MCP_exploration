import arxiv
import json
import logging
from pathlib import Path
from src.settings import settings

RESEARCH_DIR = Path(settings.research_dir)


def search_papers(topic: str, max_results: int = 5) -> list[str]:
    """Search for papers on arXiv based on a topic and store their information.
    Args:
        topic: The topic to search for
        max_results: Maximum number of results to retrieve (default: 5)
    Returns:
        List of paper IDs found in the search
    """

    # Use arxiv to find the papers
    client = arxiv.Client()

    # Search for the most relevant articles matching the queried topic
    search = arxiv.Search(
        query=topic,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    papers = client.results(search)

    # Create directory for this topic
    # Pathlib handles path joining with /
    topic_path = RESEARCH_DIR / topic.lower().replace(" ", "_")
    topic_path.mkdir(parents=True, exist_ok=True)

    file_path = topic_path / "papers_info.json"

    # Try to load existing papers info
    papers_info = {}
    if file_path.exists():
        try:
            with file_path.open("r", encoding="utf-8") as json_file:
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

    # Save updated papers_info to json file
    with file_path.open("w", encoding="utf-8") as json_file:
        json.dump(papers_info, json_file, indent=2)

    logging.info(f"Results are saved in: {file_path}")

    return paper_ids


if __name__ == "__main__":
    paper_ids = search_papers("machine learning")
    print(paper_ids)
