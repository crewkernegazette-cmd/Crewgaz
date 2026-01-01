import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ChevronDown, ChevronUp, Calendar, ArrowLeft, Trophy, ThumbsUp, ThumbsDown, Flame } from 'lucide-react';
import { apiClient } from '../config/api';

const TrendingOpinionsPage = () => {
  const [topOpinions, setTopOpinions] = useState([]);
  const [archive, setArchive] = useState({});
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [expandedMonths, setExpandedMonths] = useState({});
  const [selectedImage, setSelectedImage] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      // Fetch top opinions and archive in parallel
      const [topResponse, archiveResponse] = await Promise.all([
        apiClient.get('/opinions/top?limit=20'),
        apiClient.get('/opinions/archive')
      ]);
      
      setTopOpinions(topResponse.data.opinions || []);
      setArchive(archiveResponse.data.archive || {});
      setTotalCount(archiveResponse.data.total_count || 0);
      
      // Expand the first month by default
      const months = Object.keys(archiveResponse.data.archive || {});
      if (months.length > 0) {
        setExpandedMonths({ [months[0]]: true });
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      setTopOpinions([]);
      setArchive({});
    } finally {
      setLoading(false);
    }
  };

  const toggleMonth = (monthKey) => {
    setExpandedMonths(prev => ({
      ...prev,
      [monthKey]: !prev[monthKey]
    }));
  };

  const openLightbox = (imageUrl) => {
    setSelectedImage(imageUrl);
  };

  const closeLightbox = () => {
    setSelectedImage(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 py-12">
        <div className="container mx-auto px-4">
          <div className="text-center text-white text-xl">
            <div className="animate-spin text-4xl mb-4">🔄</div>
            Loading the archives of outrage...
          </div>
        </div>
      </div>
    );
  }

  const monthKeys = Object.keys(archive).sort().reverse();

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 py-12">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-12">
          <Link
            to="/"
            className="inline-flex items-center text-slate-400 hover:text-white mb-6 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Homepage
          </Link>
          
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            📮 TRENDING OPINIONS ARCHIVE 📮
          </h1>
          <p className="text-xl text-slate-400 mb-2">
            A permanent record of everyone&apos;s hot takes
          </p>
          <p className="text-sm text-slate-500 italic">
            &quot;The internet never forgets... neither do we&quot; 🗄️
          </p>
          
          <div className="mt-6 inline-flex items-center bg-slate-700/50 px-6 py-3 rounded-full">
            <span className="text-2xl mr-2">📊</span>
            <span className="text-white font-bold">{totalCount}</span>
            <span className="text-slate-400 ml-2">opinions and counting</span>
          </div>
        </div>

        {/* Top Trending Opinions Section */}
        {topOpinions.length > 0 && (
          <div className="mb-12">
            <div className="flex items-center justify-center mb-6">
              <Trophy className="w-8 h-8 text-yellow-500 mr-3" />
              <h2 className="text-3xl font-bold text-white">TOP TRENDING OPINIONS</h2>
              <Flame className="w-8 h-8 text-orange-500 ml-3 animate-pulse" />
            </div>
            <p className="text-center text-slate-400 mb-8">
              The hottest takes ranked by community votes 🔥
            </p>
            
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
              {topOpinions.map((opinion, index) => (
                <Link
                  key={opinion.id}
                  to={`/opinion/${opinion.id}`}
                  className="relative group cursor-pointer overflow-hidden rounded-xl aspect-square bg-slate-700 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105"
                >
                  {/* Rank Badge */}
                  <div className={`absolute top-2 left-2 z-10 w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                    index === 0 ? 'bg-yellow-500 text-black' :
                    index === 1 ? 'bg-slate-300 text-black' :
                    index === 2 ? 'bg-orange-600 text-white' :
                    'bg-slate-600 text-white'
                  }`}>
                    {index + 1}
                  </div>
                  
                  {/* Vote Badge */}
                  <div className="absolute top-2 right-2 z-10 bg-black/70 px-2 py-1 rounded-full flex items-center gap-1">
                    <ThumbsUp className="w-3 h-3 text-green-400" />
                    <span className="text-xs text-white font-medium">
                      {opinion.net_votes > 0 ? '+' : ''}{opinion.net_votes}
                    </span>
                  </div>
                  
                  <img
                    src={opinion.image_url}
                    alt={`Top Opinion #${index + 1}`}
                    className="w-full h-full object-cover"
                    loading="lazy"
                  />
                  
                  <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  
                  <div className="absolute bottom-0 left-0 right-0 p-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    <div className="flex items-center justify-between text-white text-xs">
                      <span className="flex items-center gap-1">
                        <ThumbsUp className="w-3 h-3 text-green-400" />
                        {opinion.upvotes}
                      </span>
                      <span className="flex items-center gap-1">
                        <ThumbsDown className="w-3 h-3 text-red-400" />
                        {opinion.downvotes}
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Divider */}
        {topOpinions.length > 0 && monthKeys.length > 0 && (
          <div className="flex items-center my-12">
            <div className="flex-1 border-t border-slate-700"></div>
            <div className="px-6 text-slate-500 text-sm">BROWSE BY DATE</div>
            <div className="flex-1 border-t border-slate-700"></div>
          </div>
        )}

        {/* Archive Content */}
        {monthKeys.length > 0 ? (
          <div className="max-w-6xl mx-auto space-y-6">
            {monthKeys.map((monthKey) => {
              const monthData = archive[monthKey];
              const isExpanded = expandedMonths[monthKey];
              const dayKeys = Object.keys(monthData.days).sort().reverse();
              
              return (
                <div
                  key={monthKey}
                  className="bg-slate-800/50 rounded-xl overflow-hidden border border-slate-700"
                >
                  {/* Month Header */}
                  <button
                    onClick={() => toggleMonth(monthKey)}
                    className="w-full flex items-center justify-between p-6 text-left hover:bg-slate-700/30 transition-colors"
                  >
                    <div className="flex items-center">
                      <Calendar className="w-6 h-6 text-red-500 mr-3" />
                      <h2 className="text-2xl font-bold text-white">
                        {monthData.month_name}
                      </h2>
                      <span className="ml-4 bg-red-600/20 text-red-400 px-3 py-1 rounded-full text-sm">
                        {Object.values(monthData.days).reduce((acc, day) => acc + day.opinions.length, 0)} opinions
                      </span>
                    </div>
                    {isExpanded ? (
                      <ChevronUp className="w-6 h-6 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-6 h-6 text-slate-400" />
                    )}
                  </button>

                  {/* Month Content */}
                  {isExpanded && (
                    <div className="px-6 pb-6 space-y-6">
                      {dayKeys.map((dayKey) => {
                        const dayData = monthData.days[dayKey];
                        
                        return (
                          <div key={dayKey} className="border-t border-slate-700 pt-6">
                            {/* Day Header */}
                            <h3 className="text-lg font-semibold text-slate-300 mb-4 flex items-center">
                              <span className="text-xl mr-2">📅</span>
                              {dayData.day_name}
                              <span className="ml-3 text-sm text-slate-500">
                                ({dayData.opinions.length} {dayData.opinions.length === 1 ? 'opinion' : 'opinions'})
                              </span>
                            </h3>
                            
                            {/* Day's Opinions Grid */}
                            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
                              {dayData.opinions.map((opinion) => (
                                <Link
                                  key={opinion.id}
                                  to={`/opinion/${opinion.id}`}
                                  className="relative group cursor-pointer overflow-hidden rounded-lg aspect-square bg-slate-700 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105"
                                >
                                  {/* Vote indicator */}
                                  <div className="absolute top-1 right-1 z-10 bg-black/60 px-2 py-0.5 rounded-full flex items-center gap-1">
                                    <span className={`text-xs font-medium ${opinion.net_votes >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                      {opinion.net_votes > 0 ? '+' : ''}{opinion.net_votes}
                                    </span>
                                  </div>
                                  
                                  <img
                                    src={opinion.image_url}
                                    alt="Reader Opinion"
                                    className="w-full h-full object-cover"
                                    loading="lazy"
                                  />
                                  <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
                                    <span className="text-white text-sm font-medium">View & Vote</span>
                                  </div>
                                </Link>
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : topOpinions.length === 0 ? (
          <div className="text-center py-16">
            <div className="text-6xl mb-4">🦗</div>
            <h2 className="text-2xl font-bold text-white mb-2">
              No opinions yet!
            </h2>
            <p className="text-slate-400 mb-6">
              The archive is empty... for now. Check back soon for the good stuff!
            </p>
            <Link
              to="/"
              className="inline-flex items-center px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Homepage
            </Link>
          </div>
        ) : null}

        {/* Footer fun message */}
        {totalCount > 0 && (
          <div className="text-center mt-12 text-slate-500 text-sm">
            <p>🎭 Remember: These opinions do not reflect the views of The Crewkerne Gazette</p>
            <p className="mt-1 italic">(Except when they&apos;re really funny)</p>
          </div>
        )}
      </div>

      {/* Lightbox Modal */}
      {selectedImage && (
        <div
          className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4"
          onClick={closeLightbox}
        >
          <div className="relative max-w-4xl max-h-[90vh] w-full">
            <button
              onClick={closeLightbox}
              className="absolute -top-12 right-0 text-white text-4xl hover:text-red-500 transition-colors"
            >
              ✕
            </button>
            <img
              src={selectedImage}
              alt="Opinion Full View"
              className="w-full h-full object-contain rounded-lg"
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default TrendingOpinionsPage;
