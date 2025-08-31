import React, { useState } from 'react';
import axios from 'axios';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { Mail, Send, CheckCircle, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_URL = process.env.REACT_APP_API_URL || '/api';
const API = BACKEND_URL || API_URL;

const ContactSection = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    message: ''
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    // CRITICAL: Prevent default form submission that causes page navigation
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    
    console.log('🔄 Form submit event triggered - preventDefault called');
    console.log('📤 REACT_APP_BACKEND_URL:', process.env.REACT_APP_BACKEND_URL);
    console.log('📤 REACT_APP_API_URL:', process.env.REACT_APP_API_URL);
    console.log('📤 Final API URL:', API);
    console.log('📤 Full API endpoint:', `${API}/contacts`);
    console.log('📤 Submitting contact to /api/contacts:', { 
      name: formData.name, 
      email: formData.email, 
      message: formData.message 
    });
    
    // Early exit if already loading to prevent double submission
    if (loading) {
      console.log('⏳ Already loading, ignoring duplicate submission');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess(false);

    try {
      // Validate required fields
      if (!formData.name?.trim() || !formData.email?.trim() || !formData.message?.trim()) {
        console.log('❌ Validation failed: Missing required fields');
        setError('Please fill in all required fields');
        toast.error('Please fill in all required fields');
        return; // Early return - loading will be set to false in finally
      }

      const requestData = {
        name: formData.name.trim(),
        email: formData.email.trim(),
        message: formData.message.trim()
      };
      
      console.log('🌐 Making POST request to:', `${API}/contacts`);
      console.log('📋 Request data:', requestData);
      
      const response = await axios.post(`${API}/contacts`, requestData, {
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 15000 // 15 second timeout
      });
      
      console.log('✅ Contact submission successful:', response.status, response.data);
      
      // Success handling
      setSuccess(true);
      setError(''); // Clear any previous errors
      setFormData({ name: '', email: '', message: '' });
      
      // Success notification
      try {
        toast.success('Message sent! We\'ll get back to you soon.');
      } catch (toastError) {
        console.error('❌ Toast success error:', toastError);
        alert('Message sent successfully!');
      }
      
    } catch (error) {
      console.error('❌ Contact submission failed:', error);
      console.error('❌ Error type:', typeof error);
      console.error('❌ Error stack:', error.stack);
      console.error('❌ Error details:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        message: error.message,
        name: error.name,
        code: error.code
      });
      
      // Error handling
      let errorMessage = 'Failed to send message. Please try again.';
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.code === 'NETWORK_ERROR' || error.message.includes('Network Error')) {
        errorMessage = 'Network error. Please check your connection and try again.';
      } else if (error.code === 'TIMEOUT' || error.message.includes('timeout')) {
        errorMessage = 'Request timed out. Please try again.';
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setError(errorMessage);
      setSuccess(false); // Ensure success is false on error
      
      // Error notification
      try {
        toast.error(errorMessage);
      } catch (toastError) {
        console.error('❌ Toast error:', toastError);
        alert(`Error: ${errorMessage}`);
      }
      
    } finally {
      // CRITICAL: Always reset loading state to prevent stuck blue screen
      console.log('🔄 Resetting loading state');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 relative">
      {/* Loading Overlay - Prevents blue screen */}
      {loading && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 p-6 rounded-lg shadow-xl text-white">
            <div className="flex items-center space-x-3">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-red-600"></div>
              <span>Sending your message...</span>
            </div>
          </div>
        </div>
      )}
      {/* Header */}
      <section 
        className="relative py-24 bg-cover bg-center"
        style={{
          backgroundImage: `linear-gradient(135deg, rgba(17, 24, 39, 0.9), rgba(31, 41, 55, 0.8)), 
                           url('https://images.unsplash.com/photo-1423666639041-f56000c27a9a')`
        }}
      >
        <div className="container">
          <div className="text-center">
            <h1 className="text-5xl font-bold text-white mb-6 uppercase tracking-wider">
              GET IN TOUCH
            </h1>
            <p className="text-xl text-slate-300 max-w-2xl mx-auto">
              Have a story tip? Want to collaborate? Questions about our content? 
              We want to hear from you. Your voice matters in our mission for truth.
            </p>
          </div>
        </div>
      </section>

      {/* Contact Form */}
      <section className="py-16">
        <div className="container">
          <div className="max-w-2xl mx-auto">
            <Card className="bg-slate-800/80 border-red-600/30">
              <CardHeader className="text-center">
                <CardTitle className="text-2xl text-white flex items-center justify-center">
                  <Mail className="w-6 h-6 mr-3 text-red-400" />
                  CONTACT THE GAZETTE
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Send us your inquiries, tips, or feedback. All messages go directly to our editorial team.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-6">
                {success && (
                  <Alert className="mb-6 bg-green-900/20 border-green-600">
                    <CheckCircle className="h-4 w-4 text-green-400" />
                    <AlertDescription className="text-green-300">
                      Thank you for your message! We've received your inquiry and will respond within 24 hours.
                    </AlertDescription>
                  </Alert>
                )}

                {error && (
                  <Alert variant="destructive" className="mb-6 bg-red-900/20 border-red-600">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <form onSubmit={handleSubmit} className="space-y-6" noValidate>
                  <div className="space-y-2">
                    <Label htmlFor="name" className="text-slate-200 font-semibold">
                      Your Name
                    </Label>
                    <Input
                      id="name"
                      name="name"
                      type="text"
                      value={formData.name}
                      onChange={handleChange}
                      placeholder="Your full name"
                      className="bg-slate-700/50 border-slate-600 text-white placeholder-slate-500 focus:border-red-600"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="email" className="text-slate-200 font-semibold">
                      Your Email Address
                    </Label>
                    <Input
                      id="email"
                      name="email"
                      type="email"
                      value={formData.email}
                      onChange={handleChange}
                      placeholder="yourname@example.com"
                      className="bg-slate-700/50 border-slate-600 text-white placeholder-slate-500 focus:border-red-600"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="message" className="text-slate-200 font-semibold">
                      Your Message
                    </Label>
                    <Textarea
                      id="message"
                      name="message"
                      value={formData.message}
                      onChange={handleChange}
                      placeholder="Tell us what's on your mind..."
                      className="bg-slate-700/50 border-slate-600 text-white placeholder-slate-500 focus:border-red-600 min-h-[150px] resize-none"
                      required
                    />
                    <p className="text-xs text-slate-500">
                      Share your story tips, feedback, collaboration ideas, or any questions you have about our content.
                    </p>
                  </div>

                  <Button 
                    type="submit" 
                    className="w-full bg-red-700 hover:bg-red-800 text-white font-bold py-3 text-lg border-0"
                    disabled={loading}
                    onClick={(e) => {
                      console.log('🔘 Button clicked');
                      if (loading) {
                        e.preventDefault();
                        e.stopPropagation();
                        console.log('⏳ Button click blocked - already loading');
                      }
                    }}
                  >
                    {loading ? (
                      'SENDING MESSAGE...'
                    ) : (
                      <>
                        <Send className="w-5 h-5 mr-2" />
                        SEND MESSAGE
                      </>
                    )}
                  </Button>
                </form>

                <div className="mt-8 p-4 bg-slate-700/30 rounded-lg">
                  <h3 className="text-white font-bold mb-2">Other Ways to Reach Us</h3>
                  <div className="space-y-2 text-sm text-slate-300">
                    <p>
                      <strong>Email:</strong> CrewkerneGazette@gmail.com
                    </p>
                    <p>
                      <strong>Location:</strong> Crewkerne, UK
                    </p>
                    <p>
                      <strong>Response Time:</strong> We typically respond within 24 hours
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Contact Info Cards */}
      <section className="py-16 bg-slate-800/50">
        <div className="container">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <Card className="bg-slate-800/60 border-red-600/30">
              <CardContent className="p-6 text-center">
                <Mail className="w-12 h-12 text-red-400 mx-auto mb-4" />
                <h3 className="text-lg font-bold text-white mb-2">STORY TIPS</h3>
                <p className="text-slate-300 text-sm">
                  Got a breaking story or investigation tip? Send it our way - we protect our sources.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/60 border-red-600/30">
              <CardContent className="p-6 text-center">
                <Send className="w-12 h-12 text-red-400 mx-auto mb-4" />
                <h3 className="text-lg font-bold text-white mb-2">COLLABORATIONS</h3>
                <p className="text-slate-300 text-sm">
                  Interested in working with us? Let's discuss how we can amplify important stories together.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/60 border-red-600/30">
              <CardContent className="p-6 text-center">
                <CheckCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                <h3 className="text-lg font-bold text-white mb-2">FEEDBACK</h3>
                <p className="text-slate-300 text-sm">
                  Your feedback helps us improve. Tell us what you think about our coverage and content.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>
    </div>
  );
};

export default ContactSection;