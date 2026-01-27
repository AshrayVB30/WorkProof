import React, { useEffect, useState } from 'react';
import { employeeAPI } from '../lib/api';
import { Clock, Calendar, Activity as ActivityIcon, AlertCircle } from 'lucide-react';

interface TimelineEntry {
    start_time: string;
    end_time: string;
    status: 'active' | 'idle';
    application?: string;
    window_title?: string;
    duration_minutes: number;
}

const Timeline: React.FC = () => {
    const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchTimeline();
    }, [selectedDate]);

    const fetchTimeline = async () => {
        try {
            setLoading(true);
            setError('');
            const response = await employeeAPI.getTimeline(selectedDate);
            setTimeline(response.data.timeline || []);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to load timeline');
            setTimeline([]);
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

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h2 className="text-2xl font-bold text-neutral-900">Activity Timeline</h2>
                <p className="text-neutral-600 mt-1">View your work activity throughout the day</p>
            </div>

            {/* Date Selector */}
            <div className="card shadow-soft animate-slide-up">
                <div className="card-body">
                    <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                            <Calendar className="w-5 h-5 text-primary-600" />
                        </div>
                        <label htmlFor="date" className="text-sm font-semibold text-neutral-700">
                            Select Date:
                        </label>
                        <input
                            id="date"
                            type="date"
                            value={selectedDate}
                            onChange={(e) => setSelectedDate(e.target.value)}
                            max={new Date().toISOString().split('T')[0]}
                            className="input-field"
                        />
                    </div>
                </div>
            </div>

            {/* Timeline */}
            <div className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b border-neutral-200">
                    <h3 className="text-lg font-semibold text-neutral-900">Timeline</h3>
                    <p className="text-sm text-neutral-600 mt-1">Read-only view of your activity</p>
                </div>

                <div className="p-6">
                    {loading ? (
                        <div className="flex items-center justify-center py-12">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                        </div>
                    ) : error ? (
                        <div className="p-4 bg-danger-50 border border-danger-200 rounded-lg flex items-start gap-3">
                            <AlertCircle className="w-5 h-5 text-danger-600 flex-shrink-0 mt-0.5" />
                            <p className="text-sm text-danger-800">{error}</p>
                        </div>
                    ) : timeline.length > 0 ? (
                        <div className="space-y-3">
                            {timeline.map((entry, index) => (
                                <div
                                    key={index}
                                    className={`flex items-start gap-4 p-4 rounded-lg border ${entry.status === 'active'
                                        ? 'bg-success-50 border-success-200'
                                        : 'bg-neutral-50 border-neutral-200'
                                        }`}
                                >
                                    {/* Time Range */}
                                    <div className="flex items-center gap-2 min-w-[140px]">
                                        <Clock className={`w-4 h-4 ${entry.status === 'active' ? 'text-success-600' : 'text-neutral-500'
                                            }`} />
                                        <span className={`text-sm font-medium ${entry.status === 'active' ? 'text-success-900' : 'text-neutral-700'
                                            }`}>
                                            {formatTime(entry.start_time)}–{formatTime(entry.end_time)}
                                        </span>
                                    </div>

                                    {/* Status & Application */}
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2">
                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${entry.status === 'active'
                                                ? 'bg-success-100 text-success-800'
                                                : 'bg-neutral-100 text-neutral-800'
                                                }`}>
                                                {entry.status === 'active' ? '● Active' : '○ Idle'}
                                            </span>
                                            {entry.application && (
                                                <span className="text-sm text-neutral-700">
                                                    ({entry.application})
                                                </span>
                                            )}
                                        </div>
                                        {entry.window_title && entry.status === 'active' && (
                                            <p className="text-xs text-neutral-600 mt-1">{entry.window_title}</p>
                                        )}
                                    </div>

                                    {/* Duration */}
                                    <div className="text-right min-w-[60px]">
                                        <span className="text-sm font-medium text-neutral-900">
                                            {formatDuration(entry.duration_minutes)}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-12 text-neutral-500">
                            <ActivityIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
                            <p>No activity recorded for this date</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Info Note */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-800">
                    <strong className="font-medium">Note:</strong> This timeline shows only metadata about your work sessions.
                    No keystrokes or detailed content is tracked. Screenshots are stored securely and are not visible here.
                </p>
            </div>
        </div>
    );
};

export default Timeline;

