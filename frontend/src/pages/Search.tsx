import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { searchApi, documentApi } from '../services/api';
import { Search, FileText, Code, Settings, Box, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Search() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [results, setResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [total, setTotal] = useState(0);
  const [tookMs, setTookMs] = useState(0);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    try {
      const response = await searchApi.search(query, { limit: 20 });
      setResults(response.results);
      setTotal(response.total);
      setTookMs(response.took_ms);
      navigate(`/search?q=${encodeURIComponent(query)}`);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const getIcon = (docType: string) => {
    switch (docType) {
      case 'api':
        return <Box size={18} />;
      case 'class':
        return <Box size={18} />;
      case 'function':
        return <Code size={18} />;
      case 'config':
        return <Settings size={18} />;
      default:
        return <FileText size={18} />;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Search Documentation</h1>
        <p className="text-gray-600 mt-1">
          Find documentation using natural language queries
        </p>
      </div>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="relative">
        <div className="flex gap-3">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="How do I configure database connection?"
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <button
            type="submit"
            disabled={isSearching}
            className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center"
          >
            <Search size={20} className="mr-2" />
            {isSearching ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>

      {/* Results */}
      {results.length > 0 && (
        <div className="text-sm text-gray-500">
          Found {total} results in {tookMs}ms
        </div>
      )}

      {/* Search Results */}
      <div className="space-y-4">
        {results.map((result) => (
          <div
            key={result.id}
            className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-indigo-100 text-indigo-600 rounded-lg">
                  {getIcon(result.doc_type)}
                </div>
                <div>
                  <Link
                    to={`/documents/${result.slug}`}
                    className="font-semibold text-gray-900 hover:text-indigo-600"
                  >
                    {result.title}
                  </Link>
                  <div className="flex items-center space-x-2 mt-1 text-xs text-gray-500">
                    <span className="px-2 py-1 bg-gray-100 rounded">
                      {result.doc_type}
                    </span>
                    {result.language && (
                      <span className="px-2 py-1 bg-gray-100 rounded">
                        {result.language}
                      </span>
                    )}
                    <span>{result.repository_name}</span>
                  </div>
                </div>
              </div>
              <span className="text-xs text-gray-400">
                Score: {result.score.toFixed(2)}
              </span>
            </div>

            <p className="text-sm text-gray-600 line-clamp-3">
              {result.snippet}
            </p>

            {result.file_path && (
              <div className="mt-3 flex items-center text-xs text-gray-500">
                <FileText size={14} className="mr-1" />
                {result.file_path}
              </div>
            )}
          </div>
        ))}

        {query && !isSearching && results.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <Search size={48} className="mx-auto mb-4 text-gray-300" />
            <p className="text-lg font-medium">No results found</p>
            <p className="text-sm mt-2">
              Try different keywords or check your spelling
            </p>
          </div>
        )}

        {!query && (
          <div className="text-center py-12 text-gray-500">
            <Search size={48} className="mx-auto mb-4 text-gray-300" />
            <p className="text-lg font-medium">Start your search</p>
            <p className="text-sm mt-2">
              Enter a query above to search through all documentation
            </p>
          </div>
        )}
      </div>

      {/* Search Tips */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">Search Tips</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Use natural language: "How do I connect to the database?"</li>
          <li>• Search for specific functions or classes by name</li>
          <li>• Look for configuration examples with "config" or "setup"</li>
          <li>• Filter by repository or document type using the sidebar</li>
        </ul>
      </div>
    </div>
  );
}
