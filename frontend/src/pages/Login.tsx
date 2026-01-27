import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LogIn, AlertCircle, Shield } from 'lucide-react';

const Login: React.FC = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    // Get preferred role from landing page selection
    const preferredRole = (location.state as any)?.preferredRole;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await login(email, password);
            navigate('/dashboard');
        } catch (err: any) {
            setError(err.message || 'Login failed. Please check your credentials.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-100 flex items-center justify-center p-4">
            <div className="max-w-md w-full animate-fade-in">
                {/* Logo/Header */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-primary rounded-2xl mb-4 shadow-strong">
                        <Shield className="w-10 h-10 text-white" />
                    </div>
                    <h1 className="text-4xl font-bold text-neutral-900 mb-2">WorkProof</h1>
                    <p className="text-neutral-600 text-lg">Transparent Work Verification</p>
                </div>

                {/* Login Form */}
                <div className="card shadow-strong animate-slide-up">
                    <div className="card-body">
                        <h2 className="text-2xl font-semibold text-neutral-900 mb-2">Welcome Back</h2>
                        {preferredRole && (
                            <p className="text-neutral-500 mb-6 flex items-center gap-2">
                                <span className={`w-2 h-2 rounded-full ${preferredRole === 'admin' ? 'bg-indigo-500' : 'bg-primary-500'}`}></span>
                                Logging in as <span className="font-bold text-neutral-700 capitalize">{preferredRole}</span>
                            </p>
                        )}

                        {error && (
                            <div className="mb-6 p-4 bg-danger-50 border border-danger-200 rounded-lg flex items-start gap-3 animate-slide-down">
                                <AlertCircle className="w-5 h-5 text-danger-600 flex-shrink-0 mt-0.5" />
                                <p className="text-sm text-danger-800 font-medium">{error}</p>
                            </div>
                        )}

                        <form onSubmit={handleSubmit} className="space-y-5">
                            <div>
                                <label htmlFor="email" className="block text-sm font-semibold text-neutral-700 mb-2">
                                    Email Address
                                </label>
                                <input
                                    id="email"
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    className="input-field"
                                    placeholder="you@company.com"
                                />
                            </div>

                            <div>
                                <label htmlFor="password" className="block text-sm font-semibold text-neutral-700 mb-2">
                                    Password
                                </label>
                                <input
                                    id="password"
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    className="input-field"
                                    placeholder="••••••••"
                                />
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="btn-primary w-full py-3 text-base font-semibold shadow-md hover:shadow-lg"
                            >
                                {loading ? (
                                    <span className="flex items-center justify-center gap-2">
                                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                        Signing in...
                                    </span>
                                ) : (
                                    <span className="flex items-center justify-center gap-2">
                                        <LogIn className="w-5 h-5" />
                                        Sign In
                                    </span>
                                )}
                            </button>
                        </form>
                    </div>
                </div>

                {/* Footer */}
                <div className="mt-8 text-center">
                    <p className="text-sm text-neutral-500">
                        WorkProof © 2026 - Building trust through transparency
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Login;

