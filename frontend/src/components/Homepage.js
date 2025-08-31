import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Clock, Eye } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import NewsSection from './NewsSection';
import MusicSection from './MusicSection';
import DocumentariesSection from './DocumentariesSection';
import ComedySection from './ComedySection';
import ContactSection from './ContactSection';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://crewkernegazette.co.uk';
const API = BACKEND_URL;

const Homepage = () => {
  const [articles, setArticles] = useState([]);
  const [breakingNews, setBreakingNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showBanner, setShowBanner] = useState(true);

  useEffect(() => {
    fetchArticles();
    fetchBreakingNews();
    fetchPublicSettings();
  }, []);

  const fetchPublicSettings = async () => {
    try {
      const response = await axios.get(`${API}/api/settings/public`);
      setShowBanner(response.data?.show_breaking_news_banner || true);
    } catch (error) {
      console.error('Error fetching public settings:', error);
      // Default to showing banner if error
      setShowBanner(true);
    }
  };

  const fetchArticles = async () => {
    try {
      console.warn('Fetching articles...');
      // Simple article fetch to avoid crashes
      const response = await axios.get(`${API}/api/articles?limit=8`);
      
      // Ensure we always have arrays, never null
      const articlesData = Array.isArray(response.data) ? response.data : [];
      setArticles(articlesData);
      console.warn('Articles state after fetch:', articlesData);
    } catch (error) {
      console.error('Error fetching articles:', error);
      setArticles([]); // Ensure it's always an array
      console.warn('Articles state set to empty array due to error');
    }
  };

  const fetchBreakingNews = async () => {
    try {
      const response = await axios.get(`${API}/api/articles?is_breaking=true&limit=3`);
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

  const getCategoryBadgeClass = (category) => {
    switch (category) {
      case 'news': return 'category-news';
      case 'music': return 'category-music';
      case 'documentaries': return 'category-documentaries';
      case 'comedy': return 'category-comedy';
      default: return 'category-news';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const renderCategoryLabels = (labels) => {
    if (!Array.isArray(labels) || labels.length === 0) return null;
    
    return (
      <div className="flex flex-wrap gap-1 mb-2">
        {labels.slice(0, 2).map((label, index) => (
          <Badge 
            key={index} 
            className="bg-red-600/20 text-red-300 border border-red-600/30 text-xs px-2 py-1"
          >
            {label}
          </Badge>
        ))}
        {labels.length > 2 && (
          <Badge className="bg-slate-600/20 text-slate-300 border border-slate-600/30 text-xs px-2 py-1">
            +{labels.length - 2}
          </Badge>
        )}
      </div>
    );
  };

  // Debug logging in render
  console.warn('Homepage render - Articles state:', articles, 'Type:', typeof articles, 'IsArray:', Array.isArray(articles));
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
                  <Link key={news.id || index} to={`/article/${news.slug || news.id}`} className="hover:underline mr-8">
                    {news.title}
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Clean Articles Section - GB News Style */}
      <div className="py-8 bg-slate-900 min-h-screen">
        <div className="container mx-auto px-4">
          {Array.isArray(articles) && articles.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {articles.map((article, index) => (
                <Link 
                  key={article.id || index} 
                  to={`/article/${article.slug || article.id}`} 
                  className="group bg-slate-800 rounded-lg overflow-hidden hover:bg-slate-700 transition-colors"
                >
                  {article.featured_image && (
                    <div className="aspect-video overflow-hidden">
                      <img 
                        src={article.featured_image} 
                        alt={article.title || 'Article'}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        onError={(e) => {e.target.style.display = 'none'}}
                      />
                    </div>
                  )}
                  <div className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <Badge className="bg-red-600 text-white text-xs px-2 py-1">
                        {(article.category || 'news').toUpperCase()}
                      </Badge>
                      {article.is_breaking && (
                        <Badge className="bg-red-700 text-white text-xs px-2 py-1 animate-pulse">
                          BREAKING
                        </Badge>
                      )}
                    </div>
                    
                    {/* Category Labels */}
                    {renderCategoryLabels(article.category_labels)}
                    
                    <h3 className="text-white font-bold text-lg mb-2 group-hover:text-red-400 transition-colors">
                      {article.title || 'Untitled Article'}
                    </h3>
                    
                    {article.subheading && (
                      <p className="text-slate-300 text-sm mb-2">
                        {article.subheading}
                      </p>
                    )}
                    
                    <p className="text-slate-400 text-sm mb-3">
                      {article.content ? `${article.content.substring(0, 120)}...` : 'Read more...'}
                    </p>
                    
                    <div className="flex items-center justify-between text-xs text-slate-500">
                      <span className="flex items-center">
                        <Clock className="w-3 h-3 mr-1" />
                        {article.created_at ? formatDate(article.created_at) : 'Recently'}
                      </span>
                      <span>{article.author_name || 'Admin'}</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <h2 className="text-white text-2xl font-bold mb-4">Latest News Coming Soon</h2>
              <p className="text-slate-400">We're preparing the latest stories for you.</p>
            </div>
          )}
        </div>
      </div>

      {/* News Section */}
      <NewsSection />

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