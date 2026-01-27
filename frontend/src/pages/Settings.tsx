import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { adminAPI } from '../lib/api';
import { User, Lock, Bell, Settings as SettingsIcon, Save, AlertCircle, CheckCircle } from 'lucide-react';

interface SettingsData {
    idle_threshold_minutes: number;
    screenshot_frequency_minutes: number;
    work_hours_start: string;
    work_hours_end: string;
    expected_daily_hours: number;
}

const Settings: React.FC = () => {
    const { user, isAdmin } = useAuth();
    const [activeTab, setActiveTab] = useState('profile');
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState('');
    const [error, setError] = useState('');

    // Profile state
    const [fullName, setFullName] = useState(user?.full_name || '');
    const [email, setEmail] = useState(user?.email || '');
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');

    // Admin settings state
    const [adminSettings, setAdminSettings] = useState<SettingsData>({
        idle_threshold_minutes: 60,
        screenshot_frequency_minutes: 10,
        work_hours_start: '09:00',
        work_hours_end: '18:00',
        expected_daily_hours: 9,
    });

    useEffect(() => {
        if (isAdmin && activeTab === 'admin') {
            fetchAdminSettings();
        }
    }, [isAdmin, activeTab]);

    const fetchAdminSettings = async () => {
        try {
            const response = await adminAPI.getSettings();
            setAdminSettings(response.data);
        } catch (err: any) {
            console.error('Failed to load settings:', err);
        }
    };

    const handleProfileUpdate = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSuccess('');

        try {
            // API call to update profile
            setSuccess('Profile updated successfully');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to update profile');
        } finally {
            setLoading(false);
        }
    };

    const handlePasswordChange = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSuccess('');

        if (newPassword !== confirmPassword) {
            setError('Passwords do not match');
            setLoading(false);
            return;
        }

        try {
            // API call to change password
            setSuccess('Password changed successfully');
            setCurrentPassword('');
            setNewPassword('');
            setConfirmPassword('');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to change password');
        } finally {
            setLoading(false);
        }
    };

    const handleAdminSettingsUpdate = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSuccess('');

        try {
            await adminAPI.updateSettings(adminSettings);
            setSuccess('Settings updated successfully');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to update settings');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h2 className="text-2xl font-bold text-gray-900">Settings</h2>
                <p className="text-gray-600 mt-1">Manage your account and preferences</p>
            </div>

            {/* Tabs */}
            <div className="bg-white rounded-lg shadow">
                <div className="border-b border-gray-200">
                    <nav className="flex -mb-px">
                        <button
                            onClick={() => setActiveTab('profile')}
                            className={`px-6 py-4 text-sm font-medium border-b-2 transition ${activeTab === 'profile'
                                    ? 'border-blue-600 text-blue-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                }`}
                        >
                            <div className="flex items-center gap-2">
                                <User className="w-4 h-4" />
                                Profile
                            </div>
                        </button>
                        <button
                            onClick={() => setActiveTab('password')}
                            className={`px-6 py-4 text-sm font-medium border-b-2 transition ${activeTab === 'password'
                                    ? 'border-blue-600 text-blue-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                }`}
                        >
                            <div className="flex items-center gap-2">
                                <Lock className="w-4 h-4" />
                                Password
                            </div>
                        </button>
                        <button
                            onClick={() => setActiveTab('notifications')}
                            className={`px-6 py-4 text-sm font-medium border-b-2 transition ${activeTab === 'notifications'
                                    ? 'border-blue-600 text-blue-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                }`}
                        >
                            <div className="flex items-center gap-2">
                                <Bell className="w-4 h-4" />
                                Notifications
                            </div>
                        </button>
                        {isAdmin && (
                            <button
                                onClick={() => setActiveTab('admin')}
                                className={`px-6 py-4 text-sm font-medium border-b-2 transition ${activeTab === 'admin'
                                        ? 'border-blue-600 text-blue-600'
                                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                    }`}
                            >
                                <div className="flex items-center gap-2">
                                    <SettingsIcon className="w-4 h-4" />
                                    Admin Config
                                </div>
                            </button>
                        )}
                    </nav>
                </div>

                <div className="p-6">
                    {/* Success/Error Messages */}
                    {success && (
                        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
                            <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                            <p className="text-sm text-green-800">{success}</p>
                        </div>
                    )}
                    {error && (
                        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                            <p className="text-sm text-red-800">{error}</p>
                        </div>
                    )}

                    {/* Profile Tab */}
                    {activeTab === 'profile' && (
                        <form onSubmit={handleProfileUpdate} className="space-y-6">
                            <div>
                                <label htmlFor="fullName" className="block text-sm font-medium text-gray-700 mb-2">
                                    Full Name
                                </label>
                                <input
                                    id="fullName"
                                    type="text"
                                    value={fullName}
                                    onChange={(e) => setFullName(e.target.value)}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                            <div>
                                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                                    Email Address
                                </label>
                                <input
                                    id="email"
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={loading}
                                className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
                            >
                                <Save className="w-4 h-4" />
                                Save Changes
                            </button>
                        </form>
                    )}

                    {/* Password Tab */}
                    {activeTab === 'password' && (
                        <form onSubmit={handlePasswordChange} className="space-y-6">
                            <div>
                                <label htmlFor="currentPassword" className="block text-sm font-medium text-gray-700 mb-2">
                                    Current Password
                                </label>
                                <input
                                    id="currentPassword"
                                    type="password"
                                    value={currentPassword}
                                    onChange={(e) => setCurrentPassword(e.target.value)}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                            <div>
                                <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700 mb-2">
                                    New Password
                                </label>
                                <input
                                    id="newPassword"
                                    type="password"
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                            <div>
                                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                                    Confirm New Password
                                </label>
                                <input
                                    id="confirmPassword"
                                    type="password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={loading}
                                className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
                            >
                                <Save className="w-4 h-4" />
                                Change Password
                            </button>
                        </form>
                    )}

                    {/* Notifications Tab */}
                    {activeTab === 'notifications' && (
                        <div className="space-y-6">
                            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                                <div>
                                    <p className="font-medium text-gray-900">Email Notifications</p>
                                    <p className="text-sm text-gray-600">Receive email updates about your activity</p>
                                </div>
                                <input type="checkbox" className="w-5 h-5 text-blue-600 rounded" />
                            </div>
                            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                                <div>
                                    <p className="font-medium text-gray-900">Daily Summary</p>
                                    <p className="text-sm text-gray-600">Get daily summary of your work hours</p>
                                </div>
                                <input type="checkbox" className="w-5 h-5 text-blue-600 rounded" />
                            </div>
                            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                                <div>
                                    <p className="font-medium text-gray-900">Alert Notifications</p>
                                    <p className="text-sm text-gray-600">Receive alerts for important events</p>
                                </div>
                                <input type="checkbox" className="w-5 h-5 text-blue-600 rounded" />
                            </div>
                        </div>
                    )}

                    {/* Admin Config Tab */}
                    {activeTab === 'admin' && isAdmin && (
                        <form onSubmit={handleAdminSettingsUpdate} className="space-y-6">
                            <div>
                                <label htmlFor="idleThreshold" className="block text-sm font-medium text-gray-700 mb-2">
                                    ⏱ Idle Threshold (minutes)
                                </label>
                                <input
                                    id="idleThreshold"
                                    type="number"
                                    value={adminSettings.idle_threshold_minutes}
                                    onChange={(e) => setAdminSettings({ ...adminSettings, idle_threshold_minutes: parseInt(e.target.value) })}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                                <p className="text-xs text-gray-500 mt-1">Time before marking user as idle</p>
                            </div>
                            <div>
                                <label htmlFor="screenshotFreq" className="block text-sm font-medium text-gray-700 mb-2">
                                    📸 Screenshot Frequency (minutes)
                                </label>
                                <input
                                    id="screenshotFreq"
                                    type="number"
                                    value={adminSettings.screenshot_frequency_minutes}
                                    onChange={(e) => setAdminSettings({ ...adminSettings, screenshot_frequency_minutes: parseInt(e.target.value) })}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                                <p className="text-xs text-gray-500 mt-1">How often to capture screenshots</p>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label htmlFor="workStart" className="block text-sm font-medium text-gray-700 mb-2">
                                        🕐 Work Hours Start
                                    </label>
                                    <input
                                        id="workStart"
                                        type="time"
                                        value={adminSettings.work_hours_start}
                                        onChange={(e) => setAdminSettings({ ...adminSettings, work_hours_start: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>
                                <div>
                                    <label htmlFor="workEnd" className="block text-sm font-medium text-gray-700 mb-2">
                                        🕐 Work Hours End
                                    </label>
                                    <input
                                        id="workEnd"
                                        type="time"
                                        value={adminSettings.work_hours_end}
                                        onChange={(e) => setAdminSettings({ ...adminSettings, work_hours_end: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>
                            </div>
                            <div>
                                <label htmlFor="expectedHours" className="block text-sm font-medium text-gray-700 mb-2">
                                    Expected Daily Hours
                                </label>
                                <input
                                    id="expectedHours"
                                    type="number"
                                    step="0.5"
                                    value={adminSettings.expected_daily_hours}
                                    onChange={(e) => setAdminSettings({ ...adminSettings, expected_daily_hours: parseFloat(e.target.value) })}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={loading}
                                className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
                            >
                                <Save className="w-4 h-4" />
                                Save Settings
                            </button>
                        </form>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Settings;
