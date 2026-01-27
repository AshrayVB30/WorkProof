import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { employeeAPI } from '../lib/api';
import { Shield, Check, X, Lock, AlertCircle } from 'lucide-react';

const Consent: React.FC = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();
    const { updateUser } = useAuth();

    const handleAccept = async () => {
        try {
            setLoading(true);
            setError('');
            await employeeAPI.acceptConsent();
            updateUser({ consent_accepted: true });
            navigate('/dashboard');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to accept consent');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-100 flex items-center justify-center p-4">
            <div className="max-w-3xl w-full animate-fade-in">
                {/* Header */}
                <div className="card shadow-strong mb-6">
                    <div className="bg-gradient-primary px-8 py-6 rounded-t-xl">
                        <div className="flex items-center gap-4">
                            <div className="w-14 h-14 bg-white rounded-xl flex items-center justify-center shadow-md">
                                <Shield className="w-8 h-8 text-primary-600" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold text-white">Privacy & Consent</h1>
                                <p className="text-primary-100 text-sm mt-1">Please review and accept to continue</p>
                            </div>
                        </div>
                    </div>

                    {/* Content */}
                    <div className="p-8 space-y-6">
                        {error && (
                            <div className="p-4 bg-danger-50 border border-danger-200 rounded-lg flex items-start gap-3 animate-slide-down">
                                <AlertCircle className="w-5 h-5 text-danger-600 flex-shrink-0 mt-0.5" />
                                <p className="text-sm text-danger-800 font-medium">{error}</p>
                            </div>
                        )}

                        {/* What IS tracked */}
                        <div className="border-2 border-success-200 rounded-xl p-6 bg-success-50">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="w-10 h-10 bg-success-600 rounded-xl flex items-center justify-center shadow-md">
                                    <Check className="w-6 h-6 text-white" />
                                </div>
                                <h2 className="text-lg font-bold text-neutral-900">What IS Tracked</h2>
                            </div>
                            <ul className="space-y-3">
                                <li className="flex items-start gap-3">
                                    <Check className="w-5 h-5 text-success-600 flex-shrink-0 mt-0.5" />
                                    <span className="text-neutral-700 font-medium">Application names and window titles you work in</span>
                                </li>
                                <li className="flex items-start gap-3">
                                    <Check className="w-5 h-5 text-success-600 flex-shrink-0 mt-0.5" />
                                    <span className="text-neutral-700 font-medium">Active time vs idle time (based on mouse/keyboard activity)</span>
                                </li>
                                <li className="flex items-start gap-3">
                                    <Check className="w-5 h-5 text-success-600 flex-shrink-0 mt-0.5" />
                                    <span className="text-neutral-700 font-medium">Metadata about your work sessions (timestamps, duration)</span>
                                </li>
                                <li className="flex items-start gap-3">
                                    <Check className="w-5 h-5 text-success-600 flex-shrink-0 mt-0.5" />
                                    <span className="text-neutral-700 font-medium">Screenshots (stored securely, viewable by admin only for disputes)</span>
                                </li>
                            </ul>
                        </div>

                        {/* What is NOT tracked */}
                        <div className="border-2 border-danger-200 rounded-xl p-6 bg-danger-50">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="w-10 h-10 bg-danger-600 rounded-xl flex items-center justify-center shadow-md">
                                    <X className="w-6 h-6 text-white" />
                                </div>
                                <h2 className="text-lg font-bold text-neutral-900">What is NOT Tracked</h2>
                            </div>
                            <ul className="space-y-3">
                                <li className="flex items-start gap-3">
                                    <X className="w-5 h-5 text-danger-600 flex-shrink-0 mt-0.5" />
                                    <span className="text-neutral-700 font-medium">Individual keystrokes or typed content</span>
                                </li>
                                <li className="flex items-start gap-3">
                                    <X className="w-5 h-5 text-danger-600 flex-shrink-0 mt-0.5" />
                                    <span className="text-neutral-700 font-medium">Personal browsing or non-work activities</span>
                                </li>
                                <li className="flex items-start gap-3">
                                    <X className="w-5 h-5 text-danger-600 flex-shrink-0 mt-0.5" />
                                    <span className="text-neutral-700 font-medium">Passwords, credit card numbers, or sensitive personal data</span>
                                </li>
                                <li className="flex items-start gap-3">
                                    <X className="w-5 h-5 text-danger-600 flex-shrink-0 mt-0.5" />
                                    <span className="text-neutral-700 font-medium">Screenshots are NOT visible to you or shared publicly</span>
                                </li>
                            </ul>
                        </div>

                        {/* Privacy & Data Usage */}
                        <div className="border-2 border-primary-200 rounded-xl p-6 bg-primary-50">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center shadow-md">
                                    <Lock className="w-6 h-6 text-white" />
                                </div>
                                <h2 className="text-lg font-bold text-neutral-900">Data Usage & Privacy</h2>
                            </div>
                            <ul className="space-y-3">
                                <li className="flex items-start gap-3">
                                    <Lock className="w-5 h-5 text-primary-600 flex-shrink-0 mt-0.5" />
                                    <span className="text-neutral-700 font-medium">All data is encrypted and stored securely</span>
                                </li>
                                <li className="flex items-start gap-3">
                                    <Lock className="w-5 h-5 text-primary-600 flex-shrink-0 mt-0.5" />
                                    <span className="text-neutral-700 font-medium">Data is used only for work verification and reporting</span>
                                </li>
                                <li className="flex items-start gap-3">
                                    <Lock className="w-5 h-5 text-primary-600 flex-shrink-0 mt-0.5" />
                                    <span className="text-neutral-700 font-medium">You can view your own activity timeline and daily summaries</span>
                                </li>
                                <li className="flex items-start gap-3">
                                    <Lock className="w-5 h-5 text-primary-600 flex-shrink-0 mt-0.5" />
                                    <span className="text-neutral-700 font-medium">Data is retained according to company policy and legal requirements</span>
                                </li>
                            </ul>
                        </div>

                        {/* Transparency Note */}
                        <div className="bg-gradient-to-r from-primary-50 to-success-50 border border-primary-200 rounded-xl p-5">
                            <p className="text-sm text-neutral-700 leading-relaxed">
                                <strong className="text-neutral-900 font-bold">Our Commitment:</strong> This system is designed for transparency and trust.
                                You will have full visibility into your tracked work hours and activity. We believe in building trust, not surveillance.
                            </p>
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="px-8 py-6 bg-neutral-50 border-t border-neutral-200 rounded-b-xl">
                        <button
                            onClick={handleAccept}
                            disabled={loading}
                            className="btn-primary w-full py-3.5 text-base font-semibold shadow-md hover:shadow-lg"
                        >
                            {loading ? (
                                <span className="flex items-center justify-center gap-2">
                                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                    Processing...
                                </span>
                            ) : (
                                'I Agree & Continue'
                            )}
                        </button>
                        <p className="text-xs text-neutral-500 text-center mt-3">
                            By clicking "I Agree & Continue", you acknowledge that you have read and understood the above information.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Consent;


