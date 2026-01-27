import React, { ReactNode } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
    LayoutDashboard,
    Users,
    FileText,
    Settings,
    LogOut,
    Menu,
    X,
    Clock,
    BarChart3,
    UserPlus,
    UserCircle
} from 'lucide-react';

interface DashboardLayoutProps {
    children: ReactNode;
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
    const { user, logout, isAdmin } = useAuth();
    const location = useLocation();
    const navigate = useNavigate();
    const [sidebarOpen, setSidebarOpen] = React.useState(false);

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    // Role-based navigation
    const employeeNavigation = [
        { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
        { name: 'Timeline', href: '/timeline', icon: Clock },
        { name: 'Daily Summary', href: '/daily-summary', icon: BarChart3 },
        { name: 'Settings', href: '/settings', icon: Settings },
    ];

    const adminNavigation = [
        { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
        { name: 'Employees', href: '/employees', icon: Users },
        { name: 'Add Employee', href: '/admin/add-employee', icon: UserPlus },
        { name: 'Add Admin', href: '/admin/add-admin', icon: UserCircle },
        { name: 'Reports', href: '/reports', icon: FileText },
        { name: 'Settings', href: '/settings', icon: Settings },
    ];

    const navigation = isAdmin ? adminNavigation : employeeNavigation;

    return (
        <div className="min-h-screen bg-neutral-50">
            {/* Mobile sidebar backdrop */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 bg-neutral-900 bg-opacity-50 z-20 lg:hidden transition-opacity"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Sidebar */}
            <div className={`
        fixed inset-y-0 left-0 z-30 w-64 bg-white shadow-strong transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0
      `}>
                <div className="flex flex-col h-full">
                    {/* Logo */}
                    <div className="flex items-center justify-between h-16 px-6 border-b border-neutral-200 bg-gradient-to-r from-primary-600 to-primary-700">
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center shadow-md">
                                <span className="text-primary-600 font-bold text-sm">WP</span>
                            </div>
                            <span className="text-xl font-bold text-white">WorkProof</span>
                        </div>
                        <button
                            onClick={() => setSidebarOpen(false)}
                            className="lg:hidden text-white hover:text-neutral-200 transition"
                        >
                            <X className="w-6 h-6" />
                        </button>
                    </div>

                    {/* User info */}
                    <div className="px-6 py-5 border-b border-neutral-200 bg-neutral-50">
                        <div className="flex items-center gap-3">
                            <div className="w-12 h-12 bg-gradient-primary rounded-full flex items-center justify-center shadow-md">
                                <span className="text-white font-semibold text-base">
                                    {user?.full_name.charAt(0).toUpperCase()}
                                </span>
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-semibold text-neutral-900 truncate">
                                    {user?.full_name}
                                </p>
                                <p className="text-xs text-neutral-500 truncate">{user?.email}</p>
                            </div>
                        </div>
                        {user?.role === 'admin' && (
                            <div className="mt-3">
                                <span className="badge badge-primary">
                                    Admin
                                </span>
                            </div>
                        )}
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
                        {navigation.map((item) => {
                            const isActive = location.pathname === item.href;
                            return (
                                <Link
                                    key={item.name}
                                    to={item.href}
                                    className={`
                    flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 font-medium
                    ${isActive
                                            ? 'bg-primary-50 text-primary-700 shadow-sm'
                                            : 'text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900'
                                        }
                  `}
                                >
                                    <item.icon className={`w-5 h-5 ${isActive ? 'text-primary-600' : ''}`} />
                                    <span>{item.name}</span>
                                </Link>
                            );
                        })}
                    </nav>

                    {/* Logout */}
                    <div className="p-4 border-t border-neutral-200">
                        <button
                            onClick={handleLogout}
                            className="flex items-center gap-3 w-full px-4 py-3 text-neutral-700 hover:bg-danger-50 hover:text-danger-700 rounded-lg transition-all duration-200 font-medium"
                        >
                            <LogOut className="w-5 h-5" />
                            <span>Logout</span>
                        </button>
                    </div>
                </div>
            </div>

            {/* Main content */}
            <div className="lg:pl-64">
                {/* Top bar */}
                <div className="sticky top-0 z-10 bg-white border-b border-neutral-200 h-16 flex items-center px-4 lg:px-8 shadow-sm">
                    <button
                        onClick={() => setSidebarOpen(true)}
                        className="lg:hidden text-neutral-600 hover:text-neutral-900 mr-4 transition"
                    >
                        <Menu className="w-6 h-6" />
                    </button>
                    <h1 className="text-xl font-semibold text-neutral-900">
                        {navigation.find(item => item.href === location.pathname)?.name || 'Dashboard'}
                    </h1>
                </div>

                {/* Page content */}
                <main className="p-4 lg:p-8">
                    {children}
                </main>
            </div>
        </div>
    );
};

export default DashboardLayout;


