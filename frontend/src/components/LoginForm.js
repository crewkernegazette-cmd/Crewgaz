import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../App';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Alert, AlertDescription } from './ui/alert';
import { User, Lock, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

const LoginForm = () => {
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
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

    console.log('Form submitted with:', { username: formData.username });
    
    const result = await login(formData);
    
    if (result.success) {
      toast.success('Login successful');
      navigate('/dashboard');
    } else {
      console.error('Login failed:', result.error);
      setError(result.error);
      toast.error('Invalid credentials');
    }
    
    setLoading(false);
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="text-center mb-8">
          {/* Logo */}
          <div className="gazette-logo-circle mx-auto mb-6"></div>
          <h1 className="login-title">
            Content Management
          </h1>
          <p className="text-slate-400 text-sm">
            Sign in to manage The Crewkerne Gazette
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <Alert variant="destructive" className="bg-red-900/20 border-red-600">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="space-y-2">
            <Label htmlFor="username" className="text-slate-200 font-semibold">
              Username
            </Label>
            <div className="relative">
              <User className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
              <Input
                id="username"
                name="username"
                type="text"
                value={formData.username}
                onChange={handleChange}
                placeholder="Enter username"
                className="pl-10 bg-slate-800/50 border-slate-600 text-white placeholder-slate-500 focus:border-red-600"
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="password" className="text-slate-200 font-semibold">
              Password
            </Label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
              <Input
                id="password"
                name="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Enter password"
                className="pl-10 bg-slate-800/50 border-slate-600 text-white placeholder-slate-500 focus:border-red-600"
                required
              />
            </div>
          </div>

          <Button 
            type="submit" 
            className="w-full bg-red-700 hover:bg-red-800 text-white font-bold py-3 text-lg border-0"
            disabled={loading}
          >
            {loading ? 'SIGNING IN...' : 'SIGN IN'}
          </Button>
        </form>

        <div className="mt-8 text-center">
          <p className="text-xs text-slate-500">
            Access restricted to authorized content creators only.
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginForm;