import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import axios from 'axios';
import { Clock, User, ArrowLeft, Share2, Eye, TrendingUp } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = BACKEND_URL;

const ArticleDetail = () => {
  const { id } = useParams();
  const [article, setArticle] = useState(null);
  const [relatedArticles, setRelatedArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchArticle();
    fetchRelatedArticles();
  }, [id]);

  const fetchArticle = async () => {
    try {
      const response = await axios.get(`${API}/articles/${id}`);
      setArticle(response.data);
    } catch (error) {
      console.error('Error fetching article:', error);
      setError('Article not found');
    }
  };

  const fetchRelatedArticles = async () => {
    try {
      const response = await axios.get(`${API}/articles/${id}/related`);
      setRelatedArticles(response.data);
    } catch (error) {
      console.error('Error fetching related articles:', error);
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
    return new Date(dateString).toLocaleDateString('en-GB', {
      year: 'numeric',
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getFullImageUrl = (imageUrl) => {
    if (!imageUrl) return null;
    if (imageUrl.startsWith('http')) return imageUrl;
    if (imageUrl.startsWith('/uploads/')) {
      return `${window.location.origin}${imageUrl}`;
    }
    return `${BACKEND_URL}${imageUrl}`;
  };

  const generateStructuredData = () => {
    if (!article) return {};
    
    return {
      "@context": "https://schema.org",
      "@type": "NewsArticle",
      "headline": article.title,
      "description": article.subheading || article.content.substring(0, 160),
      "image": article.featured_image ? getFullImageUrl(article.featured_image) : `${window.location.origin}/logo.png`,
      "datePublished": article.created_at,
      "dateModified": article.updated_at || article.created_at,
      "author": {
        "@type": "Person",
        "name": article.author_name || "The Crewkerne Gazette"
      },
      "publisher": {
        "@type": "Organization", 
        "name": "The Crewkerne Gazette",
        "logo": {
          "@type": "ImageObject",
          "url": `${window.location.origin}/logo.png`
        }
      },
      "mainEntityOfPage": {
        "@type": "WebPage",
        "@id": window.location.href
      }
    };
  };

  const formatDateForSchema = (dateString) => {
    return new Date(dateString).toISOString();
  };

  const shareArticle = (platform) => {
    const url = window.location.href;
    const text = `${article.title} - ${article.subheading || 'Read more on The Crewkerne Gazette'}`;
    
    let shareUrl = '';
    switch (platform) {
      case 'twitter':
        shareUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`;
        break;
      case 'facebook':
        shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`;
        break;
      case 'linkedin':
        shareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`;
        break;
      default:
        navigator.clipboard.writeText(url);
        return;
    }
    
    window.open(shareUrl, '_blank', 'width=600,height=400');
  };

  // Split content for trending topics insertion
  const getContentWithTrending = (content) => {
    const paragraphs = content.split('\n\n');
    if (paragraphs.length < 3) return content;
    
    const midPoint = Math.floor(paragraphs.length / 2);
    const firstHalf = paragraphs.slice(0, midPoint).join('\n\n');
    const secondHalf = paragraphs.slice(midPoint).join('\n\n');
    
    return { firstHalf, secondHalf, showTrending: true };
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white mb-4">Article Not Found</h1>
          <p className="text-slate-400 mb-8">The article you're looking for doesn't exist.</p>
          <Link to="/">
            <Button>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Home
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  const contentStructure = getContentWithTrending(article.content);
  const fullUrl = `${window.location.origin}/article/${article.id}`;

  // JSON-LD structured data for Google News
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    "headline": article.title,
    "description": article.subheading || article.content.substring(0, 160),
    "image": article.featured_image ? [article.featured_image] : undefined,
    "datePublished": formatDateForSchema(article.created_at),
    "dateModified": formatDateForSchema(article.updated_at),
    "author": {
      "@type": "Person",
      "name": article.publisher_name || article.author_name
    },
    "publisher": {
      "@type": "Organization",
      "name": "The Crewkerne Gazette",
      "logo": {
        "@type": "ImageObject",
        "url": `${window.location.origin}/gazette-logo.png`
      }
    },
    "mainEntityOfPage": {
      "@type": "WebPage",
      "@id": fullUrl
    },
    "articleSection": article.category,
    "keywords": article.tags?.join(", ")
  };

  return (
    <>
      {/* Google News SEO Meta Tags */}
      <Helmet>
        <title>{article.title} | The Crewkerne Gazette</title>
        <meta name="description" content={article.subheading || article.content.substring(0, 160)} />
        <meta property="og:title" content={article.title} />
        <meta property="og:description" content={article.subheading || article.content.substring(0, 160)} />
        <meta property="og:image" content={article.featured_image} />
        <meta property="og:url" content={fullUrl} />
        <meta property="og:type" content="article" />
        <meta property="og:site_name" content="The Crewkerne Gazette" />
        <meta property="article:published_time" content={formatDateForSchema(article.created_at)} />
        <meta property="article:modified_time" content={formatDateForSchema(article.updated_at)} />
        <meta property="article:author" content={article.publisher_name || article.author_name} />
        <meta property="article:section" content={article.category} />
        <meta property="article:tag" content={article.tags?.join(", ")} />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={article.title} />
        <meta name="twitter:description" content={article.subheading || article.content.substring(0, 160)} />
        <meta name="twitter:image" content={article.featured_image} />
        <link rel="canonical" content={fullUrl} />
        <script type="application/ld+json">
          {JSON.stringify(structuredData)}
        </script>
      </Helmet>

      <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800">
        <div className="container py-8">
          {/* Back Button */}
          <Link to="/" className="inline-flex items-center text-slate-400 hover:text-white mb-8 transition-colors">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Link>

          <article className="max-w-4xl mx-auto">
            {/* Article Header */}
            <header className="mb-8">
              <div className="flex items-center space-x-4 mb-6">
                <Badge className={`category-badge ${getCategoryBadgeClass(article.category)}`}>
                  {article.category}
                </Badge>
                {article.is_breaking && (
                  <Badge variant="destructive" className="animate-pulse bg-red-600 text-white font-bold">
                    BREAKING NEWS
                  </Badge>
                )}
              </div>

              {/* Breaking News Enhancement */}
              <div className="mb-6">
                {article.is_breaking && (
                  <div className="bg-red-600 text-white px-4 py-2 rounded-lg mb-4 font-bold uppercase tracking-wide">
                    🚨 BREAKING NEWS
                  </div>
                )}
                <h1 className="text-4xl md:text-5xl font-bold text-white mb-4 leading-tight">
                  {article.title}
                </h1>
                {article.subheading && (
                  <h2 className="text-xl text-slate-300 mb-4 font-medium leading-relaxed">
                    {article.subheading}
                  </h2>
                )}
              </div>

              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 text-slate-400">
                <div className="flex items-center space-x-6">
                  <span className="flex items-center">
                    <User className="w-4 h-4 mr-2" />
                    By {article.publisher_name || article.author_name}
                  </span>
                  <span className="flex items-center">
                    <Clock className="w-4 h-4 mr-2" />
                    {formatDate(article.created_at)}
                  </span>
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={shareArticle}
                  className="border-slate-600 text-slate-400 hover:border-slate-400"
                >
                  <Share2 className="w-4 h-4 mr-2" />
                  Share
                </Button>
              </div>
            </header>

            {/* Featured Image */}
            {article.featured_image && (
              <div className="mb-8 rounded-lg overflow-hidden">
                <img 
                  src={article.featured_image} 
                  alt={article.image_caption || article.title}
                  className="w-full h-96 object-cover"
                />
                {article.image_caption && (
                  <div className="bg-slate-800 p-4 text-sm text-slate-300 italic">
                    {article.image_caption}
                  </div>
                )}
              </div>
            )}

            {/* Article Content */}
            <div className="prose prose-lg prose-invert max-w-none">
              {typeof contentStructure === 'object' && contentStructure.showTrending ? (
                <>
                  {/* First Half of Content */}
                  <div 
                    className="text-slate-200 leading-relaxed text-lg mb-8"
                    style={{ whiteSpace: 'pre-wrap' }}
                  >
                    {contentStructure.firstHalf}
                  </div>

                  {/* Trending Topics Section */}
                  {relatedArticles.length > 0 && (
                    <Card className="bg-slate-800/60 border-red-600/30 my-8">
                      <CardHeader>
                        <CardTitle className="text-white flex items-center">
                          <TrendingUp className="w-5 h-5 mr-2 text-red-400" />
                          Trending Topics
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {relatedArticles.map((relatedArticle) => (
                            <Link 
                              key={relatedArticle.id} 
                              to={`/article/${relatedArticle.id}`}
                              className="block p-4 bg-slate-700/30 rounded-lg hover:bg-slate-700/50 transition-colors"
                            >
                              <div className="flex items-start space-x-4">
                                {relatedArticle.featured_image && (
                                  <img 
                                    src={relatedArticle.featured_image} 
                                    alt={relatedArticle.title}
                                    className="w-16 h-16 object-cover rounded"
                                  />
                                )}
                                <div className="flex-1">
                                  <h3 className="text-white font-medium hover:text-red-400 transition-colors">
                                    {relatedArticle.title}
                                  </h3>
                                  <p className="text-slate-400 text-sm mt-1">
                                    {new Date(relatedArticle.created_at).toLocaleDateString()}
                                  </p>
                                </div>
                              </div>
                            </Link>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Second Half of Content */}
                  <div 
                    className="text-slate-200 leading-relaxed text-lg"
                    style={{ whiteSpace: 'pre-wrap' }}
                  >
                    {contentStructure.secondHalf}
                  </div>
                </>
              ) : (
                <div 
                  className="text-slate-200 leading-relaxed text-lg"
                  style={{ whiteSpace: 'pre-wrap' }}
                >
                  {article.content}
                </div>
              )}
            </div>

            {/* Video Embed */}
            {article.video_url && (
              <div className="my-8 rounded-lg overflow-hidden bg-slate-800">
                <div className="aspect-video">
                  <iframe
                    src={article.video_url}
                    title={article.title}
                    className="w-full h-full"
                    allowFullScreen
                  />
                </div>
              </div>
            )}

            {/* Article Tags */}
            {article.tags && article.tags.length > 0 && (
              <div className="mt-8 pt-8 border-t border-slate-700">
                <h3 className="text-sm font-medium text-slate-400 mb-4">Tags:</h3>
                <div className="flex flex-wrap gap-2">
                  {article.tags.map((tag, index) => (
                    <Badge key={index} variant="secondary" className="text-xs">
                      #{tag}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Article Footer */}
            <footer className="mt-12 pt-8 border-t border-slate-700">
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="text-slate-400 text-sm">
                  Published on {formatDate(article.created_at)}
                  {article.updated_at !== article.created_at && (
                    <span> • Updated {formatDate(article.updated_at)}</span>
                  )}
                </div>
                <div className="flex items-center space-x-4">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={shareArticle}
                  >
                    <Share2 className="w-4 h-4 mr-2" />
                    Share Article
                  </Button>
                  <Link to={`/${article.category}`}>
                    <Button variant="outline" size="sm">
                      <Eye className="w-4 h-4 mr-2" />
                      More {article.category}
                    </Button>
                  </Link>
                </div>
              </div>
            </footer>
          </article>
        </div>
      </div>
    </>
  );
};

export default ArticleDetail;