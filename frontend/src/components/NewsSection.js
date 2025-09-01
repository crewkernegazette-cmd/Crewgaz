import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Clock, Eye, Target } from 'lucide-react';
import { Badge } from './ui/badge';

import { apiClient } from '../config/api';

const NewsSection = () => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNews();
  }, []);

  const fetchNews = async () => {
    try {
      const response = await apiClient.get('/articles?category=news&limit=12');
      const articlesData = Array.isArray(response.data) ? response.data : [];
      setArticles(articlesData);
      console.warn('NewsSection - Articles state after fetch:', articlesData);
    } catch (error) {
      console.error('Error fetching news:', error);
      setArticles([]); // Ensure it's always an array
      console.warn('NewsSection - Articles state set to empty array due to error');
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

  // Debug logging in render
  console.warn('NewsSection render - Articles state:', articles, 'Type:', typeof articles, 'IsArray:', Array.isArray(articles));

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800">
      {/* Video Section - Replaces Sharp & Punchy Header */}
      <section className="relative py-16 bg-slate-900">
        <div className="container">
          <div className="max-w-5xl mx-auto">
            {/* Video Container with Border */}
            <div className="bg-slate-800 p-6 rounded-xl border-2 border-red-600/30 shadow-2xl">
              <div className="text-center mb-6">
                <h1 className="text-4xl font-bold text-white mb-4">
                  News, But not as you know it
                </h1>
              </div>
              <div className="relative aspect-video rounded-lg overflow-hidden border border-slate-600/50">
                <iframe
                  src="https://www.youtube.com/embed/jiZkkqK2410"
                  title="News, But not as you know it"
                  className="w-full h-full"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* YouTube Video Section */}
      <section className="py-12 bg-slate-800/50">
        <div className="container">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-white mb-4">
              News, But not as you know it
            </h2>
          </div>
          <div className="max-w-4xl mx-auto">
            <div className="relative aspect-video rounded-lg overflow-hidden shadow-2xl">
              <iframe
                src="https://www.youtube.com/embed/jiZkkqK2410"
                title="News, But not as you know it"
                className="w-full h-full"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
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
                  key={article.slug} 
                  to={`/article/${article.slug}`}
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
                    
                    {/* Category Labels */}
                    {article.category_labels && article.category_labels.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-3">
                        {article.category_labels.slice(0, 2).map((label, index) => (
                          <Badge 
                            key={index} 
                            className="bg-red-600/20 text-red-300 border border-red-600/30 text-xs px-2 py-1"
                          >
                            {label}
                          </Badge>
                        ))}
                        {article.category_labels.length > 2 && (
                          <Badge className="bg-slate-600/20 text-slate-300 border border-slate-600/30 text-xs px-2 py-1">
                            +{article.category_labels.length - 2}
                          </Badge>
                        )}
                      </div>
                    )}
                    
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