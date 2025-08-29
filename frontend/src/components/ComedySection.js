import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Clock, Smile, Zap, Laugh, ExternalLink, Youtube } from 'lucide-react';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = BACKEND_URL;

const ComedySection = () => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  // Your actual comedy videos
  const comedyVideos = [
    { id: 'd68tPxozCVk', title: 'Comedy Sketch 1' },
    { id: 'Pw_LZkP6FLo', title: 'Comedy Sketch 2' },
    { id: 'XoOje2jhmXs', title: 'Comedy Sketch 3' },
    { id: 'Hgo4WBSXC9g', title: 'Comedy Sketch 4' }
  ];

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
          backgroundImage: `linear-gradient(135deg, rgba(17, 24, 39, 0.9), rgba(31, 41, 55, 0.8)), 
                           url('https://images.unsplash.com/photo-1527224857830-43a7acc85260')`
        }}
      >
        <div className="container">
          <div className="text-center">
            <h1 className="text-5xl font-bold text-white mb-6 uppercase tracking-wider">
              LEVITY & LAUGHTER
            </h1>
            <p className="text-xl text-slate-300 max-w-3xl mx-auto mb-8">
              Satire and sketches that bring levity and laughter while poking fun at the modern circus. 
              Comedy with grit that dares to laugh at the absurdities of our times.
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
                Watch More Comedy
                <ExternalLink className="w-4 h-4 ml-2" />
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Comedy Videos Section */}
      <section className="py-16 bg-slate-800/50">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">SATIRICAL SKETCHES</h2>
            <p className="section-subtitle">
              Comedy that cuts deeper than any headline — laughing at the modern circus
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
            {comedyVideos.map((video, index) => (
              <Card key={video.id} className="bg-slate-800/80 border-orange-600/30">
                <CardContent className="p-6">
                  <div className="aspect-video bg-slate-900 rounded-lg overflow-hidden mb-4">
                    <iframe 
                      src={`https://www.youtube.com/embed/${video.id}`}
                      width="100%" 
                      height="100%" 
                      frameBorder="0" 
                      allowFullScreen
                      className="rounded-lg"
                      title={`The Crewkerne Gazette Comedy ${index + 1}`}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Badge className="bg-orange-600/80 text-white">
                      SKETCH {index + 1}
                    </Badge>
                    <a 
                      href={`https://youtu.be/${video.id}`}
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-orange-400 hover:text-orange-300 text-sm flex items-center"
                    >
                      Watch on YouTube
                      <ExternalLink className="w-3 h-3 ml-1" />
                    </a>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Comedy Features */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
            <Card className="bg-slate-800/60 border-orange-600/30">
              <CardContent className="p-6 text-center">
                <Laugh className="w-12 h-12 text-orange-400 mx-auto mb-4" />
                <h3 className="text-lg font-bold text-white mb-2">SATIRICAL EDGE</h3>
                <p className="text-slate-300 text-sm">
                  Sharp comedy that doesn't pull punches and isn't afraid to challenge sacred cows.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/60 border-orange-600/30">
              <CardContent className="p-6 text-center">
                <Smile className="w-12 h-12 text-orange-400 mx-auto mb-4" />
                <h3 className="text-lg font-bold text-white mb-2">BRITISH HUMOUR</h3>
                <p className="text-slate-300 text-sm">
                  Comedy that reflects British life with all its contradictions and absurdities.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/60 border-orange-600/30">
              <CardContent className="p-6 text-center">
                <Zap className="w-12 h-12 text-orange-400 mx-auto mb-4" />
                <h3 className="text-lg font-bold text-white mb-2">CUTTING COMMENTARY</h3>
                <p className="text-slate-300 text-sm">
                  Sometimes you have to laugh to keep from crying — comedy as social commentary.
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Call to Action */}
          <div className="text-center">
            <h3 className="text-2xl font-bold text-white mb-4">
              SUBSCRIBE FOR LAUGHS
            </h3>
            <p className="text-slate-300 mb-6 max-w-2xl mx-auto">
              Don't miss our latest satirical takes and comedy sketches. 
              Subscribe for humor that dares to poke fun at the modern circus.
            </p>
            <a 
              href="https://m.youtube.com/@TheCrewkerneGazette" 
              target="_blank" 
              rel="noopener noreferrer"
              className="btn btn-primary"
            >
              <Youtube className="w-5 h-5 mr-2" />
              Subscribe for Comedy
            </a>
          </div>
        </div>
      </section>

      {/* Comedy Articles Grid */}
      <section className="py-16">
        <div className="container">
          {articles.length > 0 && (
            <>
              <div className="section-header">
                <h2 className="section-title">BEHIND THE LAUGHS</h2>
                <p className="section-subtitle">
                  The stories behind our satirical content and comedic commentary on current events
                </p>
              </div>

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
                          SATIRICAL
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
                            Have a Laugh
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
              <Smile className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <h3 className="text-2xl font-semibold text-slate-300 mb-4">
                MORE SATIRICAL CONTENT COMING SOON
              </h3>
              <p className="text-slate-400 mb-6 max-w-2xl mx-auto">
                We're preparing sharp comedy that doesn't pull punches. Comedy that reflects British life 
                with all its contradictions — because sometimes you have to laugh to keep from crying. 
                Watch our sketches above for now.
              </p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default ComedySection;