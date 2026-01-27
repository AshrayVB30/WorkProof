import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { authAPI } from '../lib/api';
import { UserPlus, UserCog, Briefcase, Mail, Lock, User, Hash, Clock, Building, AlertCircle, ArrowLeft, CheckCircle2 } from 'lucide-react';

const AddUser: React.FC = () => {
    const navigate = useNavigate();
    const location = useLocation();

    // Determine context (adding employee vs admin)
    const isAdminMode = location.pathname.includes('add-admin');
    const defaultRole = isAdminMode ? 'admin' : 'employee';

    const [formData, setFormData] = useState({
        full_name: '',
        email: '',
        password: '',
        employee_id: '',
        department: '',
        role: defaultRole,
        expected_daily_hours: '8'
    });

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const submitData = {
                ...formData,
                expected_daily_hours: parseFloat(formData.expected_daily_hours) || 0
            };
            await authAPI.register(submitData);
            setSuccess(true);
            setTimeout(() => {
                navigate(isAdminMode ? '/settings' : '/employees');
            }, 2000);
        } catch (err: any) {
            const detail = err.response?.data?.detail;
            if (typeof detail === 'string') {
                setError(detail);
            } else if (Array.isArray(detail)) {
                // Handle FastAPI validation errors (list of objects)
                setError(detail.map((e: any) => `${e.loc.join('.')}: ${e.msg}`).join(', '));
            } else {
                setError('Failed to create user. Please try again.');
            }
        } finally {
            setLoading(false);
        }
    };

    if (success) {
        return (
            <div className="max-w-md mx-auto mt-20 text-center animate-fade-in">
                <div className="w-20 h-20 bg-success-100 rounded-full flex items-center justify-center mx-auto mb-6 text-success-600">
                    <CheckCircle2 className="w-12 h-12" />
                </div>
                <h2 className="text-2xl font-bold text-neutral-900 mb-2">User Created Successfully!</h2>
                <p className="text-neutral-600 mb-8">
                    The {formData.role} account has been created and is ready for use.
                </p>
                <p className="text-sm text-neutral-400">Redirecting you back...</p>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto">
            {/* Header */}
            <div className="mb-8 flex items-center justify-between">
                <div>
                    <button
                        onClick={() => navigate(-1)}
                        className="flex items-center gap-2 text-neutral-500 hover:text-primary-600 transition-colors mb-4"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Back to management
                    </button>
                    <h1 className="text-3xl font-bold text-neutral-900 flex items-center gap-3">
                        {isAdminMode ? (
                            <><UserCog className="w-8 h-8 text-indigo-500" /> Add New Administrator</>
                        ) : (
                            <><Briefcase className="w-8 h-8 text-primary-500" /> Add New Employee</>
                        )}
                    </h1>
                    <p className="text-neutral-600 mt-2">
                        Create a new {formData.role} account and assign their initial configuration.
                    </p>
                </div>
            </div>

            <div className="bg-white rounded-2xl shadow-strong overflow-hidden border border-neutral-100">
                <form onSubmit={handleSubmit} className="divide-y divide-neutral-100">
                    {/* Basic Information */}
                    <div className="p-8">
                        <h2 className="text-lg font-bold text-neutral-900 mb-6 flex items-center gap-2">
                            <span className="w-8 h-8 rounded-lg bg-neutral-100 flex items-center justify-center text-neutral-500">1</span>
                            Profile Information
                        </h2>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-neutral-700">Full Name</label>
                                <div className="relative">
                                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" />
                                    <input
                                        required
                                        type="text"
                                        placeholder="John Doe"
                                        className="input-field pl-10"
                                        value={formData.full_name}
                                        onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-neutral-700">Email Address</label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" />
                                    <input
                                        required
                                        type="email"
                                        placeholder="john@example.com"
                                        className="input-field pl-10"
                                        value={formData.email}
                                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-neutral-700">Employee ID</label>
                                <div className="relative">
                                    <Hash className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" />
                                    <input
                                        required
                                        type="text"
                                        placeholder="BP-2026-001"
                                        className="input-field pl-10"
                                        value={formData.employee_id}
                                        onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-neutral-700">Initial Password</label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" />
                                    <input
                                        required
                                        type="password"
                                        placeholder="••••••••"
                                        className="input-field pl-10"
                                        value={formData.password}
                                        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Roles & Responsibility */}
                    <div className="p-8 bg-neutral-50/50">
                        <h2 className="text-lg font-bold text-neutral-900 mb-6 flex items-center gap-2">
                            <span className="w-8 h-8 rounded-lg bg-neutral-100 flex items-center justify-center text-neutral-500">2</span>
                            Role & Configuration
                        </h2>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-neutral-700">Department</label>
                                <div className="relative">
                                    <Building className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" />
                                    <select
                                        className="input-field pl-10 cursor-pointer"
                                        value={formData.department}
                                        onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                                    >
                                        <option value="">Select Department</option>
                                        <option value="Engineering">Engineering</option>
                                        <option value="Product">Product</option>
                                        <option value="Design">Design</option>
                                        <option value="Operations">Operations</option>
                                        <option value="HR">Human Resources</option>
                                    </select>
                                </div>
                            </div>

                            {!isAdminMode && (
                                <div className="space-y-2">
                                    <label className="text-sm font-semibold text-neutral-700">Expected Daily Hours</label>
                                    <div className="relative">
                                        <Clock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" />
                                        <input
                                            required
                                            type="number"
                                            step="0.5"
                                            min="1"
                                            max="24"
                                            className="input-field pl-10"
                                            value={formData.expected_daily_hours}
                                            onChange={(e) => setFormData({ ...formData, expected_daily_hours: e.target.value })}
                                        />
                                    </div>
                                </div>
                            )}

                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-neutral-700">Account Role</label>
                                <div className="flex gap-4">
                                    <label className={`flex-1 p-4 rounded-xl border-2 cursor-pointer transition-all ${formData.role === 'employee' ? 'border-primary-500 bg-primary-50' : 'border-neutral-100 bg-white hover:border-neutral-200'}`}>
                                        <input
                                            type="radio"
                                            className="hidden"
                                            name="role"
                                            value="employee"
                                            checked={formData.role === 'employee'}
                                            onChange={(e) => setFormData({ ...formData, role: 'employee' })}
                                        />
                                        <div className="flex items-center gap-3">
                                            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${formData.role === 'employee' ? 'bg-primary-500 text-white' : 'bg-neutral-100 text-neutral-500'}`}>
                                                <Briefcase className="w-5 h-5" />
                                            </div>
                                            <span className="font-bold text-neutral-900">Employee</span>
                                        </div>
                                    </label>
                                    <label className={`flex-1 p-4 rounded-xl border-2 cursor-pointer transition-all ${formData.role === 'admin' ? 'border-indigo-500 bg-indigo-100' : 'border-neutral-100 bg-white hover:border-neutral-200'}`}>
                                        <input
                                            type="radio"
                                            className="hidden"
                                            name="role"
                                            value="admin"
                                            checked={formData.role === 'admin'}
                                            onChange={(e) => setFormData({ ...formData, role: 'admin' })}
                                        />
                                        <div className="flex items-center gap-3">
                                            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${formData.role === 'admin' ? 'bg-indigo-500 text-white' : 'bg-neutral-100 text-neutral-500'}`}>
                                                <UserCog className="w-5 h-5" />
                                            </div>
                                            <span className="font-bold text-neutral-900">Admin</span>
                                        </div>
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Footer / Actions */}
                    <div className="p-8 bg-neutral-50 flex flex-col md:flex-row items-center justify-between gap-6">
                        <div className="flex items-start gap-3 max-w-lg">
                            <div className="w-10 h-10 rounded-full bg-warning-100 flex items-center justify-center flex-shrink-0">
                                <AlertCircle className="w-5 h-5 text-warning-600" />
                            </div>
                            <p className="text-sm text-neutral-600">
                                <span className="font-bold text-neutral-900 block mb-1">Important Notice</span>
                                Please ensure the email and employee ID are correct. A notification will be sent (if configured) or the user will need these credentials to sign in.
                            </p>
                        </div>

                        <div className="flex gap-4 w-full md:w-auto">
                            <button
                                type="button"
                                onClick={() => navigate(-1)}
                                className="flex-1 md:flex-none btn-secondary py-3 px-8"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                disabled={loading}
                                className={`flex-1 md:flex-none ${isAdminMode ? 'bg-indigo-600 hover:bg-indigo-700' : 'btn-primary'} text-white py-3 px-12 flex items-center justify-center gap-2 shadow-lg disabled:opacity-50`}
                            >
                                {loading ? (
                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                ) : (
                                    <>
                                        <UserPlus className="w-5 h-5" />
                                        Create Account
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </form>
            </div>

            {error && (
                <div className="mt-6 p-4 bg-danger-50 border border-danger-200 rounded-xl flex items-center gap-3 animate-shake">
                    <AlertCircle className="w-5 h-5 text-danger-600 flex-shrink-0" />
                    <p className="text-danger-800 text-sm font-medium">{error}</p>
                </div>
            )}
        </div>
    );
};

export default AddUser;
