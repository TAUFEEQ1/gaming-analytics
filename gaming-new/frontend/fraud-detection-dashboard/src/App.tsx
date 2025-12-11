import React from 'react';
import './App.css';
import Dashboard from './components/Dashboard';
import { FraudProvider } from './context/FraudContext';

function App() {
  return (
    <FraudProvider>
      <div className="min-h-screen bg-gray-50">
        <header className="bg-blue-900 text-white p-4 shadow-lg">
          <div className="container mx-auto">
            <h1 className="text-3xl font-bold">Gaming Analytics</h1>
            <p className="text-blue-200 mt-1">Comprehensive Gaming Data Dashboard</p>
          </div>
        </header>
        <main className="container mx-auto p-4">
          <Dashboard />
        </main>
      </div>
    </FraudProvider>
  );
}

export default App;
