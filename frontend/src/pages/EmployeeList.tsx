import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminAPI } from '../lib/api';
import { Users, Search, Filter, Download, AlertCircle, TrendingUp, TrendingDown, UserPlus } from 'lucide-react';

interface Employee {
    id: number;
    employee_id: string;
    full_name: string;
    email: string;
    department: string;
    hours_worked: number;
    expected_hours: number;
    productivity_percentage: number;
    status: 'on_track' | 'below_target' | 'alert';
    last_active: string;
}

const EmployeeList: React.FC = () => {
    const [employees, setEmployees] = useState<Employee[]>([]);
    const [filteredEmployees, setFilteredEmployees] = useState<Employee[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState<string>('all');
    const [departmentFilter, setDepartmentFilter] = useState<string>('all');
    const navigate = useNavigate();

    useEffect(() => {
        fetchEmployees();
    }, []);

    useEffect(() => {
        filterEmployees();
    }, [employees, searchTerm, statusFilter, departmentFilter]);

    const fetchEmployees = async () => {
        try {
            setLoading(true);
            setError('');
            const response = await adminAPI.getEmployees();
            setEmployees(response.data.employees || []);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to load employees');
            setEmployees([]);
        } finally {
            setLoading(false);
        }
    };

    const filterEmployees = () => {
        let filtered = [...employees];

        // Search filter
        if (searchTerm) {
            filtered = filtered.filter(emp =>
                emp.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                emp.employee_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                emp.email.toLowerCase().includes(searchTerm.toLowerCase())
            );
        }

        // Status filter
        if (statusFilter !== 'all') {
            filtered = filtered.filter(emp => emp.status === statusFilter);
        }

        // Department filter
        if (departmentFilter !== 'all') {
            filtered = filtered.filter(emp => emp.department === departmentFilter);
        }

        setFilteredEmployees(filtered);
    };

    const getStatusBadge = (status: string) => {
        const badges = {
            on_track: { bg: 'bg-green-100', text: 'text-green-800', icon: '✅', label: 'On Track' },
            below_target: { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: '⚠️', label: 'Below Target' },
            alert: { bg: 'bg-red-100', text: 'text-red-800', icon: '❌', label: 'Alert' },
        };
        const badge = badges[status as keyof typeof badges] || badges.on_track;
        return (
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badge.bg} ${badge.text}`}>
                {badge.icon} {badge.label}
            </span>
        );
    };

    const departments = ['all', ...new Set(employees.map(emp => emp.department).filter(Boolean))];

    // Calculate stats
    const totalEmployees = employees.length;
    const activeEmployees = employees.filter(emp => emp.status === 'on_track').length;
    const belowTarget = employees.filter(emp => emp.status === 'below_target').length;
    const alerts = employees.filter(emp => emp.status === 'alert').length;

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
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">Employee Management</h2>
                    <p className="text-gray-600 mt-1">Monitor and manage employee work verification</p>
                </div>
                <button
                    onClick={() => navigate('/admin/add-employee')}
                    className="btn-primary py-2.5 px-6 flex items-center gap-2 shadow-md hover:shadow-lg transition-all"
                >
                    <UserPlus className="w-5 h-5" />
                    Add Employee
                </button>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
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
                            <p className="text-sm font-medium text-gray-600">On Track</p>
                            <p className="text-3xl font-bold text-green-600 mt-2">{activeEmployees}</p>
                        </div>
                        <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                            <TrendingUp className="w-6 h-6 text-green-600" />
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-600">Below Target</p>
                            <p className="text-3xl font-bold text-yellow-600 mt-2">{belowTarget}</p>
                        </div>
                        <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                            <TrendingDown className="w-6 h-6 text-yellow-600" />
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-600">Alerts</p>
                            <p className="text-3xl font-bold text-red-600 mt-2">{alerts}</p>
                        </div>
                        <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                            <AlertCircle className="w-6 h-6 text-red-600" />
                        </div>
                    </div>
                </div>
            </div>

            {/* Filters */}
            <div className="bg-white rounded-lg shadow p-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {/* Search */}
                    <div className="md:col-span-2">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                            <input
                                type="text"
                                placeholder="Search by name, ID, or email..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>
                    </div>

                    {/* Status Filter */}
                    <div>
                        <select
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            <option value="all">All Status</option>
                            <option value="on_track">On Track</option>
                            <option value="below_target">Below Target</option>
                            <option value="alert">Alert</option>
                        </select>
                    </div>

                    {/* Department Filter */}
                    <div>
                        <select
                            value={departmentFilter}
                            onChange={(e) => setDepartmentFilter(e.target.value)}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            {departments.map(dept => (
                                <option key={dept} value={dept}>
                                    {dept === 'all' ? 'All Departments' : dept}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>
            </div>

            {/* Employee Table */}
            <div className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-900">
                        Employees ({filteredEmployees.length})
                    </h3>
                    <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                        <Download className="w-4 h-4" />
                        Export
                    </button>
                </div>

                <div className="overflow-x-auto">
                    {error ? (
                        <div className="p-6">
                            <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                                <p className="text-sm text-red-800">{error}</p>
                            </div>
                        </div>
                    ) : filteredEmployees.length > 0 ? (
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Employee
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Department
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Hours Worked
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Productivity
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Status
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Actions
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {filteredEmployees.map((employee) => (
                                    <tr
                                        key={employee.id}
                                        className="hover:bg-gray-50 cursor-pointer"
                                        onClick={() => navigate(`/employees/${employee.id}`)}
                                    >
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center">
                                                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                                                    <span className="text-blue-600 font-semibold text-sm">
                                                        {employee.full_name.charAt(0).toUpperCase()}
                                                    </span>
                                                </div>
                                                <div>
                                                    <div className="text-sm font-medium text-gray-900">{employee.full_name}</div>
                                                    <div className="text-xs text-gray-500">{employee.employee_id}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                            {employee.department || 'N/A'}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                            {employee.hours_worked.toFixed(1)}h / {employee.expected_hours.toFixed(1)}h
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center gap-2">
                                                <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-[100px]">
                                                    <div
                                                        className="bg-blue-600 h-2 rounded-full"
                                                        style={{ width: `${Math.min(employee.productivity_percentage, 100)}%` }}
                                                    />
                                                </div>
                                                <span className="text-sm font-medium text-gray-900">
                                                    {employee.productivity_percentage.toFixed(0)}%
                                                </span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            {getStatusBadge(employee.status)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    navigate(`/employees/${employee.id}`);
                                                }}
                                                className="text-blue-600 hover:text-blue-800 font-medium"
                                            >
                                                View Details
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    ) : (
                        <div className="text-center py-12 text-gray-500">
                            <Users className="w-12 h-12 mx-auto mb-3 opacity-50" />
                            <p>No employees found</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default EmployeeList;
