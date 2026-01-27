import React, { useEffect, useState } from 'react';
import { employeeAPI } from '../lib/api';
import { Calendar, Clock, TrendingUp, Activity, CheckCircle, AlertCircle, BarChart3 } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

interface DailySummaryData {
    date: string;
    total_hours: number;
    active_hours: number;
    idle_hours: number;
    expected_hours: number;
    productivity_percentage: number;
    report_status: 'pending' | 'submitted' | 'verified';
    application_breakdown: Array<{
        application: string;
        hours: number;
        percentage: number;
    }>;
}

const DailySummary: React.FC = () => {
    const [summary, setSummary] = useState<DailySummaryData | null>(null);
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchDailySummary();
    }, [selectedDate]);

    const fetchDailySummary = async () => {
        try {
            setLoading(true);
            setError('');
            const response = await employeeAPI.getDailySummary(selectedDate);
            setSummary(response.data);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to load daily summary');
            setSummary(null);
        } finally {
            setLoading(false);
        }
    };

    const getStatusBadge = (status: string) => {
        const badges = {
            pending: { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: '⏳', label: 'Pending' },
            submitted: { bg: 'bg-blue-100', text: 'text-blue-800', icon: '📤', label: 'Submitted' },
            verified: { bg: 'bg-green-100', text: 'text-green-800', icon: '✅', label: 'Verified' },
        };
        const badge = badges[status as keyof typeof badges] || badges.pending;
        return (
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${badge.bg} ${badge.text}`}>
                {badge.icon} {badge.label}
            </span>
        );
    };

    const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h2 className="text-2xl font-bold text-gray-900">Daily Summary</h2>
                <p className="text-gray-600 mt-1">Your work metrics and activity breakdown</p>
            </div>

            {/* Date Selector */}
            <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center gap-4">
                    <Calendar className="w-5 h-5 text-gray-500" />
                    <label htmlFor="date" className="text-sm font-medium text-gray-700">
                        Select Date:
                    </label>
                    <input
                        id="date"
                        type="date"
                        value={selectedDate}
                        onChange={(e) => setSelectedDate(e.target.value)}
                        max={new Date().toISOString().split('T')[0]}
                        className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                </div>
            </div>

            {error ? (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-red-800">{error}</p>
                </div>
            ) : summary ? (
                <>
                    {/* Stats Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        <div className="bg-white rounded-lg shadow p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-medium text-gray-600">Total Hours</p>
                                    <p className="text-3xl font-bold text-gray-900 mt-2">
                                        {summary.total_hours.toFixed(1)}h
                                    </p>
                                </div>
                                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                                    <Clock className="w-6 h-6 text-blue-600" />
                                </div>
                            </div>
                        </div>

                        <div className="bg-white rounded-lg shadow p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-medium text-gray-600">Active Time</p>
                                    <p className="text-3xl font-bold text-gray-900 mt-2">
                                        {summary.active_hours.toFixed(1)}h
                                    </p>
                                </div>
                                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                                    <Activity className="w-6 h-6 text-green-600" />
                                </div>
                            </div>
                        </div>

                        <div className="bg-white rounded-lg shadow p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-medium text-gray-600">Productivity</p>
                                    <p className="text-3xl font-bold text-gray-900 mt-2">
                                        {summary.productivity_percentage.toFixed(0)}%
                                    </p>
                                </div>
                                <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center">
                                    <TrendingUp className="w-6 h-6 text-amber-600" />
                                </div>
                            </div>
                        </div>

                        <div className="bg-white rounded-lg shadow p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-medium text-gray-600">Report Status</p>
                                    <div className="mt-2">
                                        {getStatusBadge(summary.report_status)}
                                    </div>
                                </div>
                                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                                    <CheckCircle className="w-6 h-6 text-purple-600" />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <div className="flex items-center justify-between mb-4">
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900">Daily Progress</h3>
                                <p className="text-sm text-gray-600 mt-1">
                                    {summary.active_hours.toFixed(1)}h / {summary.expected_hours.toFixed(1)}h required
                                </p>
                            </div>
                            <span className={`text-2xl font-bold ${summary.active_hours >= summary.expected_hours ? 'text-green-600' : 'text-amber-600'
                                }`}>
                                {((summary.active_hours / summary.expected_hours) * 100).toFixed(0)}%
                            </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-4">
                            <div
                                className={`h-4 rounded-full transition-all ${summary.active_hours >= summary.expected_hours ? 'bg-green-600' : 'bg-amber-600'
                                    }`}
                                style={{ width: `${Math.min((summary.active_hours / summary.expected_hours) * 100, 100)}%` }}
                            />
                        </div>
                    </div>

                    {/* Application Breakdown */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Application Breakdown</h3>
                        {summary.application_breakdown && summary.application_breakdown.length > 0 ? (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {/* Pie Chart */}
                                <div className="h-64">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <PieChart>
                                            <Pie
                                                data={summary.application_breakdown}
                                                dataKey="hours"
                                                nameKey="application"
                                                cx="50%"
                                                cy="50%"
                                                outerRadius={80}
                                                label={(entry) => `${entry.percentage.toFixed(0)}%`}
                                            >
                                                {summary.application_breakdown.map((entry, index) => (
                                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                                ))}
                                            </Pie>
                                            <Tooltip />
                                            <Legend />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>

                                {/* List */}
                                <div className="space-y-3">
                                    {summary.application_breakdown.map((app, index) => (
                                        <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                            <div className="flex items-center gap-3">
                                                <div
                                                    className="w-4 h-4 rounded-full"
                                                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                                                />
                                                <span className="font-medium text-gray-900">{app.application}</span>
                                            </div>
                                            <div className="text-right">
                                                <span className="text-sm font-semibold text-gray-900">
                                                    {app.hours.toFixed(1)}h
                                                </span>
                                                <span className="text-xs text-gray-500 ml-2">
                                                    ({app.percentage.toFixed(0)}%)
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ) : (
                            <div className="text-center py-8 text-gray-500">
                                <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-50" />
                                <p>No application data available</p>
                            </div>
                        )}
                    </div>

                    {/* Info Note */}
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <p className="text-sm text-blue-800">
                            <strong className="font-medium">Transparency:</strong> This summary provides complete visibility
                            into your tracked work. All data is available for your review to avoid any surprises.
                        </p>
                    </div>
                </>
            ) : (
                <div className="text-center py-12 text-gray-500 bg-white rounded-lg shadow">
                    <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No summary data available for this date</p>
                </div>
            )}
        </div>
    );
};

export default DailySummary;
