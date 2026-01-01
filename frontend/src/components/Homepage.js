import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Clock, Eye } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import TopRail from './TopRail';
import NewsSection from './NewsSection';
import MusicSection from './MusicSection';
import DocumentariesSection from './DocumentariesSection';
import ComedySection from './ComedySection';
import ContactSection from './ContactSection';
import TrendingOpinionsSection from './TrendingOpinionsSection';
import { apiClient } from '../config/api';

const Homepage = () => {
  const [breakingNews, setBreakingNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showBanner, setShowBanner] = useState(true);

  useEffect(() => {
    fetchBreakingNews();
    fetchPublicSettings();
  }, []);

  const fetchPublicSettings = async () => {
    try {
      const response = await apiClient.get('/settings/public');
      setShowBanner(response.data?.show_breaking_news_banner || true);
    } catch (error) {
      console.error('Error fetching public settings:', error);
      // Default to showing banner if error
      setShowBanner(true);
    }
  };

  const fetchBreakingNews = async () => {
    try {
      const response = await apiClient.get('/articles?is_breaking=true&limit=3');
      const breakingData = Array.isArray(response.data) ? response.data : [];
      setBreakingNews(breakingData);
      console.warn('Breaking news state:', breakingData);
    } catch (error) {
      console.error('Error fetching breaking news:', error);
      setBreakingNews([]); // Ensure it's always an array
      console.warn('Breaking news state set to empty array due to error');
    }
    setLoading(false); // Always set loading to false
  };

  // Debug logging in render
  console.warn('Homepage render - Breaking news state:', breakingNews, 'Type:', typeof breakingNews, 'IsArray:', Array.isArray(breakingNews));

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div>
      {/* Breaking News Ticker */}
      {Array.isArray(breakingNews) && breakingNews.length > 0 && showBanner && (
        <div className="bg-red-600 text-white py-2">
          <div className="container mx-auto px-4 flex items-center">
            <span className="bg-red-800 px-3 py-1 text-sm font-bold mr-4">BREAKING</span>
            <div className="flex-1 overflow-hidden">
              <div className="whitespace-nowrap animate-scroll">
                {breakingNews.map((news, index) => (
                  <Link key={news.id || index} to={`/article/${news.slug}`} className="hover:underline mr-8">
                    {news.title}
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* GB News Style Top Rail */}
      <TopRail />

      {/* News Section */}
      <NewsSection />

      {/* Dover Dash Game Section */}
      <section className="py-16 bg-gradient-to-r from-red-900 via-blue-900 to-red-900 relative overflow-hidden">
        <div className="absolute inset-0 bg-black/20"></div>
        <div className="container relative z-10">
          <div className="text-center">
            <h2 className="text-4xl font-bold text-white mb-4 tracking-wider" style={{fontFamily: '"Press Start 2P", monospace', textShadow: '3px 3px 0px #000000'}}>
              🎮 RETRO ARCADE 🎮
            </h2>
            <p className="text-lg text-white/90 mb-8 max-w-2xl mx-auto">
              Take control as Prime Minister in our exclusive 8-bit political satire game!
              Defend Dover from incoming boats using British bureaucracy and border patrol bathtubs.
            </p>
            <div className="flex justify-center">
              <a 
                href="/dover-dash" 
                className="inline-block bg-red-600 hover:bg-white text-white hover:text-red-600 font-bold py-4 px-8 border-4 border-white hover:border-red-600 transition-all duration-300 transform hover:scale-105 hover:shadow-2xl"
                style={{
                  fontFamily: '"Press Start 2P", monospace',
                  fontSize: '14px',
                  textDecoration: 'none',
                  boxShadow: '8px 8px 0px #000000',
                  imageRendering: 'pixelated'
                }}
              >
                ⚡ PLAY DOVER DASH ⚡
              </a>
            </div>
            <div className="mt-6 text-sm text-white/70" style={{fontFamily: '"Press Start 2P", monospace'}}>
              🏆 Beat the leaderboard and become PM of the week! 🏆
            </div>
          </div>
        </div>
        
        {/* Animated background elements */}
        <div className="absolute top-10 left-10 animate-bounce text-white/30" style={{fontSize: '24px'}}>🚤</div>
        <div className="absolute top-20 right-20 animate-pulse text-white/30" style={{fontSize: '24px'}}>🇬🇧</div>
        <div className="absolute bottom-10 left-1/4 animate-bounce text-white/30" style={{fontSize: '24px', animationDelay: '1s'}}>🛥️</div>
        <div className="absolute bottom-20 right-1/3 animate-pulse text-white/30" style={{fontSize: '24px', animationDelay: '2s'}}>👑</div>
      </section>

      {/* Music Section */}
      <MusicSection />

      {/* Documentaries Section */}
      <DocumentariesSection />

      {/* Comedy Section */}
      <ComedySection />

      {/* Contact Section */}
      <ContactSection />
    </div>
  );
};

export default Homepage;