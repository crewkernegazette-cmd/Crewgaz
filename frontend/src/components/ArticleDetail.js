import React, { useState, useEffect, useContext } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { AuthContext } from '../App';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Calendar, User, Share2, ArrowLeft, Clock, Eye } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const ArticleDetail = () => {
  const { slug } = useParams();
  const { user } = useContext(AuthContext);
  const [article, setArticle] = useState(null);
  const [relatedArticles, setRelatedArticles] = useState([]);
  const [structuredData, setStructuredData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchArticle();
  }, [slug]);

  const fetchArticle = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/articles/${slug}`);
      setArticle(response.data);
      
      // Fetch related articles (for now, use general articles endpoint)
      const relatedResponse = await axios.get(`${BACKEND_URL}/articles?limit=3&category=${response.data.category}`);
      const filteredRelated = relatedResponse.data.filter(a => a.slug !== slug);
      setRelatedArticles(filteredRelated.slice(0, 3));
      
      // Fetch structured data
      const structuredResponse = await axios.get(`${BACKEND_URL}/articles/${slug}/structured-data`);
      setStructuredData(structuredResponse.data);
      
    } catch (error) {
      console.error('Error fetching article:', error);
      setError('Article not found');
    } finally {
      setLoading(false);
    }
  };

  const shareArticle = (platform) => {
    const url = window.location.href;
    const text = `${article.title}${article.subheading ? ` - ${article.subheading}` : ''} | The Crewkerne Gazette`;
    
    let shareUrl = '';
    switch (platform) {
      case 'twitter':
        shareUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`;
        break;
      case 'facebook':
        shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`;
        break;
      case 'linkedin':
        shareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}&title=${encodeURIComponent(article.title)}`;
        break;
      default:
        // Copy to clipboard
        navigator.clipboard.writeText(url).then(() => {
          showToast('Link copied to clipboard!', 'success');
        }).catch(() => {
          showToast('Failed to copy link', 'error');
        });
        return;
    }
    
    window.open(shareUrl, '_blank', 'width=600,height=400');
  };

  const showToast = (message, type = 'success') => {
    const toast = document.createElement('div');
    toast.textContent = message;
    toast.className = `fixed top-4 right-4 px-4 py-2 rounded shadow-lg z-50 text-white ${
      type === 'success' ? 'bg-green-600' : 'bg-red-600'
    }`;
    document.body.appendChild(toast);
    setTimeout(() => {
      if (document.body.contains(toast)) {
        document.body.removeChild(toast);
      }
    }, 3000);
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

  const formatDateForSchema = (dateString) => {
    return new Date(dateString).toISOString();
  };

  const getFullImageUrl = (imageUrl) => {
    if (!imageUrl) return null;
    // Return data URIs and full HTTP URLs as-is
    if (imageUrl.startsWith('data:') || imageUrl.startsWith('http')) {
      return imageUrl;
    }
    // Fallback for relative URLs
    return `${BACKEND_URL}${imageUrl}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
          <p className="text-slate-300 mt-4">Loading article...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Article Not Found</h1>
          <p className="text-slate-300 mb-6">The article you're looking for doesn't exist.</p>
          <Link to="/">
            <Button className="bg-red-600 hover:bg-red-700">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Home
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  if (!article) return null;

  const fullImageUrl = getFullImageUrl(article.featured_image);
  const fullUrl = `${window.location.origin}/article/${article.id}`;

  return (
    <>
      <Helmet>
        <title>{article.title} | The Crewkerne Gazette</title>
        <meta name="description" content={article.subheading || article.content.substring(0, 160)} />
        
        {/* Open Graph / Facebook */}
        <meta property="og:type" content="article" />
        <meta property="og:title" content={article.title} />
        <meta property="og:description" content={article.subheading || article.content.substring(0, 160)} />
        <meta property="og:image" content={fullImageUrl || `${window.location.origin}/logo.png`} />
        <meta property="og:url" content={fullUrl} />
        <meta property="og:site_name" content="The Crewkerne Gazette" />
        
        {/* Article specific meta */}
        <meta property="article:published_time" content={formatDateForSchema(article.created_at)} />
        <meta property="article:modified_time" content={formatDateForSchema(article.updated_at)} />
        <meta property="article:author" content={article.author_name || article.publisher_name} />
        <meta property="article:section" content={article.category} />
        {article.tags && article.tags.map(tag => (
          <meta key={tag} property="article:tag" content={tag} />
        ))}
        
        {/* Twitter */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={article.title} />
        <meta name="twitter:description" content={article.subheading || article.content.substring(0, 160)} />
        <meta name="twitter:image" content={fullImageUrl || `${window.location.origin}/logo.png`} />
        <meta name="twitter:site" content="@CrewkerneGazette" />
        
        {/* Structured Data */}
        {structuredData && (
          <script type="application/ld+json">
            {JSON.stringify(structuredData)}
          </script>
        )}
      </Helmet>

      <div className="min-h-screen bg-black text-white">
        <div className="container mx-auto px-4 py-8">
          {/* Back Button */}
          <div className="mb-6">
            <Link to="/">
              <Button variant="outline" className="border-slate-600 text-slate-300 hover:border-slate-400">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Articles
              </Button>
            </Link>
          </div>

          <article className="max-w-4xl mx-auto">
            {/* Article Header */}
            <header className="mb-8">
              {article.is_breaking && (
                <div className="mb-4">
                  <Badge className="bg-red-600 text-white font-bold px-3 py-1">
                    BREAKING NEWS
                  </Badge>
                </div>
              )}

              <h1 className="text-4xl md:text-5xl font-bold text-white mb-4 leading-tight">
                {article.title}
              </h1>

              {article.subheading && (
                <h2 className="text-xl md:text-2xl text-slate-300 mb-6 font-medium leading-relaxed">
                  {article.subheading}
                </h2>
              )}

              {/* Article Meta */}
              <div className="flex flex-wrap items-center gap-4 text-slate-400 text-sm mb-6">
                <div className="flex items-center space-x-2">
                  <User className="w-4 h-4" />
                  <span>By {article.author_name || article.publisher_name}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Calendar className="w-4 h-4" />
                  <span>{formatDate(article.created_at)}</span>
                </div>
                {article.updated_at !== article.created_at && (
                  <div className="flex items-center space-x-2">
                    <Clock className="w-4 h-4" />
                    <span>Updated {formatDate(article.updated_at)}</span>
                  </div>
                )}
                <div className="flex items-center space-x-2">
                  <Eye className="w-4 h-4" />
                  <span>{article.category.charAt(0).toUpperCase() + article.category.slice(1)}</span>
                </div>
              </div>

              {/* Tags */}
              {article.tags && article.tags.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-6">
                  {article.tags.map(tag => (
                    <Badge key={tag} variant="outline" className="border-slate-600 text-slate-300">
                      {tag}
                    </Badge>
                  ))}
                </div>
              )}

              {/* Share Buttons */}
              <div className="flex flex-wrap items-center gap-3 pt-4 border-t border-slate-700">
                <span className="text-slate-400 text-sm font-medium">Share:</span>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => shareArticle('twitter')}
                  className="border-slate-600 text-slate-400 hover:border-blue-400 hover:text-blue-400 transition-colors"
                >
                  <Share2 className="w-4 h-4 mr-2" />
                  Twitter
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => shareArticle('facebook')}
                  className="border-slate-600 text-slate-400 hover:border-blue-600 hover:text-blue-600 transition-colors"
                >
                  <Share2 className="w-4 h-4 mr-2" />
                  Facebook
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => shareArticle('linkedin')}
                  className="border-slate-600 text-slate-400 hover:border-blue-500 hover:text-blue-500 transition-colors"
                >
                  <Share2 className="w-4 h-4 mr-2" />
                  LinkedIn
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => shareArticle()}
                  className="border-slate-600 text-slate-400 hover:border-slate-400"
                >
                  <Share2 className="w-4 h-4 mr-2" />
                  Copy Link
                </Button>
              </div>
            </header>

            {/* Featured Image */}
            {article.featured_image && (
              <div className="mb-8 rounded-lg overflow-hidden">
                <img 
                  src={fullImageUrl} 
                  alt={article.image_caption || article.title}
                  className="w-full h-96 object-cover"
                  onError={(e) => {
                    console.error('Image load error:', e);
                    e.target.style.display = 'none';
                  }}
                />
                {article.image_caption && (
                  <div className="bg-slate-800 p-4 text-sm text-slate-300 italic">
                    {article.image_caption}
                  </div>
                )}
              </div>
            )}

            {/* Article Content */}
            <div className="prose prose-invert max-w-none">
              <div 
                className="text-lg leading-relaxed text-slate-200"
                dangerouslySetInnerHTML={{ __html: article.content.replace(/\n/g, '<br />') }}
              />
            </div>

            {/* Video Embed */}
            {article.video_url && (
              <div className="mt-8">
                <div className="aspect-video">
                  <iframe
                    src={article.video_url}
                    title="Article Video"
                    className="w-full h-full rounded-lg"
                    allowFullScreen
                  />
                </div>
              </div>
            )}

            {/* Related Articles */}
            {relatedArticles.length > 0 && (
              <div className="mt-12 pt-8 border-t border-slate-700">
                <h3 className="text-2xl font-bold mb-6 text-white">Related Articles</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {relatedArticles.map(relatedArticle => (
                    <Link
                      key={relatedArticle.id}
                      to={`/article/${relatedArticle.id}`}
                      className="group block bg-slate-900/50 rounded-lg overflow-hidden hover:bg-slate-800/50 transition-colors"
                    >
                      {relatedArticle.featured_image && (
                        <img
                          src={getFullImageUrl(relatedArticle.featured_image)}
                          alt={relatedArticle.title}
                          className="w-full h-32 object-cover"
                          onError={(e) => e.target.style.display = 'none'}
                        />
                      )}
                      <div className="p-4">
                        <h4 className="font-semibold text-white group-hover:text-red-400 transition-colors line-clamp-2">
                          {relatedArticle.title}
                        </h4>
                        <p className="text-sm text-slate-400 mt-2">
                          {formatDate(relatedArticle.created_at)}
                        </p>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </article>
        </div>
      </div>
    </>
  );
};

export default ArticleDetail;