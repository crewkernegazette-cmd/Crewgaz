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

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
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
      setShowBanner(response.data.show_breaking_news_banner);
    } catch (error) {
      console.error('Error fetching public settings:', error);
      // Default to showing banner if error
      setShowBanner(true);
    }
  };

  const fetchArticles = async () => {
    try {
      console.warn('Fetching articles...');
      // Fetch news articles first (prioritized)
      const newsResponse = await axios.get(`${API}/api/articles?category=news&limit=6`);
      const otherResponse = await axios.get(`${API}/api/articles?limit=6`);
      
      // Ensure we always have arrays, never null
      const newsArticles = Array.isArray(newsResponse.data) ? newsResponse.data : [];
      const otherArticles = Array.isArray(otherResponse.data) ? otherResponse.data : [];
      
      // Combine news articles first, then other articles, avoiding duplicates
      const filteredOtherArticles = otherArticles.filter(
        article => !newsArticles.some(newsArticle => newsArticle.id === article.id)
      );
      
      // Prioritize news articles at the top
      const combinedArticles = [...newsArticles, ...filteredOtherArticles].slice(0, 6);
      setArticles(combinedArticles);
      console.warn('Articles state after fetch:', combinedArticles);
    } catch (error) {
      console.error('Error fetching articles:', error);
      setArticles([]); // Ensure it's always an array
      console.warn('Articles state set to empty array due to error');
    }
  };

  const fetchBreakingNews = async () => {
    try {
      const response = await axios.get(`${API}/articles?is_breaking=true&limit=3`);
      const breakingData = Array.isArray(response.data) ? response.data : [];
      setBreakingNews(breakingData);
      console.warn('Breaking news state:', breakingData);
    } catch (error) {
      console.error('Error fetching breaking news:', error);
      setBreakingNews([]); // Ensure it's always an array
      console.warn('Breaking news state set to empty array due to error');
    } finally {
      setLoading(false);
    }
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
    return <div className="loading-spinner">Loading...</div>;
  }

  return (
    <div>
      {/* Breaking News Ticker */}
      {Array.isArray(breakingNews) && breakingNews.length > 0 && showBanner && (
        <div className="breaking-news-ticker">
          <div className="breaking-badge">
            BREAKING
          </div>
          <div className="ticker-content">
            {breakingNews.map((news, index) => (
              <Link key={news.id} to={`/article/${news.slug || news.id}`} className="ticker-link">
                {news.title}
                {index < breakingNews.length - 1 && ' • '}
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Clean Articles Section - GB News Style */}
      <div className="py-8 bg-slate-900">
        <div className="container mx-auto px-4">
          {Array.isArray(articles) && articles.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {articles.map((article) => (
                <Link 
                  key={article.id} 
                  to={`/article/${article.slug || article.id}`} 
                  className="group bg-slate-800 rounded-lg overflow-hidden hover:bg-slate-700 transition-colors"
                >
                  {article.featured_image && (
                    <div className="aspect-video overflow-hidden">
                      <img 
                        src={article.featured_image} 
                        alt={article.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                    </div>
                  )}
                  <div className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <Badge className="bg-red-600 text-white text-xs px-2 py-1">
                        {article.category.toUpperCase()}
                      </Badge>
                      {article.is_breaking && (
                        <Badge className="bg-red-700 text-white text-xs px-2 py-1 animate-pulse">
                          BREAKING
                        </Badge>
                      )}
                    </div>
                    
                    {/* Category Labels */}
                    {renderCategoryLabels(article.category_labels)}
                    
                    <h3 className="text-white font-bold text-lg mb-2 group-hover:text-red-400 transition-colors line-clamp-2">
                      {article.title}
                    </h3>
                    
                    {article.subheading && (
                      <p className="text-slate-300 text-sm mb-2">
                        {article.subheading}
                      </p>
                    )}
                    
                    <p className="text-slate-400 text-sm mb-3 line-clamp-2">
                      {article.content.substring(0, 120)}...
                    </p>
                    
                    <div className="flex items-center justify-between text-xs text-slate-500">
                      <span className="flex items-center">
                        <Clock className="w-3 h-3 mr-1" />
                        {formatDate(article.created_at)}
                      </span>
                      <span>{article.author_name}</span>
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