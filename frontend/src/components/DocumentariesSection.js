import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Clock, Play, Film, ExternalLink, Youtube } from 'lucide-react';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DocumentariesSection = () => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDocumentaries();
  }, []);

  const fetchDocumentaries = async () => {
    try {
      const response = await axios.get(`${API}/articles?category=documentaries&limit=12`);
      setArticles(response.data);
    } catch (error) {
      console.error('Error fetching documentaries:', error);
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
                           url('https://images.unsplash.com/photo-1570882004527-319ba653f4d6')`
        }}
      >
        <div className="container">
          <div className="text-center">
            <h1 className="text-5xl font-bold text-white mb-6 uppercase tracking-wider">
              DEEP DIVES
            </h1>
            <p className="text-xl text-slate-300 max-w-2xl mx-auto mb-8">
              Investigative documentaries that expose the truth. Watch our latest 
              documentary-style videos and deep investigations on YouTube.
            </p>
            
            {/* YouTube Channel Link */}
            <div className="flex justify-center">
              <a 
                href="https://m.youtube.com/@TheCrewkerneGazette" 
                target="_blank" 
                rel="noopener noreferrer"
                className="btn btn-primary"
              >
                <Youtube className="w-5 h-5 mr-2" />
                Watch on YouTube
                <ExternalLink className="w-4 h-4 ml-2" />
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Featured YouTube Section */}
      <section className="py-16 bg-slate-800/50">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">LATEST DOCUMENTARIES</h2>
            <p className="section-subtitle">
              Watch our investigative documentaries and exposé videos
            </p>
          </div>

          {/* YouTube Channel Embed */}
          <div className="max-w-4xl mx-auto mb-12">
            <Card className="bg-slate-800/80 border-blue-600/30">
              <CardContent className="p-6">
                <div className="flex items-center mb-4">
                  <Youtube className="w-6 h-6 text-red-400 mr-3" />
                  <h3 className="text-xl font-bold text-white">The Crewkerne Gazette Channel</h3>
                </div>
                <div className="aspect-video bg-slate-900 rounded-lg overflow-hidden">
                  <iframe 
                    src="https://www.youtube.com/embed/videoseries?list=UULFolderIdHere" 
                    width="100%" 
                    height="100%" 
                    frameBorder="0" 
                    allowFullScreen
                    className="rounded-lg"
                    title="The Crewkerne Gazette Documentaries"
                  />
                </div>
                <div className="mt-4 text-center">
                  <a 
                    href="https://m.youtube.com/@TheCrewkerneGazette" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-red-400 hover:text-red-300 flex items-center justify-center"
                  >
                    Visit our YouTube channel for all documentaries
                    <ExternalLink className="w-4 h-4 ml-2" />
                  </a>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Documentary Features */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
            <Card className="bg-slate-800/60 border-blue-600/30">
              <CardContent className="p-6 text-center">
                <Film className="w-12 h-12 text-blue-400 mx-auto mb-4" />
                <h3 className="text-lg font-bold text-white mb-2">INVESTIGATIVE REPORTS</h3>
                <p className="text-slate-300 text-sm">
                  Deep-dive investigations into corruption, cover-ups, and stories the mainstream won't touch.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/60 border-blue-600/30">
              <CardContent className="p-6 text-center">
                <Play className="w-12 h-12 text-blue-400 mx-auto mb-4" />
                <h3 className="text-lg font-bold text-white mb-2">EXCLUSIVE INTERVIEWS</h3>
                <p className="text-slate-300 text-sm">
                  One-on-one conversations with whistleblowers, experts, and those fighting for truth.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/60 border-blue-600/30">
              <CardContent className="p-6 text-center">
                <Youtube className="w-12 h-12 text-blue-400 mx-auto mb-4" />
                <h3 className="text-lg font-bold text-white mb-2">WEEKLY RELEASES</h3>
                <p className="text-slate-300 text-sm">
                  New documentary content every week, covering the issues that matter most to our community.
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Call to Action */}
          <div className="text-center">
            <h3 className="text-2xl font-bold text-white mb-4">
              SUBSCRIBE FOR TRUTH
            </h3>
            <p className="text-slate-300 mb-6 max-w-2xl mx-auto">
              Don't miss our latest investigations. Subscribe to our YouTube channel 
              and turn on notifications for breaking documentary releases.
            </p>
            <a 
              href="https://m.youtube.com/@TheCrewkerneGazette" 
              target="_blank" 
              rel="noopener noreferrer"
              className="btn btn-primary"
            >
              <Youtube className="w-5 h-5 mr-2" />
              Subscribe Now
            </a>
          </div>
        </div>
      </section>

      {/* Documentary Articles Grid */}
      <section className="py-16">
        <div className="container">
          {articles.length > 0 && (
            <>
              <div className="section-header">
                <h2 className="section-title">BEHIND THE SCENES</h2>
                <p className="section-subtitle">
                  Read about our documentary projects, investigations, and the stories behind the stories
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 stagger-children">
                {articles.map((article) => (
                  <div key={article.id} className="article-card group">
                    {article.featured_image && (
                      <div className="relative overflow-hidden">
                        <img 
                          src={article.featured_image} 
                          alt={article.title}
                          className="article-image group-hover:scale-110 transition-transform duration-500"
                        />
                        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                          <Button size="lg" className="bg-blue-600 hover:bg-blue-700">
                            <Play className="w-5 h-5 mr-2" />
                            Read
                          </Button>
                        </div>
                        <div className="absolute top-4 left-4">
                          <Badge className="bg-blue-600/80 text-white">
                            Documentary
                          </Badge>
                        </div>
                      </div>
                    )}
                    <div className="article-content">
                      <div className="flex items-center justify-between mb-3">
                        <Badge className="category-badge category-documentaries">
                          Documentaries
                        </Badge>
                      </div>
                      <h3 className="article-title group-hover:text-blue-400 transition-colors">
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
                          <Button variant="outline" size="sm" className="w-full border-blue-400 text-blue-400 hover:bg-blue-400 hover:text-white">
                            Learn More
                          </Button>
                        </Link>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          {articles.length === 0 && (
            <div className="text-center py-16">
              <Film className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <h3 className="text-2xl font-semibold text-slate-300 mb-4">
                MORE DOCUMENTARY CONTENT COMING SOON
              </h3>
              <p className="text-slate-400 mb-6">
                Check out our YouTube channel for the latest investigative documentaries and video content.
              </p>
              <a 
                href="https://m.youtube.com/@TheCrewkerneGazette" 
                target="_blank" 
                rel="noopener noreferrer"
                className="btn btn-primary"
              >
                <Youtube className="w-5 h-5 mr-2" />
                Watch Now
              </a>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default DocumentariesSection;