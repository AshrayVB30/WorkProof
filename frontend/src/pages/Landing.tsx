import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Clock, BarChart3, Lock, CheckCircle2, ArrowRight, MousePointer2, UserCheck, X, Briefcase, UserCog } from 'lucide-react';

const Landing: React.FC = () => {
    const [showRoleModal, setShowRoleModal] = React.useState(false);
    const navigate = useNavigate();

    const handleRoleSelect = (role: 'employee' | 'admin') => {
        // We can pass the intended role to login page or just navigate
        // For now, let's just go to login. If we had separate login pages, we'd navigate there.
        navigate('/login', { state: { preferredRole: role } });
    };

    return (
        <div className="min-h-screen bg-white">
            {/* Navigation */}
            <nav className="fixed top-0 w-full bg-white/80 backdrop-blur-md z-50 border-b border-neutral-100">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-16">
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 bg-gradient-primary rounded-lg flex items-center justify-center shadow-md">
                                <Shield className="w-5 h-5 text-white" />
                            </div>
                            <span className="text-xl font-bold text-neutral-900">WorkProof</span>
                        </div>
                        <div className="flex items-center gap-4">
                            <button onClick={() => setShowRoleModal(true)} className="text-neutral-600 hover:text-primary-600 font-medium transition-colors">
                                Sign In
                            </button>
                            <button onClick={() => handleRoleSelect('employee')} className="btn-primary py-2 px-4 text-sm">
                                Get Started
                            </button>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="pt-32 pb-20 px-4 bg-gradient-to-b from-primary-50 to-white overflow-hidden">
                <div className="max-w-7xl mx-auto text-center relative">
                    <div className="inline-flex items-center gap-2 px-4 py-2 bg-white rounded-full shadow-soft border border-neutral-100 mb-8 animate-fade-in">
                        <span className="flex h-2 w-2 rounded-full bg-primary-500 animate-pulse"></span>
                        <span className="text-sm font-medium text-neutral-600">Trust-based productivity tracking</span>
                    </div>
                    <h1 className="text-5xl md:text-7xl font-extrabold text-neutral-900 tracking-tight mb-8 animate-slide-up">
                        Building Trust Through <br />
                        <span className="text-gradient">Transparency</span>
                    </h1>
                    <p className="max-w-2xl mx-auto text-xl text-neutral-600 leading-relaxed mb-12 animate-slide-up" style={{ animationDelay: '0.1s' }}>
                        The work verification platform that empowers employees while providing
                        the oversight managers need. No surveillance, just proof of effort.
                    </p>
                    <div className="flex flex-col sm:flex-row justify-center gap-4 animate-slide-up" style={{ animationDelay: '0.2s' }}>
                        <a href="#preview" className="btn-primary text-lg px-8 py-4 flex items-center justify-center gap-2 cursor-pointer">
                            Explore Dashboard <ArrowRight className="w-5 h-5" />
                        </a>
                        <a href="#features" className="btn-secondary text-lg px-8 py-4 border border-neutral-200 cursor-pointer">
                            How it works
                        </a>
                    </div>

                    {/* Dashboard Preview Decal */}
                    <div id="preview" className="scroll-mt-24 mt-20 relative mx-auto max-w-5xl rounded-2xl shadow-strong overflow-hidden border border-neutral-200 animate-slide-up" style={{ animationDelay: '0.3s' }}>
                        <div className="bg-neutral-900 h-8 flex items-center px-4 gap-1.5">
                            <div className="w-3 h-3 rounded-full bg-red-500 opacity-60"></div>
                            <div className="w-3 h-3 rounded-full bg-amber-500 opacity-60"></div>
                            <div className="w-3 h-3 rounded-full bg-green-500 opacity-60"></div>
                        </div>
                        <div className="bg-neutral-50 p-4 md:p-8">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                <div className="stat-card">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-sm font-medium text-neutral-500">Active Time</span>
                                        <Clock className="w-5 h-5 text-primary-500" />
                                    </div>
                                    <p className="text-2xl font-bold text-neutral-900">7h 42m</p>
                                    <div className="mt-4 w-full bg-neutral-100 rounded-full h-1.5">
                                        <div className="bg-primary-500 h-1.5 rounded-full" style={{ width: '85%' }}></div>
                                    </div>
                                </div>
                                <div className="stat-card">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-sm font-medium text-neutral-500">Daily Goal</span>
                                        <CheckCircle2 className="w-5 h-5 text-success-500" />
                                    </div>
                                    <p className="text-2xl font-bold text-neutral-900">92%</p>
                                    <div className="mt-4 w-full bg-neutral-100 rounded-full h-1.5">
                                        <div className="bg-success-500 h-1.5 rounded-full" style={{ width: '92%' }}></div>
                                    </div>
                                </div>
                                <div className="stat-card">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-sm font-medium text-neutral-500">Activity Level</span>
                                        <BarChart3 className="w-5 h-5 text-warning-500" />
                                    </div>
                                    <p className="text-2xl font-bold text-neutral-900">High</p>
                                    <div className="mt-4 flex gap-1 h-1.5">
                                        <div className="flex-1 bg-warning-400 rounded-full"></div>
                                        <div className="flex-1 bg-warning-400 rounded-full"></div>
                                        <div className="flex-1 bg-warning-400 rounded-full"></div>
                                        <div className="flex-1 bg-neutral-200 rounded-full"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section id="features" className="scroll-mt-24 py-24 px-4">
                <div className="max-w-7xl mx-auto">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl md:text-4xl font-bold text-neutral-900 mb-4">A Mutual Trust Platform</h2>
                        <p className="text-lg text-neutral-600 max-w-2xl mx-auto">
                            Designed with privacy as a priority. We track outcomes and effort, not individual actions.
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        {/* Feature 1 */}
                        <div className="p-8 rounded-2xl border border-neutral-100 bg-neutral-50/50 hover:border-primary-200 hover:bg-white transition-all duration-300">
                            <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center mb-6">
                                <UserCheck className="w-6 h-6 text-primary-600" />
                            </div>
                            <h3 className="text-xl font-bold text-neutral-900 mb-3">Employee Consent</h3>
                            <p className="text-neutral-600 leading-relaxed">
                                Complete transparency on what data is being tracked. No hidden features or secret monitoring.
                            </p>
                        </div>

                        {/* Feature 2 */}
                        <div className="p-8 rounded-2xl border border-neutral-100 bg-neutral-50/50 hover:border-success-200 hover:bg-white transition-all duration-300">
                            <div className="w-12 h-12 bg-success-100 rounded-xl flex items-center justify-center mb-6">
                                <Lock className="w-6 h-6 text-success-600" />
                            </div>
                            <h3 className="text-xl font-bold text-neutral-900 mb-3">Privacy Protected</h3>
                            <p className="text-neutral-600 leading-relaxed">
                                No raw keystrokes or camera access. Only high-level activity metadata is used for reporting.
                            </p>
                        </div>

                        {/* Feature 3 */}
                        <div className="p-8 rounded-2xl border border-neutral-100 bg-neutral-50/50 hover:border-warning-200 hover:bg-white transition-all duration-300">
                            <div className="w-12 h-12 bg-warning-100 rounded-xl flex items-center justify-center mb-6">
                                <MousePointer2 className="w-6 h-6 text-warning-600" />
                            </div>
                            <h3 className="text-xl font-bold text-neutral-900 mb-3">Smart Activity Detection</h3>
                            <p className="text-neutral-600 leading-relaxed">
                                Intelligently detects work sessions vs idle time to provide fair and accurate productivity metrics.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="bg-neutral-50 py-12 border-t border-neutral-200">
                <div className="max-w-7xl mx-auto px-4 text-center">
                    <div className="flex items-center justify-center gap-2 mb-6">
                        <div className="w-6 h-6 bg-primary-600 rounded flex items-center justify-center shadow-sm">
                            <Shield className="w-4 h-4 text-white" />
                        </div>
                        <span className="font-bold text-neutral-900">WorkProof</span>
                    </div>
                    <p className="text-neutral-500 text-sm">
                        WorkProof © 2026. Empowering remote teams with verifiable trust.
                    </p>
                </div>
            </footer>

            {/* Role Selection Modal */}
            {showRoleModal && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 animate-fade-in">
                    <div className="absolute inset-0 bg-neutral-900/40 backdrop-blur-sm" onClick={() => setShowRoleModal(false)}></div>
                    <div className="relative w-full max-w-md bg-white rounded-2xl shadow-strong overflow-hidden animate-slide-up">
                        <div className="p-6 border-b border-neutral-100 flex items-center justify-between">
                            <h3 className="text-xl font-bold text-neutral-900">Sign In to WorkProof</h3>
                            <button onClick={() => setShowRoleModal(false)} className="p-2 hover:bg-neutral-100 rounded-full transition-colors">
                                <X className="w-5 h-5 text-neutral-500" />
                            </button>
                        </div>
                        <div className="p-8">
                            <p className="text-neutral-600 mb-8 text-center italic">Please select your workspace role to continue</p>

                            <div className="grid gap-4">
                                <button
                                    onClick={() => handleRoleSelect('employee')}
                                    className="group p-6 rounded-xl border-2 border-neutral-100 hover:border-primary-500 hover:bg-primary-50/30 transition-all duration-300 text-left flex items-center gap-4"
                                >
                                    <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center group-hover:bg-primary-500 transition-colors">
                                        <Briefcase className="w-6 h-6 text-primary-600 group-hover:text-white" />
                                    </div>
                                    <div>
                                        <div className="font-bold text-neutral-900 group-hover:text-primary-700">Login as Employee</div>
                                        <div className="text-sm text-neutral-500">Track your work and view your progress</div>
                                    </div>
                                </button>

                                <button
                                    onClick={() => handleRoleSelect('admin')}
                                    className="group p-6 rounded-xl border-2 border-neutral-100 hover:border-indigo-500 hover:bg-indigo-50/30 transition-all duration-300 text-left flex items-center gap-4"
                                >
                                    <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center group-hover:bg-indigo-500 transition-colors">
                                        <UserCog className="w-6 h-6 text-indigo-600 group-hover:text-white" />
                                    </div>
                                    <div>
                                        <div className="font-bold text-neutral-900 group-hover:text-indigo-700">Login as Admin</div>
                                        <div className="text-sm text-neutral-500">Manage team, view reports and settings</div>
                                    </div>
                                </button>
                            </div>
                        </div>
                        <div className="p-6 bg-neutral-50 text-center text-xs text-neutral-400">
                            By signing in, you agree to our Terms of Service and Privacy Policy.
                        </div>
                    </div>
                </div>
            )}
        </div>

    );
};

export default Landing;
