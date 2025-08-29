import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Clock, ArrowRight, Zap, TrendingUp, Users } from 'lucide-react';
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
          <div className="breaking-badge">
            BREAKING
          </div>
          <div className="ticker-content">
            {breakingNews.map((news, index) => (
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
        <div className="hero-overlay"></div>
        <div className="hero-content">
          <h1 className="hero-title">
            UNFILTERED TRUTH FOR THE PEOPLE
          </h1>
          <p className="hero-subtitle">
            Bold journalism that challenges the establishment. Real stories, real facts, 
            real impact. Your voice in the fight for transparency and accountability.
          </p>
          <div className="hero-cta">
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" className="btn-primary">
                <TrendingUp className="w-5 h-5 mr-2" />
                Latest Stories
              </Button>
              <Button variant="outline" size="lg" className="btn-secondary">
                <Users className="w-5 h-5 mr-2" />
                Join the Movement
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Articles */}
      <section className="py-20 bg-gradient-to-b from-transparent to-slate-800/50">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">BREAKING THE SILENCE</h2>
            <p className="section-subtitle">
              The stories they don't want you to see. Fearless reporting that 
              cuts through the noise to deliver the truth that matters most.
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
                  <div className="flex items-center justify-between mb-4">
                    <Badge className={`category-badge ${getCategoryBadgeClass(article.category)}`}>
                      {article.category.toUpperCase()}
                    </Badge>
                    {article.is_breaking && (
                      <div className="breaking-alert">
                        HOT
                      </div>
                    )}
                  </div>
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
            ))}
          </div>

          <div className="text-center mt-16">
            <Link to="/news">
              <Button size="lg" variant="outline" className="btn-secondary">
                More Truth Bombs
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Sections Preview */}
      <section className="py-20 bg-gradient-to-b from-slate-800/50 to-slate-900">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">WHAT WE COVER</h2>
            <p className="section-subtitle">
              From breaking news to cultural commentary - we've got the stories 
              that shape your world, told without fear or favor.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 stagger-children">
            {/* News Section */}
            <Link to="/news" className="group">
              <div className="article-card h-80 flex flex-col">
                <img 
                  src="https://images.unsplash.com/photo-1675973094287-f4af3e49bb3d" 
                  alt="Breaking News"
                  className="article-image flex-1"
                />
                <div className="p-6 text-center bg-gradient-to-t from-red-900/20 to-transparent">
                  <div className="category-badge category-news mb-3">NEWS</div>
                  <h3 className="text-xl font-bold text-red-400 group-hover:text-red-300 mb-2">
                    BREAKING NEWS
                  </h3>
                  <p className="text-sm text-slate-400">
                    The stories that matter, told without compromise
                  </p>
                </div>
              </div>
            </Link>

            {/* Music Section */}
            <Link to="/music" className="group">
              <div className="article-card h-80 flex flex-col">
                <img 
                  src="https://images.unsplash.com/photo-1598488035139-bdbb2231ce04" 
                  alt="Music"
                  className="article-image flex-1"
                />
                <div className="p-6 text-center bg-gradient-to-t from-purple-900/20 to-transparent">
                  <div className="category-badge category-music mb-3">MUSIC</div>
                  <h3 className="text-xl font-bold text-purple-400 group-hover:text-purple-300 mb-2">
                    SOUND & FURY
                  </h3>
                  <p className="text-sm text-slate-400">
                    Music that moves culture and changes minds
                  </p>
                </div>
              </div>
            </Link>

            {/* Documentaries Section */}
            <Link to="/documentaries" className="group">
              <div className="article-card h-80 flex flex-col">
                <img 
                  src="https://images.unsplash.com/photo-1570882004527-319ba653f4d6" 
                  alt="Documentaries"
                  className="article-image flex-1"
                />
                <div className="p-6 text-center bg-gradient-to-t from-blue-900/20 to-transparent">
                  <div className="category-badge category-documentaries mb-3">DOCS</div>
                  <h3 className="text-xl font-bold text-blue-400 group-hover:text-blue-300 mb-2">
                    DEEP DIVES
                  </h3>
                  <p className="text-sm text-slate-400">
                    Investigative documentaries that expose the truth
                  </p>
                </div>
              </div>
            </Link>

            {/* Comedy Section */}
            <Link to="/comedy" className="group">
              <div className="article-card h-80 flex flex-col">
                <img 
                  src="https://images.unsplash.com/photo-1527224857830-43a7acc85260" 
                  alt="Comedy"
                  className="article-image flex-1"
                />
                <div className="p-6 text-center bg-gradient-to-t from-orange-900/20 to-transparent">
                  <div className="category-badge category-comedy mb-3">COMEDY</div>
                  <h3 className="text-xl font-bold text-orange-400 group-hover:text-orange-300 mb-2">
                    TRUTH BOMBS
                  </h3>
                  <p className="text-sm text-slate-400">
                    Humor that cuts deeper than any headline
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