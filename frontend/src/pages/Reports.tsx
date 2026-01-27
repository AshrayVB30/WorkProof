import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { reportsAPI } from '../lib/api';
import { FileText, Download, Calendar } from 'lucide-react';
import { format } from 'date-fns';

const Reports: React.FC = () => {
    const { user, isAdmin } = useAuth();
    const [startDate, setStartDate] = useState(format(new Date(), 'yyyy-MM-dd'));
    const [endDate, setEndDate] = useState(format(new Date(), 'yyyy-MM-dd'));
    const [reports, setReports] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [selectedUserId, setSelectedUserId] = useState<number>(user?.id || 0);

    useEffect(() => {
        if (user) {
            setSelectedUserId(user.id);
            fetchReports();
        }
    }, [user]);

    const fetchReports = async () => {
        if (!selectedUserId) return;

        try {
            setLoading(true);
            const response = await reportsAPI.getReportsRange(selectedUserId, startDate, endDate);
            setReports(response.data);
        } catch (error) {
            console.error('Error fetching reports:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleExportPDF = async () => {
        try {
            const response = await reportsAPI.exportPDF(selectedUserId, startDate, endDate);
            const blob = new Blob([response.data], { type: 'application/pdf' });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `workproof_report_${startDate}_${endDate}.pdf`;
            link.click();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error exporting PDF:', error);
        }
    };

    const handleExportExcel = async () => {
        try {
            const response = await reportsAPI.exportExcel(selectedUserId, startDate, endDate);
            const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `workproof_report_${startDate}_${endDate}.xlsx`;
            link.click();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error exporting Excel:', error);
        }
    };

    const totalHours = reports.reduce((sum, r) => sum + r.total_hours, 0);
    const totalActiveHours = reports.reduce((sum, r) => sum + r.active_hours, 0);
    const avgProductivity = reports.length > 0
        ? reports.reduce((sum, r) => sum + r.productive_percentage, 0) / reports.length
        : 0;

    return (
        <div className="space-y-6">
            {/* Filters */}
            <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Generate Report</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Start Date
                        </label>
                        <input
                            type="date"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            End Date
                        </label>
                        <input
                            type="date"
                            value={endDate}
                            onChange={(e) => setEndDate(e.target.value)}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>
                    <div className="flex items-end">
                        <button
                            onClick={fetchReports}
                            disabled={loading}
                            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 transition disabled:opacity-50"
                        >
                            {loading ? 'Loading...' : 'Generate Report'}
                        </button>
                    </div>
                </div>
            </div>

            {/* Summary */}
            {reports.length > 0 && (
                <>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="bg-white rounded-lg shadow p-6">
                            <p className="text-sm font-medium text-gray-600">Total Hours</p>
                            <p className="text-3xl font-bold text-gray-900 mt-2">{totalHours.toFixed(1)}</p>
                            <p className="text-sm text-gray-500 mt-1">{reports.length} days</p>
                        </div>
                        <div className="bg-white rounded-lg shadow p-6">
                            <p className="text-sm font-medium text-gray-600">Active Hours</p>
                            <p className="text-3xl font-bold text-gray-900 mt-2">{totalActiveHours.toFixed(1)}</p>
                            <p className="text-sm text-gray-500 mt-1">Productive time</p>
                        </div>
                        <div className="bg-white rounded-lg shadow p-6">
                            <p className="text-sm font-medium text-gray-600">Avg Productivity</p>
                            <p className="text-3xl font-bold text-gray-900 mt-2">{avgProductivity.toFixed(1)}%</p>
                            <p className="text-sm text-gray-500 mt-1">Overall performance</p>
                        </div>
                    </div>

                    {/* Export Buttons */}
                    <div className="flex gap-4">
                        <button
                            onClick={handleExportPDF}
                            className="flex items-center gap-2 bg-red-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-red-700 transition"
                        >
                            <Download className="w-4 h-4" />
                            Export PDF
                        </button>
                        <button
                            onClick={handleExportExcel}
                            className="flex items-center gap-2 bg-green-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-green-700 transition"
                        >
                            <Download className="w-4 h-4" />
                            Export Excel
                        </button>
                    </div>

                    {/* Daily Reports Table */}
                    <div className="bg-white rounded-lg shadow">
                        <div className="px-6 py-4 border-b border-gray-200">
                            <h3 className="text-lg font-semibold text-gray-900">Daily Breakdown</h3>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Date
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Total Hours
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Active Hours
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Idle Hours
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Productivity
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Activities
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {reports.map((report) => (
                                        <tr key={report.id} className="hover:bg-gray-50">
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                {new Date(report.report_date).toLocaleDateString()}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                                {report.total_hours.toFixed(2)} hrs
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                                {report.active_hours.toFixed(2)} hrs
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                                {report.idle_hours.toFixed(2)} hrs
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <div className="flex items-center gap-2">
                                                    <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-[100px]">
                                                        <div
                                                            className="bg-blue-600 h-2 rounded-full"
                                                            style={{ width: `${Math.min(report.productive_percentage, 100)}%` }}
                                                        />
                                                    </div>
                                                    <span className="text-sm font-medium text-gray-900">
                                                        {report.productive_percentage.toFixed(0)}%
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                                {report.total_activities}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </>
            )}

            {reports.length === 0 && !loading && (
                <div className="bg-white rounded-lg shadow p-12 text-center">
                    <FileText className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">No Reports Available</h3>
                    <p className="text-gray-600">
                        Select a date range and click "Generate Report" to view your activity reports.
                    </p>
                </div>
            )}
        </div>
    );
};

export default Reports;
