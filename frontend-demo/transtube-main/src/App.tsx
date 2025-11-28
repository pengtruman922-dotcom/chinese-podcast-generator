import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import TasksPage from './pages/TasksPage';
import SettingsPage from './pages/SettingsPage';
import TaskDetailPage from './pages/TaskDetailPage';

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <main className="container mx-auto px-4 py-6 max-w-7xl">
        <Routes>
          <Route path="/" element={<TasksPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/task/:taskId" element={<TaskDetailPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;