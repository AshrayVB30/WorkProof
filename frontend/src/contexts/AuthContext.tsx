import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authAPI } from '../lib/api';

interface User {
    id: string;
    email: string;
    full_name: string;
    role: 'admin' | 'employee';
    expected_daily_hours: number;
    department?: string;
    employee_id?: string;
    is_active: boolean;
    is_verified: boolean;
    created_at: string;
    last_login?: string;
    consent_accepted: boolean;
}

interface AuthContextType {
    user: User | null;
    loading: boolean;
    login: (email: string, password: string) => Promise<void>;
    logout: () => void;
    updateUser: (userData: any) => void;
    isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check if user is already logged in
        const storedUser = localStorage.getItem('user');
        const token = localStorage.getItem('access_token');

        if (storedUser && token) {
            setUser(JSON.parse(storedUser));
        }
        setLoading(false);
    }, []);

    const login = async (email: string, password: string) => {
        try {
            const response = await authAPI.login(email, password);
            const { access_token, refresh_token, user: userData } = response.data;

            localStorage.setItem('access_token', access_token);
            localStorage.setItem('refresh_token', refresh_token);
            localStorage.setItem('user', JSON.stringify(userData));

            setUser(userData);
        } catch (error: any) {
            throw new Error(error.response?.data?.detail || 'Login failed');
        }
    };

    const logout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        setUser(null);
    };

    const updateUser = (userData: any) => {
        if (!user) return;
        const newUser = { ...user, ...userData };
        localStorage.setItem('user', JSON.stringify(newUser));
        setUser(newUser);
    };

    const isAdmin = user?.role === 'admin';

    return (
        <AuthContext.Provider value={{ user, loading, login, logout, updateUser, isAdmin }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
