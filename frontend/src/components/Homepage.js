import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Clock, ArrowRight, TrendingUp } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Homepage = () => {
  const [articles, setArticles] = useState([]);
  const [breakingNews, setBreakingNews] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchArticles();
    fetchBreakingNews();
  }, []);

  const fetchArticles = async () => {
    try {
      const response = await axios.get(`${API}/articles?limit=6`);
      setArticles(response.data);
    } catch (error) {
      console.error('Error fetching articles:', error);
    }
  };

  const fetchBreakingNews = async () => {
    try {
      const response = await axios.get(`${API}/articles?is_breaking=true&limit=3`);
      setBreakingNews(response.data);
    } catch (error) {
      console.error('Error fetching breaking news:', error);
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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div>
      {/* Breaking News Ticker */}
      {breakingNews.length > 0 && (
        <div className="breaking-news-ticker">
          <div className="ticker-text">
            <strong>BREAKING:</strong> {breakingNews.map((news, index) => (
              <span key={news.id}>
                {news.title}
                {index < breakingNews.length - 1 && ' • '}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-bg"></div>
        <div className="hero-content">
          <h1 className="hero-title">
            Bold Stories, Unfiltered Truth
          </h1>
          <p className="hero-subtitle">
            Your source for breaking news, original music, compelling documentaries, 
            and cutting-edge comedy that challenges the status quo.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" className="btn-primary">
              <TrendingUp className="w-5 h-5 mr-2" />
              Latest Stories
            </Button>
            <Button variant="outline" size="lg">
              Subscribe to Updates
            </Button>
          </div>
        </div>
      </section>

      {/* Featured Articles */}
      <section className="py-16">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">Latest Stories</h2>
            <p className="section-subtitle">
              Stay informed with our most recent coverage across news, music, 
              documentaries, and comedy.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 stagger-children">
            {articles.map((article) => (
              <Link 
                key={article.id} 
                to={`/article/${article.id}`}
                className="article-card"
              >
                {article.featured_image && (
                  <img 
                    src={article.featured_image} 
                    alt={article.title}
                    className="article-image"
                  />
                )}
                <div className="article-content">
                  <div className="flex items-center justify-between mb-3">
                    <Badge className={`category-badge ${getCategoryBadgeClass(article.category)}`}>
                      {article.category}
                    </Badge>
                    {article.is_breaking && (
                      <Badge variant="destructive" className="text-xs">
                        BREAKING
                      </Badge>
                    )}
                  </div>
                  <h3 className="article-title">{article.title}</h3>
                  <p className="article-excerpt">
                    {article.content.substring(0, 120)}...
                  </p>
                  <div className="article-meta">
                    <span className="flex items-center">
                      <Clock className="w-3 h-3 mr-1" />
                      {formatDate(article.created_at)}
                    </span>
                    <span>By {article.author_name}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>

          <div className="text-center mt-12">
            <Link to="/news">
              <Button size="lg" variant="outline">
                View All Articles
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Sections Preview */}
      <section className="py-16 bg-slate-800/50">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">Explore Our Sections</h2>
            <p className="section-subtitle">
              Dive deeper into our specialized content areas
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 stagger-children">
            {/* News Section */}
            <Link to="/news" className="group">
              <div className="article-card h-64 flex flex-col">
                <img 
                  src="https://images.unsplash.com/photo-1675973094287-f4af3e49bb3d" 
                  alt="News"
                  className="article-image flex-1"
                />
                <div className="p-6 text-center">
                  <h3 className="text-xl font-bold text-red-400 group-hover:text-red-300">
                    News
                  </h3>
                  <p className="text-sm text-slate-400 mt-2">
                    Breaking stories and in-depth analysis
                  </p>
                </div>
              </div>
            </Link>

            {/* Music Section */}
            <Link to="/music" className="group">
              <div className="article-card h-64 flex flex-col">
                <img 
                  src="https://images.unsplash.com/photo-1598488035139-bdbb2231ce04" 
                  alt="Music"
                  className="article-image flex-1"
                />
                <div className="p-6 text-center">
                  <h3 className="text-xl font-bold text-purple-400 group-hover:text-purple-300">
                    Music
                  </h3>
                  <p className="text-sm text-slate-400 mt-2">
                    Original tracks and audio content
                  </p>
                </div>
              </div>
            </Link>

            {/* Documentaries Section */}
            <Link to="/documentaries" className="group">
              <div className="article-card h-64 flex flex-col">
                <img 
                  src="https://images.unsplash.com/photo-1570882004527-319ba653f4d6" 
                  alt="Documentaries"
                  className="article-image flex-1"
                />
                <div className="p-6 text-center">
                  <h3 className="text-xl font-bold text-blue-400 group-hover:text-blue-300">
                    Documentaries
                  </h3>
                  <p className="text-sm text-slate-400 mt-2">
                    Cinematic storytelling and investigations
                  </p>
                </div>
              </div>
            </Link>

            {/* Comedy Section */}
            <Link to="/comedy" className="group">
              <div className="article-card h-64 flex flex-col">
                <img 
                  src="https://images.unsplash.com/photo-1527224857830-43a7acc85260" 
                  alt="Comedy"
                  className="article-image flex-1"
                />
                <div className="p-6 text-center">
                  <h3 className="text-xl font-bold text-orange-400 group-hover:text-orange-300">
                    Comedy
                  </h3>
                  <p className="text-sm text-slate-400 mt-2">
                    Satirical takes and comedic content
                  </p>
                </div>
              </div>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Homepage;