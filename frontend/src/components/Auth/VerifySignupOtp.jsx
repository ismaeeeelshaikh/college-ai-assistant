import React, { useState } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';

const VerifySignupOtp = () => {
  const location = useLocation();
  const navigate = useNavigate();

  // Get user info passed from Register.jsx
  const { username, email, password } = location.state || {};

  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!username || !email || !password) {
    // If no user info, redirect back to register
    navigate('/register');
    return null;
  }

  const handleVerify = async () => {
    if (!otp) {
      setError('Please enter the OTP received in your email');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('/apiauth/complete-signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password, otp }),
      });

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(errText || 'OTP verification failed');
      }

      // On success redirect to login page or dashboard
      navigate('/login');
    } catch (err) {
      setError(err.message || 'Failed to verify OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full bg-white p-8 rounded-lg shadow">
        <h2 className="text-2xl font-bold text-center mb-6">
          Verify Signup OTP
        </h2>
        <p className="text-center mb-4 text-gray-700">
          Please enter the OTP sent to <strong>{email}</strong>
        </p>
        <input
          type="text"
          name="otp"
          placeholder="Enter OTP"
          value={otp}
          onChange={(e) => setOtp(e.target.value)}
          disabled={loading}
          className="w-full px-4 py-2 border border-gray-300 rounded-md mb-4 focus:ring-2 focus:ring-primary-500 outline-none"
        />
        {error && (
          <p className="text-red-600 text-sm mb-4 text-center">{error}</p>
        )}
        <button
          onClick={handleVerify}
          disabled={loading}
          className="w-full py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
        >
          {loading ? 'Verifying...' : 'Verify & Create Account'}
        </button>
        <p className="mt-4 text-center text-sm text-gray-600">
          Didn't receive OTP? Please check your spam or{' '}
          <Link to="/register" className="text-primary-600 hover:underline">
            go back and try again
          </Link>.
        </p>
      </div>
    </div>
  );
};

export default VerifySignupOtp;
