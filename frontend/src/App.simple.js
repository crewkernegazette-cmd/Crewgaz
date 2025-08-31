import React from 'react';
import './App.css';

function App() {
  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <nav className="bg-slate-800 border-b border-slate-700">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-red-500">The Crewkerne Gazette</h1>
        </div>
      </nav>
      
      <main className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold mb-4">Latest News</h2>
          <p className="text-slate-400">Your trusted source for local and national news</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Sample Article Cards */}
          <div className="bg-slate-800 rounded-lg p-6">
            <h3 className="text-xl font-bold mb-2">Welcome to Crewkerne Gazette</h3>
            <p className="text-slate-300 mb-4">We're getting the latest news ready for you.</p>
            <span className="text-sm text-slate-500">Just now</span>
          </div>
          
          <div className="bg-slate-800 rounded-lg p-6">
            <h3 className="text-xl font-bold mb-2">Site Maintenance Complete</h3>
            <p className="text-slate-300 mb-4">Our team has been working to improve your experience.</p>
            <span className="text-sm text-slate-500">Recently</span>
          </div>
          
          <div className="bg-slate-800 rounded-lg p-6">
            <h3 className="text-xl font-bold mb-2">More Stories Coming Soon</h3>
            <p className="text-slate-300 mb-4">Check back soon for the latest breaking news and updates.</p>
            <span className="text-sm text-slate-500">Today</span>
          </div>
        </div>
        
        <div className="text-center mt-12">
          <a 
            href="/login" 
            className="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg font-semibold"
          >
            Admin Login
          </a>
        </div>
      </main>
      
      <footer className="bg-slate-800 border-t border-slate-700 mt-16">
        <div className="container mx-auto px-4 py-8 text-center text-slate-400">
          <p>&copy; 2025 The Crewkerne Gazette. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

export default App;