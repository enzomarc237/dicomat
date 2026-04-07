"""
Repository Scanner Module

Handles cloning repositories, discovering files, and orchestrating the scanning process.
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
import git

from app.config import settings


@dataclass
class FileInfo:
    """Information about a scanned file."""
    path: str
    language: str
    size: int
    content: str
    last_modified: datetime
    is_config: bool = False
    config_type: Optional[str] = None


@dataclass
class ScanResult:
    """Result of a repository scan."""
    repository_id: int
    scan_id: int
    total_files: int
    files_scanned: int
    documents_generated: int
    errors: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class RepositoryScanner:
    """Scans Git repositories for documentation generation."""
    
    def __init__(self, workdir: Optional[str] = None):
        self.workdir = workdir or settings.SCAN_WORKDIR
        self.supported_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.jsx': 'javascript',
            '.go': 'go',
            '.java': 'java',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
        }
        self.config_files = {
            '.env': 'env',
            'docker-compose.yml': 'docker-compose',
            'docker-compose.yaml': 'docker-compose',
            'docker-compose.local.yml': 'docker-compose',
            'docker-compose.dev.yml': 'docker-compose',
            'k8s': 'kubernetes',
            'kubernetes': 'kubernetes',
        }
    
    def clone_repository(self, repo_url: str, branch: str = "main", auth_token: Optional[str] = None) -> Path:
        """Clone a repository to the working directory."""
        # Extract repo name from URL
        repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
        repo_path = Path(self.workdir) / repo_name
        
        # Remove existing clone if present
        if repo_path.exists():
            shutil.rmtree(repo_path)
        
        # Prepare clone options
        clone_kwargs = {
            'depth': 1,  # Shallow clone for speed
            'single-branch': True,
            'branch': branch,
        }
        
        # Add authentication if provided
        if auth_token:
            # Inject token into URL for private repos
            if 'github.com' in repo_url:
                repo_url = repo_url.replace('https://github.com', f'https://x-access-token:{auth_token}@github.com')
            elif 'gitlab.com' in repo_url:
                repo_url = repo_url.replace('https://gitlab.com', f'https://oauth2:{auth_token}@gitlab.com')
        
        # Clone repository
        try:
            repo = git.Repo.clone_from(repo_url, repo_path, **clone_kwargs)
            return repo_path
        except git.GitError as e:
            raise Exception(f"Failed to clone repository: {str(e)}")
    
    def discover_files(self, repo_path: Path, exclude_patterns: Optional[List[str]] = None) -> List[FileInfo]:
        """Discover all relevant files in the repository."""
        files = []
        exclude_patterns = exclude_patterns or [
            '__pycache__',
            'node_modules',
            '.git',
            '.venv',
            'venv',
            'dist',
            'build',
            '*.min.js',
            '*.test.*',
            '*.spec.*',
        ]
        
        for root, dirs, filenames in os.walk(repo_path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not any(p in d for p in exclude_patterns)]
            
            for filename in filenames:
                file_path = Path(root) / filename
                rel_path = file_path.relative_to(repo_path)
                
                # Check exclusions
                if any(self._matches_pattern(str(rel_path), p) for p in exclude_patterns):
                    continue
                
                # Determine file type
                language = self._get_language(filename, file_path)
                is_config, config_type = self._is_config_file(filename, file_path)
                
                if language or is_config:
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        stat = file_path.stat()
                        
                        files.append(FileInfo(
                            path=str(rel_path),
                            language=language or 'config',
                            size=stat.st_size,
                            content=content,
                            last_modified=datetime.fromtimestamp(stat.st_mtime),
                            is_config=is_config,
                            config_type=config_type
                        ))
                    except Exception as e:
                        # Skip files that can't be read
                        continue
        
        return files
    
    async def scan_incremental(
        self,
        repo_path: Path,
        last_scan_at: Optional[datetime] = None
    ) -> AsyncGenerator[FileInfo, None]:
        """Incrementally scan only changed files since last scan."""
        if last_scan_at is None:
            # Full scan
            files = self.discover_files(repo_path)
            for file_info in files:
                yield file_info
        else:
            # Only yield modified files
            files = self.discover_files(repo_path)
            for file_info in files:
                if file_info.last_modified > last_scan_at:
                    yield file_info
    
    def _get_language(self, filename: str, file_path: Path) -> Optional[str]:
        """Determine programming language from file extension."""
        ext = file_path.suffix.lower()
        return self.supported_extensions.get(ext)
    
    def _is_config_file(self, filename: str, file_path: Path) -> tuple[bool, Optional[str]]:
        """Check if file is a configuration file."""
        # Check exact matches
        if filename in self.config_files:
            return True, self.config_files[filename]
        
        # Check .env files
        if filename.startswith('.env'):
            return True, 'env'
        
        # Check YAML files for k8s/terraform
        if file_path.suffix.lower() in ['.yml', '.yaml']:
            content = file_path.read_text(encoding='utf-8', errors='ignore')[:500]
            if 'apiVersion:' in content and 'kind:' in content:
                return True, 'kubernetes'
            if 'resource "' in content or 'data "' in content:
                return True, 'terraform'
        
        return False, None
    
    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches exclusion pattern."""
        import fnmatch
        return fnmatch.fnmatch(path, pattern) or pattern in path
    
    def cleanup(self, repo_path: Path):
        """Clean up cloned repository."""
        if repo_path.exists():
            shutil.rmtree(repo_path)


# Singleton instance
_scanner_instance: Optional[RepositoryScanner] = None


def get_scanner() -> RepositoryScanner:
    """Get or create scanner instance."""
    global _scanner_instance
    if _scanner_instance is None:
        _scanner_instance = RepositoryScanner()
    return _scanner_instance
