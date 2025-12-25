import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api';
import { ProjectAnalytics } from '../types';

export default function Analytics() {
  const { id } = useParams<{ id: string }>();
  const [analytics, setAnalytics] = useState<ProjectAnalytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, [id]);

  const loadAnalytics = async () => {
    if (!id) return;
    try {
      const data = await api.getProjectAnalytics(parseInt(id));
      setAnalytics(data);
    } catch (err) {
      console.error('Failed to load analytics', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-50">
        <p className="text-neutral-600">Loading</p>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-50">
        <p className="text-neutral-600">Analytics not found</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-50">
      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="mb-8">
          <Link to={`/projects/${id}`} className="text-sm text-neutral-600 hover:text-neutral-900">
            ← Back to project
          </Link>
        </div>

        <div className="mb-8">
          <h1 className="text-3xl font-medium text-neutral-900 mb-2">
            {analytics.project_name}
          </h1>
          <p className="text-neutral-600">Analytics</p>
        </div>

        <div className="bg-white border border-neutral-200">
          <table className="w-full">
            <thead>
              <tr className="border-b border-neutral-200">
                <th className="px-4 py-3 text-left text-sm font-medium text-neutral-700">
                  Member
                </th>
                <th className="px-4 py-3 text-right text-sm font-medium text-neutral-700">
                  Current streak
                </th>
                <th className="px-4 py-3 text-right text-sm font-medium text-neutral-700">
                  Longest streak
                </th>
                <th className="px-4 py-3 text-right text-sm font-medium text-neutral-700">
                  Total check-ins
                </th>
                <th className="px-4 py-3 text-right text-sm font-medium text-neutral-700">
                  Consistency
                </th>
              </tr>
            </thead>
            <tbody>
              {analytics.user_streaks
                .sort((a, b) => b.consistency_percent - a.consistency_percent)
                .map((streak) => (
                  <tr key={streak.user_id} className="border-b border-neutral-200 last:border-0">
                    <td className="px-4 py-3 text-neutral-900">
                      {streak.username}
                    </td>
                    <td className="px-4 py-3 text-right text-neutral-700">
                      {streak.current_streak}
                    </td>
                    <td className="px-4 py-3 text-right text-neutral-700">
                      {streak.longest_streak}
                    </td>
                    <td className="px-4 py-3 text-right text-neutral-700">
                      {streak.total_checkins} / {streak.total_days}
                    </td>
                    <td className="px-4 py-3 text-right text-neutral-900 font-medium">
                      {streak.consistency_percent.toFixed(1)}%
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>

        <div className="mt-6">
          <p className="text-sm text-neutral-500">
            Project age: {analytics.total_project_days} days
          </p>
        </div>
      </div>
    </div>
  );
}
