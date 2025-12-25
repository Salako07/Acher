import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../AuthContext';
import { ProjectDetail, CheckinStatus } from '../types';

export default function Project() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [checkinLoading, setCheckinLoading] = useState(false);
  const [error, setError] = useState('');
  const [showInvite, setShowInvite] = useState(false);

  useEffect(() => {
    loadProject();
  }, [id]);

  const loadProject = async () => {
    if (!id) return;
    try {
      const data = await api.getProject(parseInt(id));
      setProject(data);
    } catch (err) {
      setError('Failed to load project');
    } finally {
      setLoading(false);
    }
  };

  const handleCheckin = async () => {
    if (!id || !project) return;
    setCheckinLoading(true);
    setError('');

    try {
      await api.createCheckin(parseInt(id));
      await loadProject();
    } catch (err: any) {
      setError(err.message || 'Check-in failed');
    } finally {
      setCheckinLoading(false);
    }
  };

  const getCurrentUserStatus = () => {
    if (!project || !user) return null;
    return project.today_statuses.find(s => s.user_id === user.id);
  };

  const userStatus = getCurrentUserStatus();
  const canCheckin = userStatus && !userStatus.status;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-50">
        <p className="text-neutral-600">Loading</p>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-50">
        <p className="text-neutral-600">{error || 'Project not found'}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-50">
      <div className="max-w-2xl mx-auto px-6 py-12">
        <div className="mb-8">
          <Link to="/dashboard" className="text-sm text-neutral-600 hover:text-neutral-900">
            ← Projects
          </Link>
        </div>

        <div className="mb-8">
          <h1 className="text-3xl font-medium text-neutral-900 mb-2">
            {project.name}
          </h1>
          {project.description && (
            <p className="text-neutral-600">{project.description}</p>
          )}
        </div>

        <div className="mb-12">
          <p className="text-sm text-neutral-500 mb-6">
            {new Date().toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            })}
          </p>

          {canCheckin ? (
            <button
              onClick={handleCheckin}
              disabled={checkinLoading}
              className="w-full px-6 py-4 bg-neutral-900 text-white text-lg font-semibold hover:bg-neutral-800 disabled:bg-neutral-400"
            >
              {checkinLoading ? 'Marking...' : 'Mark done today'}
            </button>
          ) : userStatus?.status === CheckinStatus.DONE ? (
            <div className="w-full px-6 py-4 border border-neutral-300 bg-white text-center">
              <p className="text-neutral-900">Checked in at {formatTime(userStatus.checked_at)}</p>
            </div>
          ) : userStatus?.status === CheckinStatus.MISSED ? (
            <div className="w-full px-6 py-4 border border-neutral-300 bg-white text-center">
              <p className="text-neutral-600">Missed</p>
            </div>
          ) : null}

          {error && (
            <p className="mt-3 text-sm text-neutral-600">{error}</p>
          )}
        </div>

        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-neutral-900">Participants</h2>
            {user && user.id === project.creator_id && (
              <button
                onClick={() => setShowInvite(!showInvite)}
                className="px-3 py-1 border border-neutral-300 text-sm text-neutral-900 hover:border-neutral-900"
              >
                {showInvite ? 'Hide invite' : 'Generate invite'}
              </button>
            )}
          </div>

          {showInvite && <InviteSection projectId={project.id} />}

          <div className="space-y-1 mt-4">
            {project.today_statuses.map((status) => (
              <div
                key={status.user_id}
                className="px-4 py-3 border border-neutral-200 bg-white flex items-center justify-between"
              >
                <span className="text-neutral-900">{status.username}</span>
                <div className="text-sm">
                  {status.status === CheckinStatus.DONE && (
                    <span className="text-neutral-900">
                      {formatTime(status.checked_at)}
                    </span>
                  )}
                  {status.status === CheckinStatus.MISSED && (
                    <span className="text-neutral-500">Missed</span>
                  )}
                  {!status.status && (
                    <span className="text-neutral-400">Pending</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="flex gap-4">
          <Link
            to={`/projects/${project.id}/analytics`}
            className="text-sm text-neutral-600 hover:text-neutral-900"
          >
            View analytics
          </Link>
        </div>
      </div>
    </div>
  );
}

function InviteSection({ projectId }: { projectId: number }) {
  const [inviteCode, setInviteCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const generateInvite = async () => {
    setLoading(true);
    try {
      const invite = await api.createInvite(projectId);
      setInviteCode(invite.code);
    } catch (err) {
      console.error('Failed to generate invite', err);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(inviteCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy', err);
    }
  };

  return (
    <div className="mb-4 p-4 border border-neutral-300 bg-neutral-50">
      {inviteCode ? (
        <div>
          <p className="text-sm text-neutral-700 mb-2">Invite code</p>
          <div className="flex gap-2">
            <p className="flex-1 font-mono text-sm px-3 py-2 border border-neutral-300 bg-white">
              {inviteCode}
            </p>
            <button
              onClick={copyToClipboard}
              className="px-3 py-2 border border-neutral-300 bg-white text-neutral-900 text-sm hover:border-neutral-900"
            >
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>
          <p className="text-xs text-neutral-500 mt-2">Share this code with others to invite them</p>
        </div>
      ) : (
        <button
          onClick={generateInvite}
          disabled={loading}
          className="w-full px-4 py-2 bg-neutral-900 text-white font-medium hover:bg-neutral-800 disabled:bg-neutral-400"
        >
          {loading ? 'Generating...' : 'Generate invite code'}
        </button>
      )}
    </div>
  );
}

function formatTime(timestamp: string | null): string {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}
