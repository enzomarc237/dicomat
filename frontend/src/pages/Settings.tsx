export default function Settings() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
      
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Application Settings</h2>
        <p className="text-gray-600">
          Configure your DocuMate AI preferences and integrations.
        </p>
        
        <div className="mt-6 space-y-4">
          <div className="border-t border-gray-200 pt-4">
            <h3 className="font-medium text-gray-900">Scan Configuration</h3>
            <p className="text-sm text-gray-500 mt-1">
              Configure default scan schedules and exclusions
            </p>
          </div>
          
          <div className="border-t border-gray-200 pt-4">
            <h3 className="font-medium text-gray-900">Integrations</h3>
            <p className="text-sm text-gray-500 mt-1">
              Connect to GitHub, GitLab, Slack, and other services
            </p>
          </div>
          
          <div className="border-t border-gray-200 pt-4">
            <h3 className="font-medium text-gray-900">API Keys</h3>
            <p className="text-sm text-gray-500 mt-1">
              Manage API keys for external services
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">About DocuMate AI</h2>
        <div className="space-y-2 text-sm text-gray-600">
          <p><strong>Version:</strong> 0.1.0 (MVP)</p>
          <p><strong>Build:</strong> Development</p>
          <p className="mt-4">
            DocuMate AI is an AI-powered documentation platform that automatically 
            generates, maintains, and evolves searchable, example-rich internal wikis 
            for private APIs, configuration files, and internal libraries.
          </p>
        </div>
      </div>
    </div>
  );
}
