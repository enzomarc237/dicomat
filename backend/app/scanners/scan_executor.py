"""
Scan Executor Module

Orchestrates the full scanning process: cloning, parsing, example extraction,
redaction, and document generation.
"""

from typing import List, Dict, Any, Optional

import structlog
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.scanners.repository_scanner import RepositoryScanner, FileInfo, ScanResult
from app.parsers.code_parser import get_parser, CodeElement
from app.redaction.secret_redactor import get_redactor
from app.models.schemas import Repository, Scan, Document
from app.models.pydantic_schemas import ScanStatus, DocumentType
from app.db.database import get_db

logger = structlog.get_logger(__name__)


class ScanExecutor:
    """Executes repository scans and generates documentation."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.scanner = RepositoryScanner()
        self.redactor = get_redactor()
    
    async def execute_scan(self, scan_id: int) -> ScanResult:
        """Execute a complete scan for a repository."""
        logger.info("Starting scan execution", scan_id=scan_id)
        
        # Get scan record
        result = await self.db.execute(
            select(Scan).where(Scan.id == scan_id)
        )
        scan = result.scalar_one_or_none()
        
        if not scan:
            raise ValueError(f"Scan {scan_id} not found")
        
        # Get repository
        repo_result = await self.db.execute(
            select(Repository).where(Repository.id == scan.repository_id)
        )
        repo = repo_result.scalar_one_or_none()
        
        if not repo:
            raise ValueError(f"Repository {scan.repository_id} not found")
        
        # Update scan status to running
        scan.status = ScanStatus.RUNNING
        scan.started_at = datetime.utcnow()
        await self.db.flush()
        
        result = ScanResult(
            repository_id=repo.id,
            scan_id=scan.id,
            total_files=0,
            files_scanned=0,
            documents_generated=0
        )
        
        try:
            # Clone repository
            logger.info("Cloning repository", repo_url=repo.url, branch=repo.branch)
            repo_path = self.scanner.clone_repository(
                repo.url,
                branch=repo.branch,
                auth_token=None  # TODO: Get from secure storage
            )
            
            # Discover files
            logger.info("Discovering files", repo_path=str(repo_path))
            exclude_patterns = repo.config.get('exclude_patterns', []) if repo.config else []
            files = self.scanner.discover_files(repo_path, exclude_patterns)
            result.total_files = len(files)
            
            # Process each file
            documents_to_create = []
            for file_info in files:
                try:
                    result.files_scanned += 1
                    
                    # Parse file content
                    parsed_elements = await self._parse_file(file_info)
                    
                    # Generate documents from parsed elements
                    for element in parsed_elements:
                        doc = await self._generate_document(
                            element=element,
                            repository_id=repo.id,
                            scan_id=scan.id,
                            file_info=file_info
                        )
                        if doc:
                            documents_to_create.append(doc)
                    
                    # Handle config files specially
                    if file_info.is_config:
                        config_doc = await self._generate_config_document(
                            file_info=file_info,
                            repository_id=repo.id,
                            scan_id=scan.id
                        )
                        if config_doc:
                            documents_to_create.append(config_doc)
                
                except Exception as e:
                    logger.error("Error processing file", file=file_info.path, error=str(e))
                    result.errors.append(f"Error processing {file_info.path}: {str(e)}")
            
            # Bulk create documents
            if documents_to_create:
                self.db.add_all(documents_to_create)
                result.documents_generated = len(documents_to_create)
            
            # Mark old documents as not latest
            await self._mark_old_documents(repo.id, scan.id)
            
            # Update scan status to completed
            scan.status = ScanStatus.COMPLETED
            scan.completed_at = datetime.utcnow()
            scan.files_scanned = result.files_scanned
            scan.documents_generated = result.documents_generated
            repo.last_scan_at = datetime.utcnow()
            
            await self.db.flush()
            await self.db.commit()
            
            # Cleanup cloned repo
            self.scanner.cleanup(repo_path)
            
            logger.info(
                "Scan completed successfully",
                scan_id=scan_id,
                files_scanned=result.files_scanned,
                documents_generated=result.documents_generated
            )
            
        except Exception as e:
            logger.error("Scan failed", scan_id=scan_id, error=str(e))
            scan.status = ScanStatus.FAILED
            scan.error_message = str(e)
            scan.completed_at = datetime.utcnow()
            await self.db.flush()
            await self.db.commit()
            
            result.errors.append(str(e))
        
        return result
    
    async def _parse_file(self, file_info: FileInfo) -> List[CodeElement]:
        """Parse a file and extract code elements."""
        if file_info.is_config:
            return []
        
        parser = get_parser(file_info.language)
        elements = parser.parse(file_info.content, file_info.path)
        
        # Find usage examples for each element
        for element in elements:
            examples = parser.find_usage_examples(element.name)
            element.examples = examples
        
        return elements
    
    async def _generate_document(
        self,
        element: CodeElement,
        repository_id: int,
        scan_id: int,
        file_info: FileInfo
    ) -> Optional[Document]:
        """Generate a document from a code element."""
        # Redact any secrets in the element content
        redacted_content = self.redactor.redact_code(element.content or "")
        
        # Build examples list with redaction
        examples = []
        if hasattr(element, 'examples') and element.examples:
            for example in element.examples:
                redacted_example = self.redactor.redact_code(example.code_snippet)
                examples.append({
                    "code": redacted_example.redacted,
                    "file_path": example.file_path,
                    "line_number": example.line_number,
                    "context": example.context,
                    "is_redacted": not redacted_example.is_safe
                })
        
        # Generate summary using AI (placeholder - would call LLM in production)
        summary = self._generate_summary(element)
        
        # Create slug from element name
        slug = element.name.lower().replace('_', '-').replace('.', '-')
        
        doc_type_map = {
            'function': DocumentType.FUNCTION,
            'method': DocumentType.FUNCTION,
            'class': DocumentType.CLASS,
            'module': DocumentType.MODULE,
        }
        
        doc = Document(
            repository_id=repository_id,
            scan_id=scan_id,
            title=f"{element.type.title()} {element.name}",
            slug=f"{doc_type_map.get(element.type, 'other')}-{slug}",
            doc_type=doc_type_map.get(element.type, 'other'),
            path=file_info.path,
            language=element.language,
            summary=summary,
            content=self._build_document_content(element, redacted_content.redacted),
            examples=examples,
            is_latest=True
        )
        
        return doc
    
    async def _generate_config_document(
        self,
        file_info: FileInfo,
        repository_id: int,
        scan_id: int
    ) -> Optional[Document]:
        """Generate documentation for a configuration file."""
        # Redact sensitive values
        if file_info.config_type == 'env':
            redacted = self.redactor.redact_env_file(file_info.content)
        else:
            redacted = self.redactor.redact_code(file_info.content)
        
        # Parse config structure
        config_info = self._parse_config_structure(file_info)
        
        slug = file_info.path.replace('/', '-').replace('.', '-').lower()
        
        doc = Document(
            repository_id=repository_id,
            scan_id=scan_id,
            title=f"Configuration: {file_info.path}",
            slug=f"config-{slug}",
            doc_type=DocumentType.CONFIG,
            path=file_info.path,
            language=file_info.config_type or 'config',
            summary=f"Configuration file: {file_info.path}",
            content=self._build_config_content(file_info, redacted.redacted, config_info),
            examples=[],
            is_latest=True
        )
        
        return doc
    
    def _generate_summary(self, element: CodeElement) -> str:
        """Generate a summary for a code element."""
        # In production, this would call an LLM
        # For now, use docstring or simple description
        if element.docstring:
            # Extract first sentence from docstring
            first_line = element.docstring.strip().split('\n')[0]
            return first_line.strip()
        
        params_desc = ""
        if element.parameters:
            param_names = [p['name'] for p in element.parameters[:3]]
            params_desc = f" Takes parameters: {', '.join(param_names)}."
        
        return f"A {element.type} named {element.name}.{params_desc}"
    
    def _build_document_content(self, element: CodeElement, redacted_code: str) -> str:
        """Build Markdown content for a document."""
        lines = [
            f"# {element.type.title()}: `{element.name}`",
            "",
            "## Summary",
            "",
            element.docstring or "No description available.",
            "",
            "## Signature",
            "",
            "```" + element.language,
            element.signature or redacted_code.split('\n')[0],
            "```",
            "",
        ]
        
        if element.parameters:
            lines.extend([
                "## Parameters",
                "",
                "| Name | Type | Description |",
                "|------|------|-------------|",
            ])
            for param in element.parameters:
                lines.append(f"| `{param['name']}` | {param.get('type', 'Any')} | |")
            lines.append("")
        
        if element.return_type:
            lines.extend([
                "## Returns",
                "",
                f"`{element.return_type}`",
                "",
            ])
        
        lines.extend([
            "## Source Code",
            "",
            "```" + element.language,
            redacted_code,
            "```",
            "",
            "## Usage Examples",
            "",
        ])
        
        if hasattr(element, 'examples') and element.examples:
            for i, example in enumerate(element.examples, 1):
                lines.extend([
                    f"### Example {i}",
                    "",
                    f"Location: `{example.file_path}:{example.line_number}`",
                    "",
                    "```" + element.language,
                    example.code_snippet,
                    "```",
                    "",
                ])
        else:
            lines.append("No usage examples found in the codebase.")
        
        return '\n'.join(lines)
    
    def _build_config_content(
        self,
        file_info: FileInfo,
        redacted_content: str,
        config_info: Dict[str, Any]
    ) -> str:
        """Build Markdown content for a config file."""
        lines = [
            f"# Configuration: `{file_info.path}`",
            "",
            "## Overview",
            "",
            f"Type: **{file_info.config_type or 'Unknown'}**",
            "",
            "## Content",
            "",
            "```" + (file_info.config_type or 'text'),
            redacted_content,
            "```",
            "",
        ]
        
        if config_info.get('variables'):
            lines.extend([
                "## Variables",
                "",
                "| Variable | Description | Default |",
                "|----------|-------------|---------|",
            ])
            for var in config_info['variables']:
                lines.append(f"| `{var['name']}` | {var.get('desc', '')} | {var.get('default', '')} |")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _parse_config_structure(self, file_info: FileInfo) -> Dict[str, Any]:
        """Parse configuration file structure."""
        info = {'variables': []}
        
        if file_info.config_type == 'env':
            for line in file_info.content.split('\n'):
                if '=' in line and not line.strip().startswith('#'):
                    key, _, value = line.partition('=')
                    info['variables'].append({
                        'name': key.strip(),
                        'desc': '',
                        'default': value.strip() if value.strip() else None
                    })
        
        return info
    
    async def _mark_old_documents(self, repository_id: int, current_scan_id: int):
        """Mark previous documents as not latest."""
        result = await self.db.execute(
            select(Document).where(
                Document.repository_id == repository_id,
                Document.is_latest == True
            )
        )
        old_docs = result.scalars().all()
        
        for doc in old_docs:
            doc.is_latest = False
        
        await self.db.flush()


async def run_scan(scan_id: int):
    """Entry point for running a scan."""
    # Get DB session
    db_gen = get_db()
    db = await db_gen.__anext__()
    
    try:
        executor = ScanExecutor(db)
        result = await executor.execute_scan(scan_id)
        return result
    finally:
        await db_gen.aclose()
