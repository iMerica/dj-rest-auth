'use client';

import { useAuth } from '@/context/AuthContext';
import api from '@/lib/api';
import Link from 'next/link';
import { useEffect, useState } from 'react';

export default function Home() {
  const { user, logout, loading } = useAuth();
  const [mfaStatus, setMfaStatus] = useState<{ mfa_enabled: boolean } | null>(null);

  useEffect(() => {
    if (user) {
      api.get('/dj-rest-auth/mfa/status/')
        .then(res => setMfaStatus(res.data))
        .catch(err => console.error('Failed to fetch MFA status', err));
    }
  }, [user]);

  if (loading) return <div className="p-8">Loading...</div>;

  if (!user) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center p-24">
        <h1 className="text-4xl font-bold mb-8">dj-rest-auth MFA Demo</h1>
        <div className="flex gap-4">
          <Link href="/login" className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">Login</Link>
          <Link href="/register" className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600">Register</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto bg-white rounded shadow p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Welcome, {user.first_name || user.username}</h1>
          <button onClick={logout} className="px-4 py-2 border rounded hover:bg-gray-100">Logout</button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="border p-4 rounded">
            <h2 className="text-xl font-semibold mb-4">User Details</h2>
            <p><strong>Username:</strong> {user.username}</p>
            <p><strong>Email:</strong> {user.email}</p>
          </div>

          <div className="border p-4 rounded">
            <h2 className="text-xl font-semibold mb-4">Security Settings</h2>
            <div className="flex items-center justify-between mb-4">
              <span>Multi-Factor Authentication (MFA)</span>
              <span className={`px-2 py-1 rounded text-sm ${mfaStatus?.mfa_enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                {mfaStatus?.mfa_enabled ? 'Enabled' : 'Disabled'}
              </span>
            </div>

            {mfaStatus?.mfa_enabled ? (
              <div className="space-y-2">
                <Link href="/mfa/settings" className="block w-full text-center px-4 py-2 bg-gray-200 rounded hover:bg-gray-300">
                  Manage MFA (Not Implemented)
                </Link>
                <button
                  onClick={() => alert('Disable MFA logic would go here (endpoint: /dj-rest-auth/mfa/totp/deactivate/)')}
                  className="block w-full text-center px-4 py-2 text-red-600 border border-red-200 rounded hover:bg-red-50"
                >
                  Disable MFA
                </button>
              </div>
            ) : (
              <Link href="/mfa/setup" className="block w-full text-center px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700">
                Enable MFA
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
