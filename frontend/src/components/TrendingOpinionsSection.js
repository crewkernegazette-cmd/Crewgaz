import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ThumbsUp, ThumbsDown } from 'lucide-react';
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
      <div className="py-8 bg-slate-900/50">
        <div className="text-center text-slate-400">Loading opinions...</div>
      </div>
    );
  }

  return (
    <div className="py-8 mb-8 bg-gradient-to-r from-slate-800/50 via-slate-900/50 to-slate-800/50 rounded-xl border border-slate-700/50">
      {/* Section Header */}
      <div className="text-center mb-6">
        <h2 className="text-2xl md:text-3xl font-bold text-white mb-2">
          📮 TRENDING OPINIONS 📮
        </h2>
        <p className="text-slate-400 text-sm">
          Hot takes from our esteemed readers
        </p>
      </div>

      {/* Opinions Grid */}
      {opinions.length > 0 ? (
        <div className="grid grid-cols-3 md:grid-cols-6 gap-3 px-4 mb-6">
          {opinions.map((opinion) => (
            <Link
              key={opinion.id}
              to={`/opinion/${opinion.id}`}
              className="relative group overflow-hidden rounded-lg shadow-lg bg-slate-700 aspect-square"
            >
              <img
                src={opinion.image_url}
                alt="Reader Opinion"
                className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
                loading="lazy"
              />
              {/* Vote overlay */}
              <div className="absolute top-1 right-1 bg-black/60 px-2 py-0.5 rounded-full flex items-center gap-1">
                <span className={`text-xs font-medium ${opinion.net_votes >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {opinion.net_votes > 0 ? '+' : ''}{opinion.net_votes}
                </span>
              </div>
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              <div className="absolute bottom-0 left-0 right-0 p-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <div className="flex items-center justify-between text-white text-xs">
                  <span className="flex items-center gap-1">
                    <ThumbsUp className="w-3 h-3 text-green-400" />
                    {opinion.upvotes}
                  </span>
                  <span className="flex items-center gap-1">
                    <ThumbsDown className="w-3 h-3 text-red-400" />
                    {opinion.downvotes}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-6">
          <p className="text-slate-400">
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
            <button className="relative px-6 py-3 bg-gradient-to-r from-red-600 via-orange-500 to-yellow-500 rounded-lg font-bold text-lg text-white transform transition-all duration-300 hover:scale-105 hover:rotate-1 active:scale-95 shadow-2xl border-2 border-white/20">
              <span className="inline-block animate-bounce mr-2">👀</span>
              SEE ALL THE OUTRAGE
              <span className="inline-block animate-bounce ml-2">🔥</span>
            </button>
          </div>
          
          {/* Floating emojis */}
          <span className="absolute -top-3 -left-3 text-xl animate-bounce" style={{animationDelay: '0.1s'}}>💥</span>
          <span className="absolute -top-2 -right-5 text-xl animate-bounce" style={{animationDelay: '0.3s'}}>😱</span>
          <span className="absolute -bottom-3 -left-5 text-xl animate-bounce" style={{animationDelay: '0.5s'}}>🗣️</span>
          <span className="absolute -bottom-2 -right-3 text-xl animate-bounce" style={{animationDelay: '0.2s'}}>📢</span>
        </Link>
        
        {/* Sarcastic tagline */}
        <p className="mt-4 text-xs text-slate-500 italic">
          &quot;Because everyone&apos;s opinion is equally... interesting&quot; - The Editor
        </p>
      </div>
    </div>
  );
};

export default TrendingOpinionsSection;
