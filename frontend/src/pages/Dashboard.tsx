import { useQuery } from '@tanstack/react-query';
import { repositoryApi, scanApi } from '../services/api';
import { Plus, RefreshCw, GitBranch } from 'lucide-react';
import { Link } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';

export default function Dashboard() {
  const { data: repositories, isLoading } = useQuery({
    queryKey: ['repositories'],
    queryFn: repositoryApi.list,
  });

  const stats = {
    totalRepos: repositories?.length || 0,
    totalScans: 0,
    totalDocs: 0,
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <Link
          to="/repositories"
          className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
        >
          <Plus size={20} className="mr-2" />
          Add Repository
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <GitBranch className="h-10 w-10 text-indigo-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Repositories</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.totalRepos}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <RefreshCw className="h-10 w-10 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Recent Scans</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.totalScans}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <svg className="h-10 w-10 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Documents</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.totalDocs}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Repositories */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Recent Repositories</h2>
        </div>
        
        {isLoading ? (
          <div className="p-6 text-center text-gray-500">Loading...</div>
        ) : repositories && repositories.length > 0 ? (
          <div className="divide-y divide-gray-200">
            {repositories.slice(0, 5).map((repo) => (
              <div key={repo.id} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">{repo.name}</h3>
                    <p className="text-sm text-gray-500">{repo.url}</p>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      repo.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {repo.is_active ? 'Active' : 'Inactive'}
                    </span>
                    {repo.last_scan_at && (
                      <span className="text-xs text-gray-500">
                        Last scan: {formatDistanceToNow(new Date(repo.last_scan_at), { addSuffix: true })}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-6 text-center text-gray-500">
            No repositories yet. Add your first repository to get started.
          </div>
        )}
      </div>

      {/* Quick Start Guide */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Getting Started</h2>
        <ol className="space-y-3 text-sm text-gray-600">
          <li className="flex items-start">
            <span className="flex-shrink-0 w-6 h-6 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center text-xs font-medium mr-3">1</span>
            Add a repository by clicking "Add Repository" above
          </li>
          <li className="flex items-start">
            <span className="flex-shrink-0 w-6 h-6 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center text-xs font-medium mr-3">2</span>
            Trigger a scan to analyze the codebase
          </li>
          <li className="flex items-start">
            <span className="flex-shrink-0 w-6 h-6 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center text-xs font-medium mr-3">3</span>
            Browse generated documentation in the Documents section
          </li>
          <li className="flex items-start">
            <span className="flex-shrink-0 w-6 h-6 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center text-xs font-medium mr-3">4</span>
            Use natural language search to find what you need
          </li>
        </ol>
      </div>
    </div>
  );
}
