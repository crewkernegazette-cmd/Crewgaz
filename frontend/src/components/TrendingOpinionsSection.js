import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiClient } from '../config/api';

const TrendingOpinionsSection = () => {
  const [opinions, setOpinions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLatestOpinions();
  }, []);

  const fetchLatestOpinions = async () => {
    try {
      const response = await apiClient.get('/opinions/latest?limit=6');
      setOpinions(response.data.opinions || []);
    } catch (error) {
      console.error('Error fetching trending opinions:', error);
      setOpinions([]);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <section className="py-12 bg-gradient-to-b from-slate-800 to-slate-900">
        <div className="container mx-auto px-4">
          <div className="text-center text-white">Loading opinions...</div>
        </div>
      </section>
    );
  }

  return (
    <section className="py-12 bg-gradient-to-b from-slate-800 to-slate-900">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center mb-8">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-2">
            📮 TRENDING OPINIONS 📮
          </h2>
          <p className="text-slate-400 text-lg">
            Hot takes from our esteemed readers. Viewer discretion advised.
          </p>
        </div>

        {/* Opinions Grid */}
        {opinions.length > 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
            {opinions.map((opinion) => (
              <div
                key={opinion.id}
                className="relative group overflow-hidden rounded-lg shadow-lg bg-slate-700 aspect-square"
              >
                <img
                  src={opinion.image_url}
                  alt="Reader Opinion"
                  className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
                  loading="lazy"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <div className="absolute bottom-0 left-0 right-0 p-2 text-white text-xs opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  {opinion.created_at && new Date(opinion.created_at).toLocaleDateString('en-GB', {
                    day: 'numeric',
                    month: 'short'
                  })}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-slate-400 text-lg">
              No opinions yet! Check back soon for spicy hot takes. 🌶️
            </p>
          </div>
        )}

        {/* Slapstick Humor Button */}
        <div className="text-center">
          <Link
            to="/trending-opinions"
            className="inline-block relative group"
          >
            {/* Button with wild styling */}
            <div className="relative">
              {/* Background glow effect */}
              <div className="absolute -inset-1 bg-gradient-to-r from-pink-600 via-red-600 to-yellow-500 rounded-lg blur opacity-75 group-hover:opacity-100 transition duration-300 animate-pulse"></div>
              
              {/* Main button */}
              <button className="relative px-8 py-4 bg-gradient-to-r from-red-600 via-orange-500 to-yellow-500 rounded-lg font-bold text-xl text-white transform transition-all duration-300 hover:scale-105 hover:rotate-1 active:scale-95 shadow-2xl border-4 border-white/20">
                <span className="inline-block animate-bounce mr-2">👀</span>
                SEE ALL THE OUTRAGE
                <span className="inline-block animate-bounce ml-2">🔥</span>
              </button>
            </div>
            
            {/* Floating emojis */}
            <span className="absolute -top-4 -left-4 text-2xl animate-bounce" style={{animationDelay: '0.1s'}}>💥</span>
            <span className="absolute -top-2 -right-6 text-2xl animate-bounce" style={{animationDelay: '0.3s'}}>😱</span>
            <span className="absolute -bottom-4 -left-6 text-2xl animate-bounce" style={{animationDelay: '0.5s'}}>🗣️</span>
            <span className="absolute -bottom-2 -right-4 text-2xl animate-bounce" style={{animationDelay: '0.2s'}}>📢</span>
          </Link>
          
          {/* Sarcastic tagline */}
          <p className="mt-6 text-sm text-slate-500 italic">
            &quot;Because everyone&apos;s opinion is equally... interesting&quot; - The Editor
          </p>
        </div>
      </div>
    </section>
  );
};

export default TrendingOpinionsSection;
