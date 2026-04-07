import { useQuery } from '@tanstack/react-query';
import { documentApi } from '../services/api';
import { Book, FileText, Code, Settings, Box } from 'lucide-react';
import { Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';

export default function Documents() {
  const { data: documents, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documentApi.list(),
  });

  const getIcon = (docType: string) => {
    switch (docType) {
      case 'api':
        return <Box size={20} />;
      case 'class':
        return <Box size={20} />;
      case 'function':
        return <Code size={20} />;
      case 'config':
        return <Settings size={20} />;
      default:
        return <FileText size={20} />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
        <div className="text-sm text-gray-500">
          {documents?.length || 0} documents found
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {documents?.map((doc) => (
            <Link
              key={doc.id}
              to={`/documents/${doc.slug}`}
              className="block bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-4 flex-1">
                  <div className="p-2 bg-indigo-100 text-indigo-600 rounded-lg">
                    {getIcon(doc.doc_type)}
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 mb-1">
                      {doc.title}
                    </h3>
                    <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                      {doc.summary || 'No summary available'}
                    </p>
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span className="px-2 py-1 bg-gray-100 rounded">
                        {doc.doc_type}
                      </span>
                      {doc.language && (
                        <span className="px-2 py-1 bg-gray-100 rounded">
                          {doc.language}
                        </span>
                      )}
                      {doc.path && (
                        <span className="truncate max-w-xs">
                          {doc.path}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <Book size={20} className="text-gray-400 flex-shrink-0 ml-4" />
              </div>
            </Link>
          ))}

          {documents?.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No documents yet. Scan a repository to generate documentation.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
