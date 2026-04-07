"""
Code Parser Module

Uses tree-sitter for AST-based parsing of source code files.
Extracts functions, classes, methods, and usage patterns.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class CodeElement:
    """Represents a parsed code element (function, class, method, etc.)."""
    name: str
    type: str  # function, class, method, variable, etc.
    path: str  # File path
    line_start: int
    line_end: int
    signature: Optional[str] = None
    docstring: Optional[str] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    return_type: Optional[str] = None
    language: str = "unknown"
    content: Optional[str] = None


@dataclass
class UsageExample:
    """Represents a usage example of a code element."""
    element_name: str
    file_path: str
    line_number: int
    code_snippet: str
    context: Optional[str] = None
    parameters_used: Dict[str, Any] = field(default_factory=dict)


class BaseParser:
    """Base class for language-specific parsers."""
    
    def __init__(self, language: str):
        self.language = language
        self.tree = None
        self.source_code = ""
    
    def parse(self, source_code: str, file_path: str) -> List[CodeElement]:
        """Parse source code and extract code elements."""
        raise NotImplementedError
    
    def find_usage_examples(self, element_name: str) -> List[UsageExample]:
        """Find usage examples of a specific element."""
        raise NotImplementedError


class PythonParser(BaseParser):
    """Parser for Python source code using tree-sitter."""
    
    def __init__(self):
        super().__init__("python")
        self._init_tree_sitter()
    
    def _init_tree_sitter(self):
        """Initialize tree-sitter for Python."""
        try:
            from tree_sitter import Language, Parser
            
            # Load language grammar
            # Note: In production, you'd build this from the tree-sitter-python repo
            # For now, we'll use a fallback approach
            self.ts_parser = Parser()
            
            # Try to load the language
            try:
                PYTHON_LANGUAGE = Language('build/my-languages.so', 'python')
                self.ts_parser.set_language(PYTHON_LANGUAGE)
            except Exception:
                logger.warning("tree-sitter language not available, using fallback parser")
                self.ts_parser = None
        except ImportError:
            logger.warning("tree-sitter not installed, using fallback parser")
            self.ts_parser = None
    
    def parse(self, source_code: str, file_path: str) -> List[CodeElement]:
        """Parse Python source code."""
        self.source_code = source_code
        elements = []
        
        if self.ts_parser:
            # Use tree-sitter for accurate parsing
            try:
                tree = self.ts_parser.parse(bytes(source_code, "utf-8"))
                elements = self._extract_elements_ts(tree, file_path)
            except Exception as e:
                logger.error(f"tree-sitter parsing error: {e}")
                elements = self._extract_elements_fallback(source_code, file_path)
        else:
            # Fallback to regex-based parsing
            elements = self._extract_elements_fallback(source_code, file_path)
        
        return elements
    
    def _extract_elements_fallback(self, source_code: str, file_path: str) -> List[CodeElement]:
        """Fallback parser using regex patterns."""
        import re
        elements = []
        lines = source_code.split('\n')
        
        # Function pattern
        func_pattern = re.compile(r'^(\s*)def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*(\S+))?\s*:')
        
        i = 0
        while i < len(lines):
            match = func_pattern.match(lines[i])
            if match:
                indent, name, params_str, return_type = match.groups()
                
                # Parse parameters
                params = []
                if params_str.strip():
                    for param in params_str.split(','):
                        param = param.strip()
                        if ':' in param:
                            param_name, param_type = param.split(':', 1)
                            params.append({'name': param_name.strip(), 'type': param_type.strip()})
                        else:
                            params.append({'name': param, 'type': None})
                
                # Find docstring
                docstring = None
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines) and ('"""' in lines[j] or "'''" in lines[j]):
                    quote = '"""' if '"""' in lines[j] else "'''"
                    docstring_lines = []
                    if lines[j].count(quote) >= 2:
                        docstring = lines[j].split(quote)[1]
                    else:
                        docstring_lines.append(lines[j].split(quote)[1])
                        j += 1
                        while j < len(lines) and quote not in lines[j]:
                            docstring_lines.append(lines[j])
                            j += 1
                        if j < len(lines):
                            docstring_lines.append(lines[j].split(quote)[0])
                        docstring = '\n'.join(docstring_lines)
                
                # Find end of function
                func_indent = len(indent)
                end_line = i + 1
                for k in range(i + 1, len(lines)):
                    if lines[k].strip():
                        current_indent = len(lines[k]) - len(lines[k].lstrip())
                        if current_indent <= func_indent and not lines[k].strip().startswith('#'):
                            break
                    end_line = k + 1
                
                elements.append(CodeElement(
                    name=name,
                    type='function',
                    path=file_path,
                    line_start=i + 1,
                    line_end=end_line,
                    signature=lines[i].strip(),
                    docstring=docstring,
                    parameters=params,
                    return_type=return_type,
                    language='python',
                    content='\n'.join(lines[i:end_line])
                ))
            i += 1
        
        return elements
    
    def find_usage_examples(self, element_name: str) -> List[UsageExample]:
        """Find usage examples of a function/method."""
        examples = []
        import re
        
        # Pattern for function calls
        pattern = re.compile(rf'\b{re.escape(element_name)}\s*\([^)]*\)')
        
        lines = self.source_code.split('\n')
        for i, line in enumerate(lines):
            matches = pattern.findall(line)
            if matches:
                examples.append(UsageExample(
                    element_name=element_name,
                    file_path='<current>',
                    line_number=i + 1,
                    code_snippet=line.strip(),
                    context='\n'.join(lines[max(0, i - 2):min(len(lines), i + 3)])
                ))
        
        return examples


class JavaScriptParser(BaseParser):
    """Parser for JavaScript/TypeScript source code."""
    
    def __init__(self):
        super().__init__("javascript")
    
    def parse(self, source_code: str, file_path: str) -> List[CodeElement]:
        """Parse JavaScript/TypeScript source code."""
        import re
        elements = []
        lines = source_code.split('\n')
        
        # Function patterns
        patterns = [
            # Regular function
            (r'function\s+(\w+)\s*\(([^)]*)\)', 'function'),
            # Arrow function assigned to variable
            (r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>', 'function'),
            # Method in class
            (r'^\s+(?:async\s+)?(\w+)\s*\(([^)]*)\)\s*{', 'method'),
            # Class definition
            (r'class\s+(\w+)', 'class'),
        ]
        
        for i, line in enumerate(lines):
            for pattern, elem_type in patterns:
                match = re.search(pattern, line)
                if match:
                    name = match.group(1)
                    params_str = match.group(2) if len(match.groups()) > 1 else ''
                    
                    # Parse parameters
                    params = []
                    if params_str:
                        for param in params_str.split(','):
                            param = param.strip()
                            if param:
                                params.append({'name': param, 'type': None})
                    
                    elements.append(CodeElement(
                        name=name,
                        type=elem_type,
                        path=file_path,
                        line_start=i + 1,
                        line_end=i + 1,
                        signature=line.strip(),
                        language='javascript',
                        content=line.strip()
                    ))
        
        return elements
    
    def find_usage_examples(self, element_name: str) -> List[UsageExample]:
        """Find usage examples."""
        return []


def get_parser(language: str) -> BaseParser:
    """Get appropriate parser for language."""
    parsers = {
        'python': PythonParser,
        'javascript': JavaScriptParser,
        'typescript': JavaScriptParser,
    }
    
    parser_class = parsers.get(language, BaseParser)
    return parser_class()
