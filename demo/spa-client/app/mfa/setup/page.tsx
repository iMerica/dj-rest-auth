'use client';

import api from '@/lib/api';
import { useRouter } from 'next/navigation';
import { QRCodeSVG } from 'qrcode.react';
import React, { useEffect, useState } from 'react';

interface MfaSetupData {
  secret: string;
  totp_url: string;
  qr_code_data_uri: string;
  activation_token: string;
}

export default function MfaSetupPage() {
  const [setupData, setSetupData] = useState<MfaSetupData | null>(null);
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const fetchSetupData = async () => {
      try {
        // Updated URL based on my previous analysis of dj-rest-auth mfa urls
        const response = await api.get('/dj-rest-auth/mfa/totp/activate/');
        setSetupData(response.data);
      } catch (err) {
        console.error('Failed to load MFA setup data', err);
        setError('Failed to load MFA setup data. You may already have MFA enabled.');
      }
    };
    fetchSetupData();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!setupData) return;

    try {
      await api.post('/dj-rest-auth/mfa/totp/activate/', {
        activation_token: setupData.activation_token,
        code: code
      });
      setSuccess(true);
      setTimeout(() => {
        router.push('/');
      }, 2000);
    } catch (err: any) {
      setError('Activation failed. Invalid code.');
    }
  };

  if (success) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-100">
        <div className="w-full max-w-md p-8 bg-white rounded shadow-md text-center">
          <h2 className="text-2xl font-bold text-green-600">MFA Activated!</h2>
          <p>Redirecting to dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100">
      <div className="w-full max-w-md p-8 space-y-6 bg-white rounded shadow-md">
        <h2 className="text-2xl font-bold text-center">Setup Multi-Factor Authentication</h2>

        {error && <div className="p-4 text-red-700 bg-red-100 rounded">{error}</div>}

        {setupData ? (
          <>
            <div className="flex justify-center">
              {/* Use totp_url for QR code */}
              <QRCodeSVG value={setupData.totp_url} size={200} />
            </div>
            <p className="text-center text-sm text-gray-600">
              Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.).
            </p>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Verification Code</label>
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  className="w-full px-3 py-2 mt-1 border rounded-md focus:outline-none focus:ring focus:ring-indigo-200"
                  placeholder="Enter 6-digit code"
                  required
                />
              </div>
              <button
                type="submit"
                className="w-full px-4 py-2 font-bold text-white bg-indigo-600 rounded hover:bg-indigo-700 focus:outline-none focus:ring focus:ring-indigo-200"
              >
                Activate
              </button>
            </form>
          </>
        ) : (
          <p className="text-center">Loading setup data...</p>
        )}
      </div>
    </div>
  );
}
