import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Clock, ArrowRight, Users, Target, Globe, MessageCircle } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Card, CardContent } from './ui/card';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
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
      // Fetch news articles first (prioritized)
      const newsResponse = await axios.get(`${API}/articles?category=news&limit=6`);
      const otherResponse = await axios.get(`${API}/articles?limit=6`);
      
      // Combine news articles first, then other articles, avoiding duplicates
      const newsArticles = newsResponse.data || [];
      const otherArticles = (otherResponse.data || []).filter(
        article => !newsArticles.some(newsArticle => newsArticle.id === article.id)
      );
      
      // Prioritize news articles at the top
      const combinedArticles = [...newsArticles, ...otherArticles].slice(0, 6);
      setArticles(combinedArticles);
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
      {breakingNews.length > 0 && showBanner && (
        <div className="breaking-news-ticker">
          <div className="breaking-badge">
            BREAKING
          </div>
          <div className="ticker-content">
            {breakingNews.map((news, index) => (
              <Link key={news.id} to={`/article/${news.id}`} className="ticker-link">
                {news.title}
                {index < breakingNews.length - 1 && ' • '}
              </Link>
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
            WHERE COMMON SENSE MEETS HEADLINES
          </h1>
          <p className="hero-subtitle">
            Bold, unapologetic journalism from Somerset to the nation. 
            We challenge the establishment, celebrate British life, and give a voice 
            to those who feel overlooked. No spin. No fluff. Just the Gazette.
          </p>
          <div className="hero-cta">
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/news">
                <Button size="lg" className="btn-primary">
                  <Target className="w-5 h-5 mr-2" />
                  Read The Truth
                </Button>
              </Link>
              <Link to="/contact">
                <Button variant="outline" size="lg" className="btn-secondary">
                  <MessageCircle className="w-5 h-5 mr-2" />
                  Join Our Voice
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* About Section */}
      <section className="py-20 bg-gradient-to-b from-transparent to-slate-800/50">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">PROUDLY FROM CREWKERNE</h2>
            <p className="section-subtitle">
              A home for straight-talking, no-nonsense journalism and entertainment
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <div className="text-slate-200 space-y-4 text-lg leading-relaxed">
                <p>
                  Welcome to <strong className="text-red-400">The Crewkerne Gazette</strong> — a bold, 
                  unapologetic publication with its roots in Somerset and its eyes on the nation.
                </p>
                <p>
                  We are here to challenge the stale voices of the establishment and offer something fresh: 
                  a platform that speaks plainly, asks the right questions, and gives people a reason to care again.
                </p>
                <p>
                  The Gazette isn't just another outlet. It's a home for straight-talking journalism 
                  that puts <strong className="text-red-400">common sense first</strong>, not political spin.
                </p>
              </div>
              <div className="flex flex-wrap gap-3">
                <Badge className="bg-red-600/20 text-red-300 border border-red-600/30 px-4 py-2">
                  Free Speech
                </Badge>
                <Badge className="bg-red-600/20 text-red-300 border border-red-600/30 px-4 py-2">
                  Common Sense
                </Badge>
                <Badge className="bg-red-600/20 text-red-300 border border-red-600/30 px-4 py-2">
                  British Pride
                </Badge>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <Card className="bg-slate-800/60 border-red-600/30">
                <CardContent className="p-6">
                  <Globe className="w-8 h-8 text-red-400 mb-3" />
                  <h3 className="font-bold text-white mb-2">FROM SOMERSET</h3>
                  <p className="text-slate-300 text-sm">
                    Rooted in local community, reaching national conversations
                  </p>
                </CardContent>
              </Card>
              
              <Card className="bg-slate-800/60 border-red-600/30">
                <CardContent className="p-6">
                  <Target className="w-8 h-8 text-red-400 mb-3" />
                  <h3 className="font-bold text-white mb-2">NO NONSENSE</h3>
                  <p className="text-slate-300 text-sm">
                    Sharp, punchy reporting that cuts through the noise
                  </p>
                </CardContent>
              </Card>
              
              <Card className="bg-slate-800/60 border-red-600/30">
                <CardContent className="p-6">
                  <Users className="w-8 h-8 text-red-400 mb-3" />
                  <h3 className="font-bold text-white mb-2">YOUR VOICE</h3>
                  <p className="text-slate-300 text-sm">
                    A platform for those who feel overlooked by mainstream media
                  </p>
                </CardContent>
              </Card>
              
              <Card className="bg-slate-800/60 border-red-600/30">
                <CardContent className="p-6">
                  <ArrowRight className="w-8 h-8 text-red-400 mb-3" />
                  <h3 className="font-bold text-white mb-2">ALIVE AGAIN</h3>
                  <p className="text-slate-300 text-sm">
                    Making news and culture feel vibrant and relevant
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Articles */}
      <section className="py-20">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">NEWS WITH BITE</h2>
            <p className="section-subtitle">
              Stories told in a way that cuts through the noise. 
              British life as it's lived — with all its grit, humor, and contradictions.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 stagger-children">
            {articles.map((article) => (
              <Link 
                key={article.slug} 
                to={`/article/${article.slug}`}
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
                        URGENT
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
                More Straight Talk
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* What We Do Section */}
      <section className="py-20 bg-gradient-to-b from-slate-800/50 to-slate-900">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">WHAT WE DO</h2>
            <p className="section-subtitle">
              Culture with style. Comedy with grit. All boldly unapologetic and alive.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 stagger-children">
            {/* News Section */}
            <Link to="/news" className="group">
              <div className="article-card h-96 flex flex-col">
                <img 
                  src="https://images.unsplash.com/photo-1675973094287-f4af3e49bb3d" 
                  alt="News Division"
                  className="article-image flex-1"
                />
                <div className="p-6 text-center bg-gradient-to-t from-red-900/20 to-transparent">
                  <div className="category-badge category-news mb-3">NEWS</div>
                  <h3 className="text-xl font-bold text-red-400 group-hover:text-red-300 mb-3">
                    SHARP & PUNCHY
                  </h3>
                  <p className="text-sm text-slate-400">
                    Unfiltered stories that cut through the noise and tell it like it is
                  </p>
                </div>
              </div>
            </Link>

            {/* Music Section */}
            <Link to="/music" className="group">
              <div className="article-card h-96 flex flex-col">
                <img 
                  src="https://images.unsplash.com/photo-1598488035139-bdbb2231ce04" 
                  alt="Music Culture"
                  className="article-image flex-1"
                />
                <div className="p-6 text-center bg-gradient-to-t from-purple-900/20 to-transparent">
                  <div className="category-badge category-music mb-3">MUSIC</div>
                  <h3 className="text-xl font-bold text-purple-400 group-hover:text-purple-300 mb-3">
                    RAW & AUTHENTIC
                  </h3>
                  <p className="text-sm text-slate-400">
                    Sounds and culture that reflect the people — energetic and real
                  </p>
                </div>
              </div>
            </Link>

            {/* Documentaries Section */}
            <Link to="/documentaries" className="group">
              <div className="article-card h-96 flex flex-col">
                <img 
                  src="https://images.unsplash.com/photo-1570882004527-319ba653f4d6" 
                  alt="Documentary Investigations"
                  className="article-image flex-1"
                />
                <div className="p-6 text-center bg-gradient-to-t from-blue-900/20 to-transparent">
                  <div className="category-badge category-documentaries mb-3">DOCS</div>
                  <h3 className="text-xl font-bold text-blue-400 group-hover:text-blue-300 mb-3">
                    STYLE & SUBSTANCE
                  </h3>
                  <p className="text-sm text-slate-400">
                    In-depth explorations of history, crime, and issues that matter
                  </p>
                </div>
              </div>
            </Link>

            {/* Comedy Section */}
            <Link to="/comedy" className="group">
              <div className="article-card h-96 flex flex-col">
                <img 
                  src="https://images.unsplash.com/photo-1527224857830-43a7acc85260" 
                  alt="Comedy & Satire"
                  className="article-image flex-1"
                />
                <div className="p-6 text-center bg-gradient-to-t from-orange-900/20 to-transparent">
                  <div className="category-badge category-comedy mb-3">COMEDY</div>
                  <h3 className="text-xl font-bold text-orange-400 group-hover:text-orange-300 mb-3">
                    LEVITY & LAUGHTER
                  </h3>
                  <p className="text-sm text-slate-400">
                    Satire and sketches that poke fun at the modern circus
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