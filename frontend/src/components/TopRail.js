import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Clock, Eye, Pin } from 'lucide-react';
import { Badge } from './ui/badge';
import { apiClient } from '../config/api';

const TopRail = () => {
  const [topRailData, setTopRailData] = useState({
    lead: null,
    secondary: [],
    more: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchTopRailData();
  }, []);

  const fetchTopRailData = async () => {
    try {
      const response = await apiClient.get('/api/top-rail');
      
      setTopRailData({
        lead: response.data.lead || null,
        secondary: Array.isArray(response.data.secondary) ? response.data.secondary : [],
        more: Array.isArray(response.data.more) ? response.data.more : []
      });
      setError(null);
    } catch (error) {
      console.error('Error fetching top rail data:', error);
      setError('Failed to load articles');
      // Set empty arrays to prevent crashes
      setTopRailData({
        lead: null,
        secondary: [],
        more: []
      });
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Recently';
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

  const getPlaceholderImage = () => {
    return "data:image/svg+xml;base64," + btoa(`
      <svg width="800" height="400" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#1e293b"/>
        <text x="50%" y="50%" font-family="Arial, sans-serif" font-size="24" fill="#64748b" text-anchor="middle" dy=".3em">
          The Crewkerne Gazette
        </text>
      </svg>
    `);
  };

  if (loading) {
    return (
      <div className="py-8 bg-slate-900">
        <div className="container mx-auto px-4">
          <div className="text-center text-white">Loading latest news...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-8 bg-slate-900">
        <div className="container mx-auto px-4">
          <div className="text-center text-red-400">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="py-8 bg-slate-900">
      <div className="container mx-auto px-4">
        {/* Top Rail Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          
          {/* Lead Story - Takes 2/3 width on large screens */}
          <div className="lg:col-span-2">
            {topRailData.lead ? (
              <Link 
                to={`/article/${topRailData.lead.slug}`} 
                className="group block bg-slate-800 rounded-lg overflow-hidden hover:bg-slate-700 transition-colors"
              >
                <div className="aspect-video overflow-hidden">
                  <img 
                    src={topRailData.lead.featured_image || getPlaceholderImage()} 
                    alt={topRailData.lead.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    onError={(e) => {e.target.src = getPlaceholderImage()}}
                  />
                </div>
                <div className="p-6">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <Badge className="bg-red-600 text-white text-sm px-3 py-1">
                        {(topRailData.lead.category || 'news').toUpperCase()}
                      </Badge>
                      {topRailData.lead.is_breaking && (
                        <Badge className="bg-red-700 text-white text-sm px-3 py-1 animate-pulse">
                          BREAKING
                        </Badge>
                      )}
                      {topRailData.lead.pinned_at && (
                        <Badge className="bg-yellow-600 text-white text-sm px-3 py-1">
                          <Pin className="w-3 h-3 mr-1" />
                          PINNED
                        </Badge>
                      )}
                    </div>
                  </div>
                  
                  {/* Category Labels */}
                  {renderCategoryLabels(topRailData.lead.category_labels)}
                  
                  <h1 className="text-white font-bold text-2xl md:text-3xl mb-3 group-hover:text-red-400 transition-colors leading-tight">
                    {topRailData.lead.title}
                  </h1>
                  
                  {topRailData.lead.subheading && (
                    <p className="text-slate-300 text-lg mb-4 leading-relaxed">
                      {topRailData.lead.subheading}
                    </p>
                  )}
                  
                  <p className="text-slate-400 mb-4 leading-relaxed">
                    {topRailData.lead.content ? `${topRailData.lead.content.substring(0, 200)}...` : 'Read more...'}
                  </p>
                  
                  <div className="flex items-center justify-between text-sm text-slate-500">
                    <span className="flex items-center">
                      <Clock className="w-4 h-4 mr-2" />
                      {formatDate(topRailData.lead.created_at)}
                    </span>
                    <span>{topRailData.lead.author_name || 'The Crewkerne Gazette'}</span>
                  </div>
                </div>
              </Link>
            ) : (
              <div className="bg-slate-800 rounded-lg p-8 text-center">
                <h2 className="text-white text-xl mb-2">Latest News Coming Soon</h2>
                <p className="text-slate-400">We're preparing the latest stories for you.</p>
              </div>
            )}
          </div>

          {/* Secondary Stories - Takes 1/3 width on large screens */}
          <div className="space-y-6">
            <h2 className="text-white text-xl font-bold border-b border-red-600 pb-2">More Headlines</h2>
            {topRailData.secondary.length > 0 ? (
              topRailData.secondary.map((article, index) => (
                <Link 
                  key={article.id || index} 
                  to={`/article/${article.slug}`} 
                  className="group block bg-slate-800 rounded-lg overflow-hidden hover:bg-slate-700 transition-colors"
                >
                  <div className="flex">
                    <div className="w-24 h-24 flex-shrink-0 overflow-hidden">
                      <img 
                        src={article.featured_image || getPlaceholderImage()} 
                        alt={article.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        onError={(e) => {e.target.src = getPlaceholderImage()}}
                      />
                    </div>
                    <div className="flex-1 p-4">
                      <div className="flex items-center space-x-2 mb-2">
                        <Badge className="bg-red-600 text-white text-xs px-2 py-1">
                          {(article.category || 'news').toUpperCase()}
                        </Badge>
                        {article.is_breaking && (
                          <Badge className="bg-red-700 text-white text-xs px-2 py-1 animate-pulse">
                            BREAKING
                          </Badge>
                        )}
                        {article.pinned_at && (
                          <Pin className="w-3 h-3 text-yellow-500" />
                        )}
                      </div>
                      
                      {/* Category Labels */}
                      {renderCategoryLabels(article.category_labels)}
                      
                      <h3 className="text-white font-semibold text-sm mb-2 group-hover:text-red-400 transition-colors leading-tight">
                        {article.title}
                      </h3>
                      
                      <div className="text-xs text-slate-500">
                        <Clock className="w-3 h-3 inline mr-1" />
                        {formatDate(article.created_at)}
                      </div>
                    </div>
                  </div>
                </Link>
              ))
            ) : (
              <div className="text-center py-4">
                <p className="text-slate-400 text-sm">More stories coming soon</p>
              </div>
            )}
          </div>
        </div>

        {/* More Stories Grid */}
        {topRailData.more.length > 0 && (
          <div>
            <h2 className="text-white text-xl font-bold border-b border-red-600 pb-2 mb-6">Latest Stories</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {topRailData.more.map((article, index) => (
                <Link 
                  key={article.id || index} 
                  to={`/article/${article.slug}`} 
                  className="group bg-slate-800 rounded-lg overflow-hidden hover:bg-slate-700 transition-colors"
                >
                  <div className="aspect-video overflow-hidden">
                    <img 
                      src={article.featured_image || getPlaceholderImage()} 
                      alt={article.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      onError={(e) => {e.target.src = getPlaceholderImage()}}
                    />
                  </div>
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
                      {article.pinned_at && (
                        <Pin className="w-3 h-3 text-yellow-500" />
                      )}
                    </div>
                    
                    {/* Category Labels */}
                    {renderCategoryLabels(article.category_labels)}
                    
                    <h3 className="text-white font-bold text-sm mb-2 group-hover:text-red-400 transition-colors leading-tight">
                      {article.title}
                    </h3>
                    
                    {article.subheading && (
                      <p className="text-slate-300 text-xs mb-2 leading-relaxed">
                        {article.subheading}
                      </p>
                    )}
                    
                    <p className="text-slate-400 text-xs mb-3 leading-relaxed">
                      {article.content ? `${article.content.substring(0, 80)}...` : 'Read more...'}
                    </p>
                    
                    <div className="flex items-center justify-between text-xs text-slate-500">
                      <span className="flex items-center">
                        <Clock className="w-3 h-3 mr-1" />
                        {formatDate(article.created_at)}
                      </span>
                      <span>{article.author_name || 'Admin'}</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TopRail;