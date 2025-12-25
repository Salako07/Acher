import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../AuthContext';
import { ProjectListItem, CheckinStatus } from '../types';

export default function Dashboard() {
  const [projects, setProjects] = useState<ProjectListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [showJoin, setShowJoin] = useState(false);
  const { logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const data = await api.getProjects();
      setProjects(data);
    } catch (err) {
      console.error('Failed to load projects', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusDisplay = (status: CheckinStatus | null) => {
    if (status === CheckinStatus.DONE) {
      return <span className="text-neutral-900">Done</span>;
    }
    if (status === CheckinStatus.MISSED) {
      return <span className="text-neutral-500">Missed</span>;
    }
    return <span className="text-neutral-400">Pending</span>;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-50">
        <p className="text-neutral-600">Loading</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-50">
      <div className="max-w-3xl mx-auto px-6 py-12">
        <div className="flex items-center justify-between mb-12">
          <h1 className="text-3xl font-medium text-neutral-900">Projects</h1>
          <button
            onClick={logout}
            className="text-sm text-neutral-600 hover:text-neutral-900"
          >
            Sign out
          </button>
        </div>

        <div className="mb-6 flex gap-4">
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="px-4 py-2 border border-neutral-300 text-neutral-900 font-medium hover:border-neutral-900"
          >
            New project
          </button>
          <button
            onClick={() => setShowJoin(!showJoin)}
            className="px-4 py-2 border border-neutral-300 text-neutral-900 font-medium hover:border-neutral-900"
          >
            Join project
          </button>
        </div>

        {showCreate && <CreateProjectForm onSuccess={loadProjects} onCancel={() => setShowCreate(false)} />}
        {showJoin && <JoinProjectForm onSuccess={loadProjects} onCancel={() => setShowJoin(false)} />}

        {projects.length === 0 ? (
          <p className="text-neutral-500">No projects</p>
        ) : (
          <div className="space-y-1">
            {projects.map((project) => (
              <Link
                key={project.id}
                to={`/projects/${project.id}`}
                className="block px-4 py-4 border border-neutral-200 hover:border-neutral-900 bg-white"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="font-medium text-neutral-900">{project.name}</h2>
                    <p className="text-sm text-neutral-500 mt-1">{project.member_count} members</p>
                  </div>
                  <div className="text-sm">
                    {getStatusDisplay(project.user_status_today)}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function CreateProjectForm({ onSuccess, onCancel }: { onSuccess: () => void; onCancel: () => void }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [resetHour, setResetHour] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await api.createProject({
        name,
        description: description || undefined,
        daily_reset_hour: resetHour
      });
      onSuccess();
      onCancel();
    } catch (err) {
      setError('Failed to create project');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="mb-6 p-4 border border-neutral-300 bg-white">
      <h3 className="font-medium mb-4 text-neutral-900">Create project</h3>
      <div className="space-y-4">
        <input
          type="text"
          placeholder="Project name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          className="w-full px-3 py-2 border border-neutral-300 focus:outline-none focus:border-neutral-900"
        />
        <input
          type="text"
          placeholder="Description (optional)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full px-3 py-2 border border-neutral-300 focus:outline-none focus:border-neutral-900"
        />
        <div>
          <label htmlFor="resetHour" className="block text-sm font-medium text-neutral-700 mb-2">
            Daily reset time
          </label>
          <select
            id="resetHour"
            value={resetHour}
            onChange={(e) => setResetHour(parseInt(e.target.value))}
            className="w-full px-3 py-2 border border-neutral-300 focus:outline-none focus:border-neutral-900 bg-white"
          >
            {Array.from({ length: 24 }, (_, i) => (
              <option key={i} value={i}>
                {i.toString().padStart(2, '0')}:00 ({i === 0 ? 'Midnight' : i === 12 ? 'Noon' : i < 12 ? `${i} AM` : `${i - 12} PM`})
              </option>
            ))}
          </select>
          <p className="text-xs text-neutral-500 mt-1">
            Day ends and missed check-ins are marked at this time
          </p>
        </div>
        {error && <p className="text-sm text-neutral-600">{error}</p>}
        <div className="flex gap-2">
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-neutral-900 text-white font-medium hover:bg-neutral-800"
          >
            Create
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 border border-neutral-300 text-neutral-900"
          >
            Cancel
          </button>
        </div>
      </div>
    </form>
  );
}

function JoinProjectForm({ onSuccess, onCancel }: { onSuccess: () => void; onCancel: () => void }) {
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const result = await api.acceptInvite(code);
      onSuccess();
      navigate(`/projects/${result.project_id}`);
    } catch (err) {
      setError('Invalid or expired invite code');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="mb-6 p-4 border border-neutral-300 bg-white">
      <h3 className="font-medium mb-4 text-neutral-900">Join project</h3>
      <div className="space-y-4">
        <input
          type="text"
          placeholder="Invite code"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          required
          className="w-full px-3 py-2 border border-neutral-300 focus:outline-none focus:border-neutral-900"
        />
        {error && <p className="text-sm text-neutral-600">{error}</p>}
        <div className="flex gap-2">
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-neutral-900 text-white font-medium hover:bg-neutral-800"
          >
            Join
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 border border-neutral-300 text-neutral-900"
          >
            Cancel
          </button>
        </div>
      </div>
    </form>
  );
}
