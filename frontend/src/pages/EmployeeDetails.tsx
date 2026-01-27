import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { adminAPI } from '../lib/api';
import { ArrowLeft, User, Mail, Briefcase, Clock, Activity, TrendingUp, Calendar, AlertCircle, Image as ImageIcon } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface EmployeeDetails {
    id: number;
    employee_id: string;
    full_name: string;
    email: string;
    department: string;
    expected_hours: number;
    today: {
        hours_worked: number;
        active_hours: number;
        idle_hours: number;
        productivity_percentage: number;
        status: string;
    };
    timeline: Array<{
        start_time: string;
        end_time: string;
        status: 'active' | 'idle';
        application?: string;
        duration_minutes: number;
    }>;
    application_breakdown: Array<{
        application: string;
        hours: number;
        percentage: number;
    }>;
    performance_trend: Array<{
        date: string;
        hours: number;
        productivity: number;
    }>;
    screenshots: Array<{
        timestamp: string;
        url: string;
    }>;
}

const EmployeeDetails: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [employee, setEmployee] = useState<EmployeeDetails | null>(null);
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        if (id) {
            fetchEmployeeDetails();
        }
    }, [id, selectedDate]);

    const fetchEmployeeDetails = async () => {
        try {
            setLoading(true);
            setError('');
            const response = await adminAPI.getEmployeeDetails(parseInt(id!));
            const activityResponse = await adminAPI.getEmployeeActivity(parseInt(id!), selectedDate);

            setEmployee({
                ...response.data,
                ...activityResponse.data
            });
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to load employee details');
            setEmployee(null);
        } finally {
            setLoading(false);
        }
    };

    const formatTime = (timeString: string) => {
        return new Date(timeString).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        });
    };

    const formatDuration = (minutes: number) => {
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        if (hours > 0) {
            return `${hours}h ${mins}m`;
        }
        return `${mins}m`;
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    if (error || !employee) {
        return (
            <div className="space-y-6">
                <button
                    onClick={() => navigate('/employees')}
                    className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
                >
                    <ArrowLeft className="w-5 h-5" />
                    Back to Employees
                </button>
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-red-800">{error || 'Employee not found'}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <button
                    onClick={() => navigate('/employees')}
                    className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
                >
                    <ArrowLeft className="w-5 h-5" />
                    Back to Employees
                </button>
            </div>

            {/* Employee Profile */}
            <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-start gap-6">
                    <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-blue-600 font-bold text-2xl">
                            {employee.full_name.charAt(0).toUpperCase()}
                        </span>
                    </div>
                    <div className="flex-1">
                        <h2 className="text-2xl font-bold text-gray-900">{employee.full_name}</h2>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                            <div className="flex items-center gap-2 text-gray-600">
                                <User className="w-4 h-4" />
                                <span className="text-sm">{employee.employee_id}</span>
                            </div>
                            <div className="flex items-center gap-2 text-gray-600">
                                <Mail className="w-4 h-4" />
                                <span className="text-sm">{employee.email}</span>
                            </div>
                            <div className="flex items-center gap-2 text-gray-600">
                                <Briefcase className="w-4 h-4" />
                                <span className="text-sm">{employee.department || 'N/A'}</span>
                            </div>
                        </div>
                    </div>
                </div>
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

            {/* Today's Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-600">Hours Worked</p>
                            <p className="text-3xl font-bold text-gray-900 mt-2">
                                {employee.today.hours_worked.toFixed(1)}h
                            </p>
                            <p className="text-xs text-gray-500 mt-1">
                                of {employee.expected_hours.toFixed(1)}h
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
                            <p className="text-3xl font-bold text-green-600 mt-2">
                                {employee.today.active_hours.toFixed(1)}h
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
                            <p className="text-sm font-medium text-gray-600">Idle Time</p>
                            <p className="text-3xl font-bold text-amber-600 mt-2">
                                {employee.today.idle_hours.toFixed(1)}h
                            </p>
                        </div>
                        <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center">
                            <Clock className="w-6 h-6 text-amber-600" />
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-600">Productivity</p>
                            <p className="text-3xl font-bold text-blue-600 mt-2">
                                {employee.today.productivity_percentage.toFixed(0)}%
                            </p>
                        </div>
                        <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                            <TrendingUp className="w-6 h-6 text-purple-600" />
                        </div>
                    </div>
                </div>
            </div>

            {/* Hour-by-Hour Timeline */}
            <div className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900">Activity Timeline</h3>
                    <p className="text-sm text-gray-600 mt-1">Hour-by-hour breakdown</p>
                </div>
                <div className="p-6">
                    {employee.timeline && employee.timeline.length > 0 ? (
                        <div className="space-y-3">
                            {employee.timeline.map((entry, index) => (
                                <div
                                    key={index}
                                    className={`flex items-start gap-4 p-4 rounded-lg border ${entry.status === 'active'
                                            ? 'bg-green-50 border-green-200'
                                            : 'bg-gray-50 border-gray-200'
                                        }`}
                                >
                                    <div className="flex items-center gap-2 min-w-[140px]">
                                        <Clock className={`w-4 h-4 ${entry.status === 'active' ? 'text-green-600' : 'text-gray-500'
                                            }`} />
                                        <span className={`text-sm font-medium ${entry.status === 'active' ? 'text-green-900' : 'text-gray-700'
                                            }`}>
                                            {formatTime(entry.start_time)}–{formatTime(entry.end_time)}
                                        </span>
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2">
                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${entry.status === 'active'
                                                    ? 'bg-green-100 text-green-800'
                                                    : 'bg-gray-100 text-gray-800'
                                                }`}>
                                                {entry.status === 'active' ? '● Active' : '○ Idle'}
                                            </span>
                                            {entry.application && (
                                                <span className="text-sm text-gray-700">
                                                    ({entry.application})
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                    <div className="text-right min-w-[60px]">
                                        <span className="text-sm font-medium text-gray-900">
                                            {formatDuration(entry.duration_minutes)}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-8 text-gray-500">
                            <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
                            <p>No activity recorded</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Application Breakdown */}
            <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Application Usage</h3>
                {employee.application_breakdown && employee.application_breakdown.length > 0 ? (
                    <div className="space-y-3">
                        {employee.application_breakdown.map((app, index) => (
                            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                <span className="font-medium text-gray-900">{app.application}</span>
                                <div className="flex items-center gap-3">
                                    <div className="w-32 bg-gray-200 rounded-full h-2">
                                        <div
                                            className="bg-blue-600 h-2 rounded-full"
                                            style={{ width: `${app.percentage}%` }}
                                        />
                                    </div>
                                    <span className="text-sm font-semibold text-gray-900 min-w-[60px] text-right">
                                        {app.hours.toFixed(1)}h ({app.percentage.toFixed(0)}%)
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-8 text-gray-500">
                        <p>No application data available</p>
                    </div>
                )}
            </div>

            {/* Performance Trend */}
            {employee.performance_trend && employee.performance_trend.length > 0 && (
                <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">7-Day Performance Trend</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={employee.performance_trend}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="date" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Line type="monotone" dataKey="hours" stroke="#3b82f6" name="Hours Worked" />
                            <Line type="monotone" dataKey="productivity" stroke="#10b981" name="Productivity %" />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            )}

            {/* Screenshots (View on Demand) */}
            <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center gap-2 mb-4">
                    <ImageIcon className="w-5 h-5 text-gray-600" />
                    <h3 className="text-lg font-semibold text-gray-900">Screenshots</h3>
                    <span className="text-xs text-gray-500">(View on demand for disputes)</span>
                </div>
                {employee.screenshots && employee.screenshots.length > 0 ? (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {employee.screenshots.map((screenshot, index) => (
                            <div key={index} className="border border-gray-200 rounded-lg p-2">
                                <div className="aspect-video bg-gray-100 rounded flex items-center justify-center mb-2">
                                    <ImageIcon className="w-8 h-8 text-gray-400" />
                                </div>
                                <p className="text-xs text-gray-600 text-center">
                                    {formatTime(screenshot.timestamp)}
                                </p>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-8 text-gray-500">
                        <ImageIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
                        <p>No screenshots available</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default EmployeeDetails;
