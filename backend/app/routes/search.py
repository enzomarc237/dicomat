from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import time

from app.db.database import get_db
from app.models.schemas import Document
from app.models.pydantic_schemas import (
    SearchQuery,
    SearchResponse,
    DocumentSearchResult,
    DocumentResponse
)

router = APIRouter()


@router.post("/", response_model=SearchResponse)
async def search_documents(
    query: SearchQuery,
    db: AsyncSession = Depends(get_db)
):
    """
    Search documentation using natural language queries.
    
    Supports both keyword and semantic search (when vector store is configured).
    """
    start_time = time.time()
    
    # TODO: Implement vector search with Weaviate/Pinecone
    # For now, use basic keyword search
    
    results = []
    
    # Build search query
    stmt = select(Document).where(Document.is_latest == True)
    
    # Filter by repository if specified
    if query.repository_ids:
        stmt = stmt.where(Document.repository_id.in_(query.repository_ids))
    
    # Filter by document type if specified
    if query.doc_types:
        doc_type_strings = [dt.value for dt in query.doc_types]
        stmt = stmt.where(Document.doc_type.in_(doc_type_strings))
    
    # Filter by language if specified
    if query.languages:
        stmt = stmt.where(Document.language.in_(query.languages))
    
    # Execute search
    result = await db.execute(stmt)
    documents = result.scalars().all()
    
    # Simple keyword matching (replace with vector search)
    query_terms = query.query.lower().split()
    
    scored_docs = []
    for doc in documents:
        score = 0.0
        content_lower = (doc.content + " " + (doc.summary or "") + " " + doc.title).lower()
        
        for term in query_terms:
            if term in content_lower:
                score += 1.0
            # Bonus for title match
            if term in doc.title.lower():
                score += 2.0
            # Bonus for slug match
            if term in doc.slug.lower():
                score += 1.5
        
        if score > 0:
            # Generate snippet
            snippet_start = max(0, content_lower.find(query_terms[0]) - 50) if query_terms else 0
            snippet_end = min(len(doc.content), snippet_start + 200)
            snippet = doc.content[snippet_start:snippet_end].strip()
            if snippet_start > 0:
                snippet = "..." + snippet
            if snippet_end < len(doc.content):
                snippet = snippet + "..."
            
            # Get repository name (would need to join in real implementation)
            repo_name = f"repo-{doc.repository_id}"
            
            scored_docs.append({
                "doc": doc,
                "score": score,
                "snippet": snippet,
                "repo_name": repo_name
            })
    
    # Sort by score descending
    scored_docs.sort(key=lambda x: x["score"], reverse=True)
    
    # Apply pagination
    total = len(scored_docs)
    paginated = scored_docs[query.offset:query.offset + query.limit]
    
    # Convert to response format
    results = [
        DocumentSearchResult(
            id=item["doc"].id,
            score=item["score"],
            snippet=item["snippet"],
            repository_name=item["repo_name"],
            title=item["doc"].title,
            slug=item["doc"].slug,
            doc_type=item["doc"].doc_type,
            path=item["doc"].path,
            language=item["doc"].language,
            summary=item["doc"].summary,
            file_path=item["doc"].path
        )
        for item in paginated
    ]
    
    took_ms = int((time.time() - start_time) * 1000)
    
    return SearchResponse(
        query=query.query,
        results=results,
        total=total,
        took_ms=took_ms
    )


@router.get("/suggestions", response_model=List[str])
async def get_search_suggestions(
    q: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get search query suggestions based on existing documents."""
    
    # TODO: Implement proper suggestion engine
    # For now, return empty list
    return []
