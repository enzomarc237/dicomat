import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { documentApi } from '../services/api';
import { FileText, Code, Settings, Box, Calendar, GitBranch } from 'lucide-react';

export default function DocumentDetail() {
  const { slug } = useParams<{ slug: string }>();

  const { data: document, isLoading, error } = useQuery({
    queryKey: ['document', slug],
    queryFn: () => documentApi.getBySlug(slug!),
    enabled: !!slug,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-500">Loading document...</div>
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900">Document not found</h2>
        <p className="text-gray-600 mt-2">
          The document you're looking for doesn't exist or has been removed.
        </p>
      </div>
    );
  }

  const getIcon = (docType: string) => {
    switch (docType) {
      case 'api':
        return <Box size={24} />;
      case 'class':
        return <Box size={24} />;
      case 'function':
        return <Code size={24} />;
      case 'config':
        return <Settings size={24} />;
      default:
        return <FileText size={24} />;
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-indigo-100 text-indigo-600 rounded-lg">
              {getIcon(document.doc_type)}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{document.title}</h1>
              <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                <span className="px-2 py-1 bg-gray-100 rounded">
                  {document.doc_type}
                </span>
                {document.language && (
                  <span className="px-2 py-1 bg-gray-100 rounded">
                    {document.language}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {document.summary && (
          <p className="text-gray-600 mb-4">{document.summary}</p>
        )}

        <div className="flex items-center space-x-6 text-sm text-gray-500">
          <div className="flex items-center">
            <Calendar size={16} className="mr-2" />
            Created: {new Date(document.created_at).toLocaleDateString()}
          </div>
          {document.path && (
            <div className="flex items-center">
              <GitBranch size={16} className="mr-2" />
              {document.path}
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Documentation</h2>
        <div 
          className="markdown-content prose max-w-none"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(document.content) }}
        />
      </div>

      {/* Examples */}
      {document.examples && document.examples.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Usage Examples</h2>
          <div className="space-y-4">
            {document.examples.map((example, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium text-gray-900">Example {index + 1}</h3>
                  <span className="text-xs text-gray-500">
                    {example.file_path}:{example.line_number}
                  </span>
                </div>
                <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
                  <code>{example.code}</code>
                </pre>
                {example.context && (
                  <p className="text-xs text-gray-500 mt-2">{example.context}</p>
                )}
                {example.is_redacted && (
                  <p className="text-xs text-orange-600 mt-2">
                    ⚠️ This example contains redacted sensitive information
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Simple markdown renderer (in production, use react-markdown)
function renderMarkdown(content: string): string {
  let html = content
    // Headers
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    // Code blocks
    .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>')
    // Inline code
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // Bold
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    // Line breaks
    .replace(/\n/g, '<br/>');

  return html;
}
