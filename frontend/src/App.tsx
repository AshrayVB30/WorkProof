import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import DashboardLayout from './components/DashboardLayout';
import Login from './pages/Login';
import Consent from './pages/Consent';
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import Timeline from './pages/Timeline';
import DailySummary from './pages/DailySummary';
import EmployeeList from './pages/EmployeeList';
import EmployeeDetails from './pages/EmployeeDetails';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import AddUser from './pages/AddUser';
import './index.css';

function App() {
    return (
        <AuthProvider>
            <BrowserRouter>
                <Routes>
                    <Route path="/login" element={<Login />} />

                    {/* Employee Consent (First Login) */}
                    <Route
                        path="/consent"
                        element={
                            <ProtectedRoute employeeOnly>
                                <Consent />
                            </ProtectedRoute>
                        }
                    />

                    {/* Employee Routes */}
                    <Route
                        path="/dashboard"
                        element={
                            <ProtectedRoute>
                                <DashboardLayout>
                                    <Dashboard />
                                </DashboardLayout>
                            </ProtectedRoute>
                        }
                    />

                    <Route
                        path="/timeline"
                        element={
                            <ProtectedRoute employeeOnly>
                                <DashboardLayout>
                                    <Timeline />
                                </DashboardLayout>
                            </ProtectedRoute>
                        }
                    />

                    <Route
                        path="/daily-summary"
                        element={
                            <ProtectedRoute employeeOnly>
                                <DashboardLayout>
                                    <DailySummary />
                                </DashboardLayout>
                            </ProtectedRoute>
                        }
                    />

                    {/* Admin Routes */}
                    <Route
                        path="/employees"
                        element={
                            <ProtectedRoute adminOnly>
                                <DashboardLayout>
                                    <EmployeeList />
                                </DashboardLayout>
                            </ProtectedRoute>
                        }
                    />

                    <Route
                        path="/admin/add-employee"
                        element={
                            <ProtectedRoute adminOnly>
                                <DashboardLayout>
                                    <AddUser />
                                </DashboardLayout>
                            </ProtectedRoute>
                        }
                    />

                    <Route
                        path="/admin/add-admin"
                        element={
                            <ProtectedRoute adminOnly>
                                <DashboardLayout>
                                    <AddUser />
                                </DashboardLayout>
                            </ProtectedRoute>
                        }
                    />

                    <Route
                        path="/employees/:id"
                        element={
                            <ProtectedRoute adminOnly>
                                <DashboardLayout>
                                    <EmployeeDetails />
                                </DashboardLayout>
                            </ProtectedRoute>
                        }
                    />

                    <Route
                        path="/reports"
                        element={
                            <ProtectedRoute>
                                <DashboardLayout>
                                    <Reports />
                                </DashboardLayout>
                            </ProtectedRoute>
                        }
                    />

                    {/* Settings (Both Roles) */}
                    <Route
                        path="/settings"
                        element={
                            <ProtectedRoute>
                                <DashboardLayout>
                                    <Settings />
                                </DashboardLayout>
                            </ProtectedRoute>
                        }
                    />

                    <Route path="/" element={<Landing />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </BrowserRouter>
        </AuthProvider>
    );
}

export default App;
