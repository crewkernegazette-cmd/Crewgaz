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
const API = BACKEND_URL;

const ContactSection = () => {
  const [formData, setFormData] = useState({
    email: '',
    inquiry: ''
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
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess(false);

    try {
      await axios.post(`${API}/contact`, formData);
      setSuccess(true);
      setFormData({ email: '', inquiry: '' });
      toast.success('Message sent successfully! We\'ll get back to you soon.');
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to send message. Please try again.';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800">
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

                <form onSubmit={handleSubmit} className="space-y-6">
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
                    <Label htmlFor="inquiry" className="text-slate-200 font-semibold">
                      Your Message
                    </Label>
                    <Textarea
                      id="inquiry"
                      name="inquiry"
                      value={formData.inquiry}
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