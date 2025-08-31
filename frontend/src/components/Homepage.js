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
      const response = await axios.get(`${API}/settings/public`);
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
      const newsResponse = await axios.get(`${API}/articles?category=news&limit=6`);
      const otherResponse = await axios.get(`${API}/articles?limit=6`);
      
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

      {/* Hero Section */}
      <div className="hero-section">
        <div className="hero-content">
          <div className="hero-text">
            <h1 className="hero-title">
              CREWKERNE
              <span className="hero-subtitle">GAZETTE</span>
            </h1>
            <p className="hero-description">
              The voice of Crewkerne and beyond. Real news, real stories, real impact.
            </p>
            <Button className="cta-button">
              Subscribe Now
            </Button>
          </div>
        </div>
      </div>

      {/* Latest News & Features Section */}
      <div className="content-section">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">LATEST NEWS & FEATURES</h2>
            <p className="section-subtitle">
              Leading with hard-hitting news, plus the culture and stories that matter.
              British life as it's lived — with all its grit, humor, and contradictions.
            </p>
          </div>

          <div className="articles-grid">
            {Array.isArray(articles) && articles.length > 0 ? (
              articles.map((article) => (
                <Link key={article.id} to={`/article/${article.slug || article.id}`} className="article-card group">
                  {article.featured_image && (
                    <div className="article-image">
                      <img src={article.featured_image} alt={article.title} />
                    </div>
                  )}
                  <div className="article-content">
                    <div className="flex items-center justify-between mb-4">
                      <Badge className={`category-badge ${getCategoryBadgeClass(article.category)}`}>
                        {article.category.toUpperCase()}
                      </Badge>
                      {article.is_breaking && (
                        <div className="breaking-alert">
                          URGENT
                        </div>
                      )}
                    </div>
                    
                    {/* Category Labels */}
                    {renderCategoryLabels(article.category_labels)}
                    
                    <h3 className="article-title">{article.title}</h3>
                    <p className="article-excerpt">
                      {article.content.substring(0, 140)}...
                    </p>
                    <div className="article-meta">
                      <span className="flex items-center">
                        <Clock className="w-3 h-3 mr-1" />
                        {formatDate(article.created_at)}
                      </span>
                      <span className="font-bold">{article.author_name}</span>
                    </div>
                  </div>
                </Link>
              ))
            ) : (
              <div className="col-span-full text-center py-8">
                <p className="text-slate-400">No articles available at the moment.</p>
              </div>
            )}
          </div>
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