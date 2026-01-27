import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { activityAPI, reportsAPI } from '../lib/api';
import {
    Users,
    Clock,
    TrendingUp,
    Activity,
    CheckCircle,
    AlertCircle
} from 'lucide-react';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface TeamMember {
    user_id: number;
    user_name: string;
    employee_id: string;
    department: string;
    expected_hours: number;
    actual_hours: number;
    active_hours: number;
    productive_percentage: number;
    status: string;
}

const Dashboard: React.FC = () => {
    const { user, isAdmin } = useAuth();
    const [teamData, setTeamData] = useState<TeamMember[]>([]);
    const [liveActivity, setLiveActivity] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchDashboardData();
        // Refresh live activity every 30 seconds
        const interval = setInterval(fetchLiveActivity, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchDashboardData = async () => {
        try {
            setLoading(true);
            if (isAdmin) {
                const [teamResponse, liveResponse] = await Promise.all([
                    reportsAPI.getTeamOverview(),
                    activityAPI.getLiveActivity()
                ]);
                setTeamData(teamResponse.data.employees || []);
                setLiveActivity(liveResponse.data || []);
            }
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchLiveActivity = async () => {
        try {
            if (isAdmin) {
                const response = await activityAPI.getLiveActivity();
                setLiveActivity(response.data || []);
            }
        } catch (error) {
            console.error('Error fetching live activity:', error);
        }
    };

    // Calculate stats
    const totalEmployees = teamData.length;
    const activeEmployees = liveActivity.length;
    const avgProductivity = teamData.length > 0
        ? teamData.reduce((sum, emp) => sum + emp.productive_percentage, 0) / teamData.length
        : 0;
    const onTrackEmployees = teamData.filter(emp => emp.status === 'on_track').length;

    const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'];

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Welcome */}
            <div>
                <h2 className="text-2xl font-bold text-gray-900">
                    Welcome back, {user?.full_name}!
                </h2>
                <p className="text-gray-600 mt-1">
                    {isAdmin ? 'Here\'s your team overview for today' : 'Here\'s your activity summary'}
                </p>
            </div>

            {isAdmin && (
                <>
                    {/* Stats Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        <div className="bg-white rounded-lg shadow p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-medium text-gray-600">Total Employees</p>
                                    <p className="text-3xl font-bold text-gray-900 mt-2">{totalEmployees}</p>
                                </div>
                                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                                    <Users className="w-6 h-6 text-blue-600" />
                                </div>
                            </div>
                        </div>

                        <div className="bg-white rounded-lg shadow p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-medium text-gray-600">Active Now</p>
                                    <p className="text-3xl font-bold text-gray-900 mt-2">{activeEmployees}</p>
                                </div>
                                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                                    <Activity className="w-6 h-6 text-green-600" />
                                </div>
                            </div>
                        </div>

                        <div className="bg-white rounded-lg shadow p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-medium text-gray-600">Avg Productivity</p>
                                    <p className="text-3xl font-bold text-gray-900 mt-2">{avgProductivity.toFixed(1)}%</p>
                                </div>
                                <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center">
                                    <TrendingUp className="w-6 h-6 text-amber-600" />
                                </div>
                            </div>
                        </div>

                        <div className="bg-white rounded-lg shadow p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-medium text-gray-600">On Track</p>
                                    <p className="text-3xl font-bold text-gray-900 mt-2">{onTrackEmployees}</p>
                                </div>
                                <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center">
                                    <CheckCircle className="w-6 h-6 text-emerald-600" />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Live Activity */}
                    <div className="bg-white rounded-lg shadow">
                        <div className="px-6 py-4 border-b border-gray-200">
                            <h3 className="text-lg font-semibold text-gray-900">Live Activity</h3>
                            <p className="text-sm text-gray-600 mt-1">Real-time employee activity status</p>
                        </div>
                        <div className="p-6">
                            {liveActivity.length > 0 ? (
                                <div className="space-y-3">
                                    {liveActivity.map((activity) => (
                                        <div key={activity.user_id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                                                    <span className="text-blue-600 font-semibold text-sm">
                                                        {activity.user_name.charAt(0).toUpperCase()}
                                                    </span>
                                                </div>
                                                <div>
                                                    <p className="font-medium text-gray-900">{activity.user_name}</p>
                                                    <p className="text-sm text-gray-600">{activity.application || 'No application'}</p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${activity.status === 'active'
                                                        ? 'bg-green-100 text-green-800'
                                                        : 'bg-gray-100 text-gray-800'
                                                    }`}>
                                                    {activity.status === 'active' ? '● Active' : '○ Idle'}
                                                </span>
                                                <span className="text-xs text-gray-500">
                                                    {new Date(activity.last_activity).toLocaleTimeString()}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-8 text-gray-500">
                                    <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
                                    <p>No active employees at the moment</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Team Performance */}
                    <div className="bg-white rounded-lg shadow">
                        <div className="px-6 py-4 border-b border-gray-200">
                            <h3 className="text-lg font-semibold text-gray-900">Team Performance</h3>
                            <p className="text-sm text-gray-600 mt-1">Today's productivity overview</p>
                        </div>
                        <div className="p-6">
                            {teamData.length > 0 ? (
                                <div className="overflow-x-auto">
                                    <table className="min-w-full divide-y divide-gray-200">
                                        <thead>
                                            <tr>
                                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Employee
                                                </th>
                                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Department
                                                </th>
                                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Hours Worked
                                                </th>
                                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Productivity
                                                </th>
                                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Status
                                                </th>
                                            </tr>
                                        </thead>
                                        <tbody className="bg-white divide-y divide-gray-200">
                                            {teamData.map((employee) => (
                                                <tr key={employee.user_id} className="hover:bg-gray-50">
                                                    <td className="px-4 py-4 whitespace-nowrap">
                                                        <div className="flex items-center">
                                                            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                                                                <span className="text-blue-600 font-semibold text-xs">
                                                                    {employee.user_name.charAt(0).toUpperCase()}
                                                                </span>
                                                            </div>
                                                            <div>
                                                                <div className="text-sm font-medium text-gray-900">{employee.user_name}</div>
                                                                <div className="text-xs text-gray-500">{employee.employee_id}</div>
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-600">
                                                        {employee.department || 'N/A'}
                                                    </td>
                                                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                                                        {employee.actual_hours.toFixed(1)} / {employee.expected_hours.toFixed(1)} hrs
                                                    </td>
                                                    <td className="px-4 py-4 whitespace-nowrap">
                                                        <div className="flex items-center gap-2">
                                                            <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-[100px]">
                                                                <div
                                                                    className="bg-blue-600 h-2 rounded-full"
                                                                    style={{ width: `${Math.min(employee.productive_percentage, 100)}%` }}
                                                                />
                                                            </div>
                                                            <span className="text-sm font-medium text-gray-900">
                                                                {employee.productive_percentage.toFixed(0)}%
                                                            </span>
                                                        </div>
                                                    </td>
                                                    <td className="px-4 py-4 whitespace-nowrap">
                                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${employee.status === 'on_track'
                                                                ? 'bg-green-100 text-green-800'
                                                                : 'bg-amber-100 text-amber-800'
                                                            }`}>
                                                            {employee.status === 'on_track' ? 'On Track' : 'Behind'}
                                                        </span>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <div className="text-center py-8 text-gray-500">
                                    <Users className="w-12 h-12 mx-auto mb-3 opacity-50" />
                                    <p>No team data available</p>
                                </div>
                            )}
                        </div>
                    </div>
                </>
            )}

            {!isAdmin && (
                <div className="bg-white rounded-lg shadow p-6">
                    <div className="text-center py-12">
                        <Clock className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">Employee Dashboard</h3>
                        <p className="text-gray-600">
                            Your personal activity dashboard will be displayed here.
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Dashboard;
