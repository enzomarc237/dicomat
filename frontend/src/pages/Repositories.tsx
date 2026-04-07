import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { repositoryApi, scanApi } from '../services/api';
import { Plus, Trash2, Edit2, Play, GitBranch } from 'lucide-react';

export default function Repositories() {
  const queryClient = useQueryClient();
  const [showAddModal, setShowAddModal] = useState(false);
  const [newRepo, setNewRepo] = useState({
    name: '',
    url: '',
    provider: 'github',
    branch: 'main',
  });

  const { data: repositories, isLoading } = useQuery({
    queryKey: ['repositories'],
    queryFn: repositoryApi.list,
  });

  const addRepoMutation = useMutation({
    mutationFn: repositoryApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repositories'] });
      setShowAddModal(false);
      setNewRepo({ name: '', url: '', provider: 'github', branch: 'main' });
    },
  });

  const deleteRepoMutation = useMutation({
    mutationFn: repositoryApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repositories'] });
    },
  });

  const triggerScanMutation = useMutation({
    mutationFn: ({ repoId }: { repoId: number }) => 
      scanApi.trigger(repoId, 'manual'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repositories'] });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    addRepoMutation.mutate(newRepo as any);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Repositories</h1>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
        >
          <Plus size={20} className="mr-2" />
          Add Repository
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {repositories?.map((repo) => (
            <div key={repo.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center">
                  <GitBranch className="h-8 w-8 text-indigo-600 mr-3" />
                  <div>
                    <h3 className="font-semibold text-gray-900">{repo.name}</h3>
                    <p className="text-sm text-gray-500">{repo.provider}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  repo.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                }`}>
                  {repo.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>

              <p className="text-sm text-gray-600 mb-4 truncate">{repo.url}</p>
              
              <div className="text-xs text-gray-500 mb-4">
                <p>Branch: {repo.branch}</p>
                {repo.last_scan_at && (
                  <p>Last scan: {new Date(repo.last_scan_at).toLocaleDateString()}</p>
                )}
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => triggerScanMutation.mutate({ repoId: repo.id })}
                  className="flex-1 flex items-center justify-center px-3 py-2 bg-green-50 text-green-700 rounded hover:bg-green-100 text-sm"
                  disabled={triggerScanMutation.isPending}
                >
                  <Play size={16} className="mr-1" />
                  Scan
                </button>
                <button
                  onClick={() => deleteRepoMutation.mutate(repo.id)}
                  className="p-2 text-red-600 hover:bg-red-50 rounded"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            </div>
          ))}

          {repositories?.length === 0 && (
            <div className="col-span-full text-center py-12 text-gray-500">
              No repositories yet. Add your first repository to get started.
            </div>
          )}
        </div>
      )}

      {/* Add Repository Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Add Repository</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name
                </label>
                <input
                  type="text"
                  required
                  value={newRepo.name}
                  onChange={(e) => setNewRepo({ ...newRepo, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Repository URL
                </label>
                <input
                  type="url"
                  required
                  value={newRepo.url}
                  onChange={(e) => setNewRepo({ ...newRepo, url: e.target.value })}
                  placeholder="https://github.com/org/repo"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Provider
                </label>
                <select
                  value={newRepo.provider}
                  onChange={(e) => setNewRepo({ ...newRepo, provider: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="github">GitHub</option>
                  <option value="gitlab">GitLab</option>
                  <option value="bitbucket">Bitbucket</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Branch
                </label>
                <input
                  type="text"
                  value={newRepo.branch}
                  onChange={(e) => setNewRepo({ ...newRepo, branch: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={addRepoMutation.isPending}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                >
                  {addRepoMutation.isPending ? 'Adding...' : 'Add Repository'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
