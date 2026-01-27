import React, { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
    children: ReactNode;
    adminOnly?: boolean;
    employeeOnly?: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, adminOnly = false, employeeOnly = false }) => {
    const { user, loading, isAdmin } = useAuth();
    const location = useLocation();

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    // Check consent for employees (except on consent page itself)
    if (user.role === 'employee' && location.pathname !== '/consent') {
        const consentAccepted = (user as any).consent_accepted;
        if (!consentAccepted) {
            return <Navigate to="/consent" replace />;
        }
    }

    // Admin-only routes
    if (adminOnly && !isAdmin) {
        return <Navigate to="/dashboard" replace />;
    }

    // Employee-only routes
    if (employeeOnly && isAdmin) {
        return <Navigate to="/dashboard" replace />;
    }

    return <>{children}</>;
};

export default ProtectedRoute;
