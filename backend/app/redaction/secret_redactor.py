"""
Secret Redaction Module

Detects and redacts sensitive information from code examples.
Supports API keys, passwords, tokens, PII, and custom patterns.
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class SecretType(str, Enum):
    """Types of secrets that can be detected."""
    API_KEY = "api_key"
    PASSWORD = "password"
    TOKEN = "token"
    PRIVATE_KEY = "private_key"
    DATABASE_URL = "database_url"
    AWS_KEY = "aws_key"
    GITHUB_TOKEN = "github_token"
    EMAIL = "email"
    PHONE = "phone"
    IP_ADDRESS = "ip_address"
    CUSTOM = "custom"


@dataclass
class DetectedSecret:
    """Represents a detected secret in code."""
    type: SecretType
    value: str
    start_pos: int
    end_pos: int
    line_number: int
    confidence: float  # 0.0 to 1.0
    pattern_name: str


@dataclass
class RedactedContent:
    """Content with secrets redacted."""
    original: str
    redacted: str
    secrets_found: List[DetectedSecret]
    is_safe: bool


class SecretDetector:
    """Detects various types of secrets in text content."""
    
    # Default patterns for secret detection
    PATTERNS = {
        SecretType.API_KEY: [
            (r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', 0.9),
            (r'(?i)(api[_-]?secret)\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', 0.9),
        ],
        SecretType.PASSWORD: [
            (r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']?([^\s"\']{4,})["\']?', 0.85),
            (r'(?i)(db_password|database_password)\s*[=:]\s*["\']?([^\s"\']{4,})["\']?', 0.9),
        ],
        SecretType.TOKEN: [
            (r'(?i)(access[_-]?token|auth[_-]?token|bearer)\s*[=:]\s*["\']?([a-zA-Z0-9_\-\.]{20,})["\']?', 0.9),
            (r'(?i)(refresh[_-]?token)\s*[=:]\s*["\']?([a-zA-Z0-9_\-\.]{20,})["\']?', 0.9),
        ],
        SecretType.PRIVATE_KEY: [
            (r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----', 1.0),
            (r'(?i)(private[_-]?key)\s*[=:]\s*["\']?([^\s"\']{20,})["\']?', 0.8),
        ],
        SecretType.DATABASE_URL: [
            (r'(postgres(?:ql)?|mysql|mongodb|redis)://[^\s]+:[^\s]+@[^\s]+', 0.95),
            (r'(?i)(database[_-]?url|db[_-]?url|connection[_-]?string)\s*[=:]\s*["\']?([^\s"\']+)["\']?', 0.85),
        ],
        SecretType.AWS_KEY: [
            (r'AKIA[0-9A-Z]{16}', 0.95),  # AWS Access Key ID
            (r'(?i)(aws[_-]?secret|aws[_-]?access[_-]?key)\s*[=:]\s*["\']?([a-zA-Z0-9/+=]{40})["\']?', 0.9),
        ],
        SecretType.GITHUB_TOKEN: [
            (r'ghp_[a-zA-Z0-9]{36}', 0.95),  # GitHub Personal Access Token
            (r'gho_[a-zA-Z0-9]{36}', 0.95),  # GitHub OAuth Token
            (r'ghu_[a-zA-Z0-9]{36}', 0.95),  # GitHub User-to-Server Token
            (r'ghs_[a-zA-Z0-9]{36}', 0.95),  # GitHub Server-to-Server Token
        ],
        SecretType.EMAIL: [
            (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', 0.7),
        ],
        SecretType.PHONE: [
            (r'\+?1?\s*\(?[0-9]{3}\)?[\s.-]?[0-9]{3}[\s.-]?[0-9]{4}', 0.75),
        ],
        SecretType.IP_ADDRESS: [
            (r'\b(?:\d{1,3}\.){3}\d{1,3}\b', 0.6),
        ],
    }
    
    def __init__(self, custom_patterns: Optional[Dict[str, List[tuple]]] = None):
        self.patterns = {**self.PATTERNS}
        if custom_patterns:
            for secret_type, patterns in custom_patterns.items():
                if isinstance(secret_type, str):
                    secret_type = SecretType.CUSTOM
                if secret_type not in self.patterns:
                    self.patterns[secret_type] = []
                self.patterns[secret_type].extend(patterns)
        
        # Compile regex patterns
        self._compiled_patterns = {}
        for secret_type, type_patterns in self.patterns.items():
            self._compiled_patterns[secret_type] = [
                (re.compile(pattern), confidence)
                for pattern, confidence in type_patterns
            ]
    
    def detect(self, content: str) -> List[DetectedSecret]:
        """Detect all secrets in the given content."""
        secrets = []
        
        for secret_type, compiled in self._compiled_patterns.items():
            for pattern, confidence in compiled:
                for match in pattern.finditer(content):
                    start_pos = match.start()
                    line_number = content[:start_pos].count('\n') + 1
                    
                    groups = match.groups()
                    if groups:
                        value = groups[-1]
                    else:
                        value = match.group(0)
                    
                    secrets.append(DetectedSecret(
                        type=secret_type,
                        value=value,
                        start_pos=start_pos,
                        end_pos=match.end(),
                        line_number=line_number,
                        confidence=confidence,
                        pattern_name=pattern.pattern
                    ))
        
        secrets.sort(key=lambda s: s.start_pos)
        return secrets
    
    def redact(self, content: str, replacement: str = "***REDACTED***") -> RedactedContent:
        """Detect and redact all secrets in content."""
        secrets = self.detect(content)
        
        if not secrets:
            return RedactedContent(
                original=content,
                redacted=content,
                secrets_found=[],
                is_safe=True
            )
        
        unique_secrets = self._deduplicate_secrets(secrets)
        
        redacted = content
        for secret in reversed(unique_secrets):
            redacted = (
                redacted[:secret.start_pos] +
                replacement +
                redacted[secret.end_pos:]
            )
        
        return RedactedContent(
            original=content,
            redacted=redacted,
            secrets_found=unique_secrets,
            is_safe=False
        )
    
    def _deduplicate_secrets(self, secrets: List[DetectedSecret]) -> List[DetectedSecret]:
        """Remove overlapping secrets, keeping highest confidence."""
        if not secrets:
            return []
        
        sorted_secrets = sorted(secrets, key=lambda s: (s.start_pos, -s.confidence))
        result = []
        last_end = -1
        
        for secret in sorted_secrets:
            if secret.start_pos < last_end:
                continue
            result.append(secret)
            last_end = secret.end_pos
        
        return result


class CodeRedactor:
    """Redacts secrets from code while preserving structure."""
    
    def __init__(self, detector: Optional[SecretDetector] = None):
        self.detector = detector or SecretDetector()
    
    def redact_code(self, code: str, language: str = "unknown") -> RedactedContent:
        """Redact secrets from code snippet."""
        return self.detector.redact(code)
    
    def redact_env_file(self, content: str) -> RedactedContent:
        """Redact .env file content, keeping variable names but redacting values."""
        lines = content.split('\n')
        redacted_lines = []
        secrets = []
        
        for i, line in enumerate(lines):
            match = re.match(r'^([^#=][^=]*?)=(.*)$', line)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                
                if value and not value.startswith('#'):
                    if len(value) > 3 and value not in ['true', 'false', 'null', 'none']:
                        redacted_lines.append(f"{key}=***REDACTED***")
                        secrets.append(DetectedSecret(
                            type=SecretType.PASSWORD,
                            value=value,
                            start_pos=0,
                            end_pos=len(line),
                            line_number=i + 1,
                            confidence=0.8,
                            pattern_name="env_value"
                        ))
                    else:
                        redacted_lines.append(line)
                else:
                    redacted_lines.append(line)
            else:
                redacted_lines.append(line)
        
        return RedactedContent(
            original=content,
            redacted='\n'.join(redacted_lines),
            secrets_found=secrets,
            is_safe=len(secrets) == 0
        )
    
    def redact_yaml_config(self, content: str) -> RedactedContent:
        """Redact YAML configuration files."""
        return self.detector.redact(content)


_redactor_instance: Optional[CodeRedactor] = None


def get_redactor() -> CodeRedactor:
    """Get or create redactor instance."""
    global _redactor_instance
    if _redactor_instance is None:
        _redactor_instance = CodeRedactor()
    return _redactor_instance


def redact_content(content: str, content_type: str = "code") -> RedactedContent:
    """Convenience function to redact content."""
    redactor = get_redactor()
    
    if content_type == "env":
        return redactor.redact_env_file(content)
    elif content_type == "yaml":
        return redactor.redact_yaml_config(content)
    else:
        return redactor.redact_code(content)
