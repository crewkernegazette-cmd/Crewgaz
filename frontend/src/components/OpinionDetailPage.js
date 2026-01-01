import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ThumbsUp, ThumbsDown, MessageCircle, ChevronLeft, ChevronRight, ArrowLeft, Send, X } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { toast } from 'sonner';
import { apiClient } from '../config/api';

const OpinionDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [opinion, setOpinion] = useState(null);
  const [comments, setComments] = useState([]);
  const [prevId, setPrevId] = useState(null);
  const [nextId, setNextId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [userVote, setUserVote] = useState(null);
  const [commentVotes, setCommentVotes] = useState({});
  const [newComment, setNewComment] = useState('');
  const [submittingComment, setSubmittingComment] = useState(false);
  
  // User state
  const [user, setUser] = useState(null);
  const [showRegister, setShowRegister] = useState(false);
  const [registerUsername, setRegisterUsername] = useState('');
  const [registering, setRegistering] = useState(false);

  // Touch/swipe handling
  const touchStartX = useRef(0);
  const touchEndX = useRef(0);
  const containerRef = useRef(null);

  // Load user from localStorage
  useEffect(() => {
    const sessionToken = localStorage.getItem('opinion_session_token');
    const username = localStorage.getItem('opinion_username');
    if (sessionToken && username) {
      setUser({ username, sessionToken });
    }
  }, []);

  const fetchOpinion = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiClient.get(`/opinions/${id}`);
      setOpinion(response.data.opinion);
      setPrevId(response.data.prev_id);
      setNextId(response.data.next_id);
      
      // Fetch user's vote if logged in
      const sessionToken = localStorage.getItem('opinion_session_token');
      if (sessionToken) {
        const voteResponse = await apiClient.get(`/opinions/${id}/user-vote?session_token=${sessionToken}`);
        setUserVote(voteResponse.data.user_vote);
      }
    } catch (error) {
      console.error('Error fetching opinion:', error);
      toast.error('Failed to load opinion');
    } finally {
      setLoading(false);
    }
  }, [id]);

  const fetchComments = useCallback(async () => {
    try {
      const response = await apiClient.get(`/opinions/${id}/comments`);
      setComments(response.data.comments || []);
      
      // Fetch user votes on comments if logged in
      const sessionToken = localStorage.getItem('opinion_session_token');
      if (sessionToken && response.data.comments) {
        const votes = {};
        for (const comment of response.data.comments) {
          try {
            const voteRes = await apiClient.get(`/comments/${comment.id}/user-vote?session_token=${sessionToken}`);
            votes[comment.id] = voteRes.data.user_vote;
          } catch (e) {
            // Ignore individual vote fetch errors
          }
        }
        setCommentVotes(votes);
      }
    } catch (error) {
      console.error('Error fetching comments:', error);
    }
  }, [id]);

  useEffect(() => {
    fetchOpinion();
    fetchComments();
  }, [fetchOpinion, fetchComments]);

  // Swipe handlers
  const handleTouchStart = (e) => {
    touchStartX.current = e.touches[0].clientX;
  };

  const handleTouchMove = (e) => {
    touchEndX.current = e.touches[0].clientX;
  };

  const handleTouchEnd = () => {
    const diff = touchStartX.current - touchEndX.current;
    const minSwipeDistance = 50;

    if (Math.abs(diff) > minSwipeDistance) {
      if (diff > 0 && nextId) {
        // Swipe left - go to next
        navigate(`/opinion/${nextId}`);
      } else if (diff < 0 && prevId) {
        // Swipe right - go to previous
        navigate(`/opinion/${prevId}`);
      }
    }
  };

  // Register user
  const handleRegister = async (e) => {
    e.preventDefault();
    if (!registerUsername.trim()) {
      toast.error('Please enter a username');
      return;
    }

    setRegistering(true);
    try {
      const formData = new FormData();
      formData.append('username', registerUsername.trim());
      
      const response = await apiClient.post('/opinion-users/register', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      if (response.data.ok) {
        localStorage.setItem('opinion_session_token', response.data.user.session_token);
        localStorage.setItem('opinion_username', response.data.user.username);
        setUser({
          username: response.data.user.username,
          sessionToken: response.data.user.session_token
        });
        setShowRegister(false);
        setRegisterUsername('');
        toast.success(`Welcome, ${response.data.user.username}!`);
      } else {
        toast.error('Registration failed. Please try again.');
      }
    } catch (error) {
      console.error('Registration error:', error);
      const errorMessage = error.response?.data?.detail || 'Registration failed. Username may be taken.';
      toast.error(errorMessage);
    } finally {
      setRegistering(false);
    }
  };
      toast.error(error.response?.data?.detail || 'Registration failed. Username may be taken.');
    } finally {
      setRegistering(false);
    }
  };

  // Vote on opinion
  const handleVote = async (voteType) => {
    if (!user) {
      setShowRegister(true);
      return;
    }

    try {
      const formData = new FormData();
      formData.append('vote_type', voteType);
      formData.append('session_token', user.sessionToken);
      
      const response = await apiClient.post(`/opinions/${id}/vote`, formData);
      
      if (response.data.ok) {
        setOpinion(prev => ({
          ...prev,
          upvotes: response.data.upvotes,
          downvotes: response.data.downvotes
        }));
        setUserVote(response.data.user_vote);
      }
    } catch (error) {
      console.error('Vote error:', error);
      toast.error(error.response?.data?.detail || 'Failed to vote');
    }
  };

  // Vote on comment
  const handleCommentVote = async (commentId, voteType) => {
    if (!user) {
      setShowRegister(true);
      return;
    }

    try {
      const formData = new FormData();
      formData.append('vote_type', voteType);
      formData.append('session_token', user.sessionToken);
      
      const response = await apiClient.post(`/comments/${commentId}/vote`, formData);
      
      if (response.data.ok) {
        setComments(prev => prev.map(c => 
          c.id === commentId 
            ? { ...c, upvotes: response.data.upvotes, downvotes: response.data.downvotes }
            : c
        ).sort((a, b) => (b.upvotes - b.downvotes) - (a.upvotes - a.downvotes)));
        setCommentVotes(prev => ({ ...prev, [commentId]: response.data.user_vote }));
      }
    } catch (error) {
      console.error('Comment vote error:', error);
      toast.error(error.response?.data?.detail || 'Failed to vote');
    }
  };

  // Add comment
  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!user) {
      setShowRegister(true);
      return;
    }
    if (!newComment.trim()) {
      toast.error('Please enter a comment');
      return;
    }

    setSubmittingComment(true);
    try {
      const formData = new FormData();
      formData.append('content', newComment.trim());
      formData.append('session_token', user.sessionToken);
      
      const response = await apiClient.post(`/opinions/${id}/comments`, formData);
      
      if (response.data.ok) {
        setComments(prev => [response.data.comment, ...prev]);
        setNewComment('');
        toast.success('Comment added!');
      }
    } catch (error) {
      console.error('Add comment error:', error);
      toast.error(error.response?.data?.detail || 'Failed to add comment');
    } finally {
      setSubmittingComment(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 flex items-center justify-center">
        <div className="text-white text-xl animate-pulse">Loading opinion...</div>
      </div>
    );
  }

  if (!opinion) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 flex flex-col items-center justify-center">
        <div className="text-white text-xl mb-4">Opinion not found</div>
        <Link to="/trending-opinions" className="text-red-400 hover:text-red-300">
          Back to Archive
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <div className="bg-slate-800/50 border-b border-slate-700">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link
              to="/trending-opinions"
              className="flex items-center text-slate-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back to Archive
            </Link>
            {user ? (
              <div className="text-sm text-slate-400">
                Logged in as <span className="text-red-400 font-medium">{user.username}</span>
              </div>
            ) : (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowRegister(true)}
                className="border-red-600 text-red-400 hover:bg-red-600 hover:text-white"
              >
                Register to Vote
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div 
        ref={containerRef}
        className="container mx-auto px-4 py-8"
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        <div className="max-w-4xl mx-auto">
          {/* Opinion Image with Navigation */}
          <div className="relative mb-6">
            {/* Navigation Arrows */}
            {prevId && (
              <button
                onClick={() => navigate(`/opinion/${prevId}`)}
                className="absolute left-2 top-1/2 -translate-y-1/2 z-10 bg-black/50 hover:bg-black/70 text-white p-3 rounded-full transition-all"
              >
                <ChevronLeft className="w-8 h-8" />
              </button>
            )}
            {nextId && (
              <button
                onClick={() => navigate(`/opinion/${nextId}`)}
                className="absolute right-2 top-1/2 -translate-y-1/2 z-10 bg-black/50 hover:bg-black/70 text-white p-3 rounded-full transition-all"
              >
                <ChevronRight className="w-8 h-8" />
              </button>
            )}

            {/* Image */}
            <div className="bg-slate-800 rounded-xl overflow-hidden shadow-2xl">
              <img
                src={opinion.image_url}
                alt="Trending Opinion"
                className="w-full max-h-[70vh] object-contain"
              />
            </div>

            {/* Swipe hint */}
            <p className="text-center text-slate-500 text-sm mt-2">
              👆 Swipe left or right for more opinions
            </p>
          </div>

          {/* Vote Section */}
          <div className="bg-slate-800/50 rounded-xl p-6 mb-6 border border-slate-700">
            <div className="flex items-center justify-center gap-8">
              <button
                onClick={() => handleVote('up')}
                className={`flex flex-col items-center gap-2 p-4 rounded-xl transition-all ${
                  userVote === 'up' 
                    ? 'bg-green-600/20 text-green-400 border border-green-600' 
                    : 'bg-slate-700/50 text-slate-300 hover:bg-green-600/10 hover:text-green-400'
                }`}
              >
                <ThumbsUp className={`w-10 h-10 ${userVote === 'up' ? 'fill-current' : ''}`} />
                <span className="text-2xl font-bold">{opinion.upvotes}</span>
              </button>
              
              <div className="text-center">
                <div className="text-4xl font-bold text-white">
                  {opinion.upvotes - opinion.downvotes > 0 ? '+' : ''}{opinion.upvotes - opinion.downvotes}
                </div>
                <div className="text-sm text-slate-500">Net Score</div>
              </div>
              
              <button
                onClick={() => handleVote('down')}
                className={`flex flex-col items-center gap-2 p-4 rounded-xl transition-all ${
                  userVote === 'down' 
                    ? 'bg-red-600/20 text-red-400 border border-red-600' 
                    : 'bg-slate-700/50 text-slate-300 hover:bg-red-600/10 hover:text-red-400'
                }`}
              >
                <ThumbsDown className={`w-10 h-10 ${userVote === 'down' ? 'fill-current' : ''}`} />
                <span className="text-2xl font-bold">{opinion.downvotes}</span>
              </button>
            </div>
          </div>

          {/* Comments Section */}
          <div className="bg-slate-800/50 rounded-xl border border-slate-700">
            <div className="p-6 border-b border-slate-700">
              <h3 className="text-xl font-bold text-white flex items-center">
                <MessageCircle className="w-5 h-5 mr-2" />
                Comments ({comments.length})
              </h3>
            </div>

            {/* Add Comment Form */}
            <form onSubmit={handleAddComment} className="p-6 border-b border-slate-700">
              <Textarea
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder={user ? "Share your thoughts..." : "Register to comment"}
                className="bg-slate-700/50 border-slate-600 text-white mb-3 min-h-[100px]"
                disabled={!user}
              />
              <Button
                type="submit"
                disabled={!user || submittingComment || !newComment.trim()}
                className="bg-red-600 hover:bg-red-700 text-white"
              >
                {submittingComment ? (
                  'Posting...'
                ) : (
                  <>
                    <Send className="w-4 h-4 mr-2" />
                    Post Comment
                  </>
                )}
              </Button>
            </form>

            {/* Comments List */}
            <div className="divide-y divide-slate-700">
              {comments.length > 0 ? (
                comments.map((comment) => (
                  <div key={comment.id} className="p-6">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <span className="font-semibold text-red-400">{comment.username}</span>
                        <span className="text-slate-500 text-sm ml-2">
                          {comment.created_at && new Date(comment.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleCommentVote(comment.id, 'up')}
                          className={`p-1 rounded ${
                            commentVotes[comment.id] === 'up' 
                              ? 'text-green-400' 
                              : 'text-slate-400 hover:text-green-400'
                          }`}
                        >
                          <ThumbsUp className={`w-4 h-4 ${commentVotes[comment.id] === 'up' ? 'fill-current' : ''}`} />
                        </button>
                        <span className="text-sm font-medium text-slate-300">
                          {comment.upvotes - comment.downvotes}
                        </span>
                        <button
                          onClick={() => handleCommentVote(comment.id, 'down')}
                          className={`p-1 rounded ${
                            commentVotes[comment.id] === 'down' 
                              ? 'text-red-400' 
                              : 'text-slate-400 hover:text-red-400'
                          }`}
                        >
                          <ThumbsDown className={`w-4 h-4 ${commentVotes[comment.id] === 'down' ? 'fill-current' : ''}`} />
                        </button>
                      </div>
                    </div>
                    <p className="text-slate-300">{comment.content}</p>
                  </div>
                ))
              ) : (
                <div className="p-12 text-center">
                  <MessageCircle className="w-12 h-12 mx-auto text-slate-600 mb-4" />
                  <p className="text-slate-400">No comments yet. Be the first to share your thoughts!</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Registration Modal */}
      {showRegister && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
          <div className="bg-slate-800 rounded-xl p-6 w-full max-w-md border border-slate-700">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-white">Create Username</h3>
              <button
                onClick={() => setShowRegister(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            <form onSubmit={handleRegister}>
              <p className="text-slate-400 mb-4">
                Choose a username to vote and comment on opinions.
              </p>
              <Input
                value={registerUsername}
                onChange={(e) => setRegisterUsername(e.target.value)}
                placeholder="Enter username"
                className="bg-slate-700/50 border-slate-600 text-white mb-4"
                maxLength={50}
              />
              <Button
                type="submit"
                disabled={registering || !registerUsername.trim()}
                className="w-full bg-red-600 hover:bg-red-700 text-white"
              >
                {registering ? 'Creating...' : 'Create Account'}
              </Button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default OpinionDetailPage;
