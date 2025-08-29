import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Clock, Eye, Target } from 'lucide-react';
import { Badge } from './ui/badge';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const NewsSection = () => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNews();
  }, []);

  const fetchNews = async () => {
    try {
      const response = await axios.get(`${API}/articles?category=news&limit=12`);
      setArticles(response.data);
    } catch (error) {
      console.error('Error fetching news:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800">
      {/* Header */}
      <section 
        className="relative py-24 bg-cover bg-center"
        style={{
          backgroundImage: `linear-gradient(135deg, rgba(17, 24, 39, 0.9), rgba(31, 41, 55, 0.8)), 
                           url('https://images.unsplash.com/photo-1623039405147-547794f92e9e')`
        }}
      >
        <div className="container">
          <div className="text-center">
            <h1 className="text-5xl font-bold text-white mb-4 uppercase tracking-wider">
              SHARP & PUNCHY NEWS
            </h1>
            <p className="text-xl text-slate-300 max-w-3xl mx-auto mb-6">
              Unfiltered journalism that cuts through the noise. We tell stories the way they need to be told — 
              with common sense first, not political spin.
            </p>
            <div className="flex flex-wrap justify-center gap-4 text-sm">
              <Badge className="bg-red-600/20 text-red-300 border border-red-600/30 px-4 py-2">
                <Target className="w-4 h-4 mr-2" />
                No Spin Zone
              </Badge>
              <Badge className="bg-red-600/20 text-red-300 border border-red-600/30 px-4 py-2">
                Straight Talk Only
              </Badge>
              <Badge className="bg-red-600/20 text-red-300 border border-red-600/30 px-4 py-2">
                Somerset to Nation
              </Badge>
            </div>
          </div>
        </div>
      </section>

      {/* Articles Grid */}
      <section className="py-16">
        <div className="container">
          {articles.length === 0 ? (
            <div className="text-center py-16">
              <h3 className="text-2xl font-semibold text-slate-300 mb-4">
                More Sharp News Coming Soon
              </h3>
              <p className="text-slate-400 max-w-2xl mx-auto mb-6">
                We're preparing hard-hitting stories that challenge the establishment and speak truth to power. 
                The kind of journalism that gives people a reason to care again.
              </p>
              <Link to="/contact" className="text-red-400 hover:text-red-300 underline">
                Got a story tip? Let us know →
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 stagger-children">
              {articles.map((article) => (
                <Link 
                  key={article.id} 
                  to={`/article/${article.id}`}
                  className="article-card group"
                >
                  {article.featured_image && (
                    <div className="overflow-hidden">
                      <img 
                        src={article.featured_image} 
                        alt={article.title}
                        className="article-image group-hover:scale-110 transition-transform duration-500"
                      />
                    </div>
                  )}
                  <div className="article-content">
                    <div className="flex items-center justify-between mb-3">
                      <Badge className="category-badge category-news">
                        STRAIGHT TALK
                      </Badge>
                      {article.is_breaking && (
                        <Badge variant="destructive" className="text-xs animate-pulse">
                          URGENT
                        </Badge>
                      )}
                    </div>
                    <h3 className="article-title group-hover:text-red-400 transition-colors">
                      {article.title}
                    </h3>
                    <p className="article-excerpt">
                      {article.content.substring(0, 150)}...
                    </p>
                    <div className="article-meta">
                      <span className="flex items-center">
                        <Clock className="w-3 h-3 mr-1" />
                        {formatDate(article.created_at)}
                      </span>
                      <span className="flex items-center">
                        <Eye className="w-3 h-3 mr-1" />
                        By {article.author_name}
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default NewsSection;