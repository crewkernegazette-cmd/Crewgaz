import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Clock, Smile, Zap } from 'lucide-react';
import { Badge } from './ui/badge';
import { Button } from './ui/button';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ComedySection = () => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchComedy();
  }, []);

  const fetchComedy = async () => {
    try {
      const response = await axios.get(`${API}/articles?category=comedy&limit=12`);
      setArticles(response.data);
    } catch (error) {
      console.error('Error fetching comedy:', error);
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
          backgroundImage: `linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.8)), 
                           url('https://images.unsplash.com/photo-1527224857830-43a7acc85260')`
        }}
      >
        <div className="container">
          <div className="text-center">
            <h1 className="text-5xl font-bold text-white mb-4">
              Comedy
            </h1>
            <p className="text-xl text-slate-300 max-w-2xl mx-auto">
              Satirical takes, comedic sketches, and the humor that cuts through 
              the noise to reveal uncomfortable truths.
            </p>
          </div>
        </div>
      </section>

      {/* Comedy Grid */}
      <section className="py-16">
        <div className="container">
          {articles.length === 0 ? (
            <div className="text-center py-16">
              <Smile className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <h3 className="text-2xl font-semibold text-slate-300 mb-4">
                No Comedy Content Yet
              </h3>
              <p className="text-slate-400">
                Get ready for satirical content and comedic takes on current events.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 stagger-children">
              {articles.map((article) => (
                <div key={article.id} className="article-card group hover:rotate-1 transition-transform">
                  {article.featured_image && (
                    <div className="relative overflow-hidden">
                      <img 
                        src={article.featured_image} 
                        alt={article.title}
                        className="article-image group-hover:scale-110 transition-transform duration-500"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-orange-900/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                        <div className="absolute bottom-4 left-4">
                          <Zap className="w-6 h-6 text-orange-400 animate-bounce" />
                        </div>
                      </div>
                    </div>
                  )}
                  <div className="article-content">
                    <div className="flex items-center justify-between mb-3">
                      <Badge className="category-badge category-comedy">
                        Comedy
                      </Badge>
                    </div>
                    <h3 className="article-title group-hover:text-orange-400 transition-colors">
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
                      <span>By {article.author_name}</span>
                    </div>
                    <div className="mt-4">
                      <Link to={`/article/${article.id}`}>
                        <Button variant="outline" size="sm" className="w-full border-orange-400 text-orange-400 hover:bg-orange-400 hover:text-white">
                          Read & Laugh
                        </Button>
                      </Link>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default ComedySection;