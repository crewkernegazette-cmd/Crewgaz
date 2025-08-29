import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Clock, Play, Music as MusicIcon, ExternalLink, Youtube, Music2, Users } from 'lucide-react';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MusicSection = () => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  // Your actual music videos
  const musicVideos = [
    { id: 'kmNjVV1RzfU', title: 'Music Video 1' },
    { id: 'dFyVT8DKisU', title: 'Music Video 2' },
    { id: 'J23QKOvnyuc', title: 'Music Video 3' },
    { id: 'r4Uxpb15dYI', title: 'Music Video 4' },
    { id: '3OPnLmM1gUg', title: 'Music Video 5' },
    { id: '_QSSSi1uS4Y', title: 'Music Video 6' }
  ];

  useEffect(() => {
    fetchMusic();
  }, []);

  const fetchMusic = async () => {
    try {
      const response = await axios.get(`${API}/articles?category=music&limit=12`);
      setArticles(response.data);
    } catch (error) {
      console.error('Error fetching music:', error);
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
                           url('https://images.unsplash.com/photo-1598488035139-bdbb2231ce04')`
        }}
      >
        <div className="container">
          <div className="text-center">
            <h1 className="text-5xl font-bold text-white mb-6 uppercase tracking-wider">
              RAW & AUTHENTIC MUSIC
            </h1>
            <p className="text-xl text-slate-300 max-w-3xl mx-auto mb-8">
              A stage for the sounds and culture that reflect the people — raw, energetic, and authentic. 
              Music that moves culture and changes minds, proudly from Somerset.
            </p>
            
            {/* Platform Links */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a 
                href="https://open.spotify.com/artist/6iwYn8mBLB97HM21KSHsMa" 
                target="_blank" 
                rel="noopener noreferrer"
                className="btn btn-primary"
              >
                <Music2 className="w-5 h-5 mr-2" />
                Listen on Spotify
                <ExternalLink className="w-4 h-4 ml-2" />
              </a>
              <a 
                href="https://m.youtube.com/@TheCrewkerneGazette" 
                target="_blank" 
                rel="noopener noreferrer"
                className="btn btn-secondary"
              >
                <Youtube className="w-5 h-5 mr-2" />
                Watch on YouTube
                <ExternalLink className="w-4 h-4 ml-2" />
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Music Videos Section */}
      <section className="py-16 bg-slate-800/50">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">OUR MUSIC VIDEOS</h2>
            <p className="section-subtitle">
              Watch our latest tracks and performances — culture that celebrates British life
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-12">
            {musicVideos.map((video, index) => (
              <Card key={video.id} className="bg-slate-800/80 border-red-600/30">
                <CardContent className="p-6">
                  <div className="aspect-video bg-slate-900 rounded-lg overflow-hidden mb-4">
                    <iframe 
                      src={`https://www.youtube.com/embed/${video.id}`}
                      width="100%" 
                      height="100%" 
                      frameBorder="0" 
                      allowFullScreen
                      className="rounded-lg"
                      title={`The Crewkerne Gazette Music Video ${index + 1}`}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Badge className="category-badge category-music">
                      TRACK {index + 1}
                    </Badge>
                    <a 
                      href={`https://youtu.be/${video.id}`}
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-red-400 hover:text-red-300 text-sm flex items-center"
                    >
                      Watch on YouTube
                      <ExternalLink className="w-3 h-3 ml-1" />
                    </a>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Spotify Player */}
          <div className="max-w-4xl mx-auto mb-12">
            <Card className="bg-slate-800/80 border-red-600/30">
              <CardContent className="p-6">
                <div className="flex items-center mb-4">
                  <Music2 className="w-6 h-6 text-green-400 mr-3" />
                  <h3 className="text-xl font-bold text-white">Stream Our Complete Catalog</h3>
                </div>
                <div className="aspect-video bg-slate-900 rounded-lg overflow-hidden">
                  <iframe 
                    src="https://open.spotify.com/embed/artist/6iwYn8mBLB97HM21KSHsMa?utm_source=generator&theme=0" 
                    width="100%" 
                    height="100%" 
                    frameBorder="0" 
                    allowFullScreen 
                    allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" 
                    loading="lazy"
                    className="rounded-lg"
                  />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Call to Action */}
          <div className="text-center">
            <h3 className="text-2xl font-bold text-white mb-4">
              JOIN THE SOUND REVOLUTION
            </h3>
            <p className="text-slate-300 mb-6 max-w-2xl mx-auto">
              Follow us for music that doesn't compromise, doesn't conform, and doesn't apologize. 
              This is culture as it should be — alive, authentic, and unapologetically British.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a 
                href="https://open.spotify.com/artist/6iwYn8mBLB97HM21KSHsMa" 
                target="_blank" 
                rel="noopener noreferrer"
                className="btn btn-primary"
              >
                <Users className="w-5 h-5 mr-2" />
                Follow on Spotify
              </a>
              <a 
                href="https://m.youtube.com/@TheCrewkerneGazette" 
                target="_blank" 
                rel="noopener noreferrer"
                className="btn btn-secondary"
              >
                <Users className="w-5 h-5 mr-2" />
                Subscribe on YouTube
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Music Articles Grid */}
      <section className="py-16">
        <div className="container">
          {articles.length > 0 && (
            <>
              <div className="section-header">
                <h2 className="section-title">BEHIND THE MUSIC</h2>
                <p className="section-subtitle">
                  Stories from the studio, insights into our creative process, and the cultural commentary behind the sound
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
                        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                          <Button size="sm" className="bg-purple-600 hover:bg-purple-700">
                            <Play className="w-4 h-4 mr-2" />
                            Read
                          </Button>
                        </div>
                      </div>
                    )}
                    <div className="article-content">
                      <div className="flex items-center justify-between mb-3">
                        <Badge className="category-badge category-music">
                          AUTHENTIC
                        </Badge>
                      </div>
                      <h3 className="article-title group-hover:text-purple-400 transition-colors">
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
                          <Button variant="outline" size="sm" className="w-full border-purple-400 text-purple-400 hover:bg-purple-400 hover:text-white">
                            Read More
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
              <MusicIcon className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <h3 className="text-2xl font-semibold text-slate-300 mb-4">
                MORE MUSICAL CONTENT COMING SOON
              </h3>
              <p className="text-slate-400 mb-6 max-w-2xl mx-auto">
                We're creating content about our musical journey, the stories behind the songs, 
                and the culture that shapes authentic British sound. In the meantime, dive into our tracks above.
              </p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default MusicSection;