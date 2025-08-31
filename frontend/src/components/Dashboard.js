import React, { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Switch } from './ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Calendar, Clock, Edit2, Trash2, Users, FileText, Settings, MessageSquare, Eye, Tag, Copy, Mail } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

import { API_BASE } from '../config/api';

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  
  // Dashboard data state
  const [stats, setStats] = useState(null);
  const [articles, setArticles] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [availableCategoryLabels, setAvailableCategoryLabels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Settings state
  const [settings, setSettings] = useState({
    show_breaking_news_banner: true,
    admin_password: ''
  });

  // Article creation state
  const [article, setArticle] = useState({
    title: '',
    subheading: '',
    content: '',
    category: 'news',
    publisher_name: 'The Crewkerne Gazette',
    featured_image: '',
    image_caption: '',
    video_url: '',
    is_breaking: false,
    is_published: true,
    tags: [],
    category_labels: []
  });

  const [isEditing, setIsEditing] = useState(false);
  const [editingArticle, setEditingArticle] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedImageFile, setSelectedImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);

  useEffect(() => {
    fetchDashboardData();
    fetchCategoryLabels();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [statsRes, articlesRes, contactsRes, settingsRes] = await Promise.all([
        axios.get(`${API_BASE}/api/dashboard/stats`, { withCredentials: true }),
        axios.get(`${API_BASE}/api/dashboard/articles`, { withCredentials: true }),
        axios.get(`${API_BASE}/api/contacts`, { withCredentials: true }),
        axios.get(`${API_BASE}/api/settings`, { withCredentials: true })
      ]);

      setStats(statsRes.data);
      // Ensure articles is always an array
      const articlesData = Array.isArray(articlesRes.data) ? articlesRes.data : [];
      setArticles(articlesData);
      console.warn('Dashboard - Articles state after fetch:', articlesData);
      
      setContacts(contactsRes.data.contacts || contactsRes.data || []); // Handle both old and new response formats
      setSettings(settingsRes.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setError('Failed to load dashboard data');
      toast.error('Failed to load dashboard data');
      // Ensure arrays are set even on error
      setArticles([]);
      setContacts([]);
      console.warn('Dashboard - Articles state set to empty array due to error');
    } finally {
      setLoading(false);
    }
  };

  const fetchCategoryLabels = async () => {
    try {
      const response = await axios.get(`${API}/api/categories/labels`);
      const labels = Array.isArray(response.data.category_labels) ? response.data.category_labels : [];
      setAvailableCategoryLabels(labels);
      console.warn('Available category labels:', labels);
    } catch (error) {
      console.error('Error fetching category labels:', error);
      // Set default fallback categories if API fails
      setAvailableCategoryLabels([
        'Satire', 'Straight Talking', 'Opinion', 'Sports', 'Gossip', 
        'Politics', 'Local News', 'News', 'Agony Aunt', 'Special', 'Exclusive'
      ]);
    }
  };

  // Debug logging in render
  console.warn('Dashboard render - Articles state:', articles, 'Type:', typeof articles, 'IsArray:', Array.isArray(articles));

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setArticle({
      ...article,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const handleTagsChange = (e) => {
    const tags = e.target.value.split(',').map(tag => tag.trim()).filter(tag => tag);
    setArticle({
      ...article,
      tags
    });
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedImageFile(file);
      const reader = new FileReader();
      reader.onload = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const resetForm = () => {
    setArticle({
      title: '',
      subheading: '',
      content: '',
      category: 'news',
      publisher_name: 'The Crewkerne Gazette',
      featured_image: '',
      image_caption: '',
      video_url: '',
      is_breaking: false,
      is_published: true,
      tags: [],
      category_labels: []
    });
    setSelectedImageFile(null);
    setImagePreview(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        toast.error('Authentication required');
        return;
      }

      const formData = new FormData();
      formData.append('title', article.title);
      formData.append('subheading', article.subheading || '');
      formData.append('content', article.content);
      formData.append('category', article.category);
      formData.append('publisher_name', article.publisher_name);
      formData.append('image_caption', article.image_caption || '');
      formData.append('video_url', article.video_url || '');
      formData.append('tags', JSON.stringify(article.tags));
      formData.append('category_labels', JSON.stringify(article.category_labels));
      formData.append('is_breaking', article.is_breaking);
      formData.append('is_published', article.is_published);

      if (selectedImageFile) {
        formData.append('featured_image', selectedImageFile);
      }

      let response;
      if (isEditing && editingArticle) {
        response = await axios.put(`${API}/api/articles/${editingArticle.slug}`, formData, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        });
        toast.success('Article updated successfully!');
      } else {
        response = await axios.post(`${API}/api/articles`, formData, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        });
        toast.success('Article created successfully!');
      }

      resetForm();
      setIsEditing(false);
      setEditingArticle(null);
      fetchDashboardData();
    } catch (error) {
      console.error('Error submitting article:', error);
      toast.error(error.response?.data?.detail || 'Failed to submit article');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEditArticle = (articleToEdit) => {
    setEditingArticle(articleToEdit);
    setIsEditing(true);
    setArticle({
      title: articleToEdit.title,
      subheading: articleToEdit.subheading || '',
      content: articleToEdit.content,
      category: articleToEdit.category,
      publisher_name: articleToEdit.publisher_name || 'The Crewkerne Gazette',
      featured_image: articleToEdit.featured_image || '',
      image_caption: articleToEdit.image_caption || '',
      video_url: articleToEdit.video_url || '',
      is_breaking: articleToEdit.is_breaking || false,
      is_published: articleToEdit.is_published !== false, // Default to true
      tags: Array.isArray(articleToEdit.tags) ? articleToEdit.tags : [],
      category_labels: Array.isArray(articleToEdit.category_labels) ? articleToEdit.category_labels : []
    });
    setActiveTab('create'); // Switch to create tab for editing
  };

  const handleDeleteArticle = async (articleSlug) => {
    if (!window.confirm('Are you sure you want to delete this article?')) {
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      await axios.delete(`${API}/api/articles/${articleSlug}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      toast.success('Article deleted successfully!');
      fetchDashboardData();
    } catch (error) {
      console.error('Error deleting article:', error);
      toast.error('Failed to delete article');
    }
  };

  const handleSettingsUpdate = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('access_token');
      await axios.put(`${API}/api/settings`, settings, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      toast.success('Settings updated successfully!');
    } catch (error) {
      console.error('Error updating settings:', error);
      toast.error('Failed to update settings');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  const handleReplyToContact = (contact) => {
    const subject = `Re: Message from ${contact.name}`;
    const body = `Dear ${contact.name},\n\nThank you for your message:\n"${contact.message}"\n\nBest regards,\nThe Crewkerne Gazette Team`;
    const mailtoLink = `mailto:${contact.email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    window.open(mailtoLink);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-red-400 text-xl">{error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto p-6">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Dashboard</h1>
          <p className="text-slate-400">Manage your content and settings</p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-slate-800 border border-slate-700">
            <TabsTrigger value="overview" className="text-slate-300 data-[state=active]:text-white">
              <Users className="w-4 h-4 mr-2" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="create" className="text-slate-300 data-[state=active]:text-white">
              <FileText className="w-4 h-4 mr-2" />
              Create
            </TabsTrigger>
            <TabsTrigger value="articles" className="text-slate-300 data-[state=active]:text-white">
              <FileText className="w-4 h-4 mr-2" />
              Articles
            </TabsTrigger>
            <TabsTrigger value="messages" className="text-slate-300 data-[state=active]:text-white">
              <MessageSquare className="w-4 h-4 mr-2" />
              Messages
            </TabsTrigger>
            <TabsTrigger value="settings" className="text-slate-300 data-[state=active]:text-white">
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white flex items-center">
                    <FileText className="w-5 h-5 mr-2" />
                    Total Articles
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-white">{stats?.total_articles || 0}</p>
                </CardContent>
              </Card>

              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white flex items-center">
                    <Users className="w-5 h-5 mr-2" />
                    Total Messages
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-white">{Array.isArray(contacts) ? contacts.length : 0}</p>
                </CardContent>
              </Card>

              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white flex items-center">
                    <Eye className="w-5 h-5 mr-2" />
                    Published Articles
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-white">{stats?.published_articles || 0}</p>
                </CardContent>
              </Card>
            </div>

            {/* Recent Articles */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Recent Articles</CardTitle>
              </CardHeader>
              <CardContent>
                {Array.isArray(articles) && articles.length > 0 ? (
                  <div className="space-y-4">
                    {articles.slice(0, 5).map(article => (
                      <div key={article.id} className="flex items-center justify-between p-4 bg-slate-900/50 rounded-lg">
                        <div className="flex-1">
                          <h3 className="font-semibold text-white">{article.title}</h3>
                          <div className="flex items-center space-x-4 mt-2 text-sm text-slate-400">
                            <span>{formatDate(article.created_at)}</span>
                            <Badge variant="outline" className="border-slate-600 text-slate-400">
                              {article.category}
                            </Badge>
                            {article.is_breaking && (
                              <Badge className="bg-red-600 text-white">Breaking</Badge>
                            )}
                          </div>
                          
                          {/* Category Labels Display */}
                          {Array.isArray(article.category_labels) && article.category_labels.length > 0 && (
                            <div className="mt-2">
                              <div className="flex flex-wrap gap-1">
                                {article.category_labels.slice(0, 2).map((label, index) => (
                                  <Badge
                                    key={index}
                                    className="bg-red-600/20 text-red-300 border border-red-600/30 text-xs px-1 py-0.5"
                                  >
                                    {label}
                                  </Badge>
                                ))}
                                {article.category_labels.length > 2 && (
                                  <Badge className="bg-slate-600/20 text-slate-300 border border-slate-600/30 text-xs px-1 py-0.5">
                                    +{article.category_labels.length - 2}
                                  </Badge>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                        <div className="flex items-center space-x-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleEditArticle(article)}
                            className="border-slate-600 text-slate-300 hover:bg-slate-700"
                          >
                            <Edit2 className="w-3 h-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDeleteArticle(article.slug)}
                            className="border-red-600 text-red-400 hover:bg-red-900/20"
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-slate-400">No articles yet. Create your first article!</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Create Tab */}
          <TabsContent value="create">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">
                  {isEditing ? 'Edit Article' : 'Create New Article'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Title */}
                    <div className="md:col-span-2">
                      <Label htmlFor="title" className="text-slate-200">Title *</Label>
                      <Input
                        id="title"
                        name="title"
                        value={article.title}
                        onChange={handleInputChange}
                        required
                        className="bg-slate-700/50 border-slate-600 text-white"
                        placeholder="Enter article title"
                      />
                    </div>

                    {/* Subheading */}
                    <div className="md:col-span-2">
                      <Label htmlFor="subheading" className="text-slate-200">Subheading</Label>
                      <Input
                        id="subheading"
                        name="subheading"
                        value={article.subheading}
                        onChange={handleInputChange}
                        className="bg-slate-700/50 border-slate-600 text-white"
                        placeholder="Optional subheading"
                      />
                    </div>

                    {/* Category */}
                    <div>
                      <Label htmlFor="category" className="text-slate-200">Category *</Label>
                      <Select value={article.category} onValueChange={(value) => setArticle({...article, category: value})}>
                        <SelectTrigger className="bg-slate-700/50 border-slate-600 text-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-slate-800 border-slate-600">
                          <SelectItem value="news">News</SelectItem>
                          <SelectItem value="music">Music</SelectItem>
                          <SelectItem value="documentaries">Documentaries</SelectItem>
                          <SelectItem value="comedy">Comedy</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Publisher */}
                    <div>
                      <Label htmlFor="publisher_name" className="text-slate-200">Publisher</Label>
                      <Input
                        id="publisher_name"
                        name="publisher_name"
                        value={article.publisher_name}
                        onChange={handleInputChange}
                        className="bg-slate-700/50 border-slate-600 text-white"
                      />
                    </div>

                    {/* Featured Image Upload */}
                    <div>
                      <Label htmlFor="featured_image" className="text-slate-200">Featured Image</Label>
                      <Input
                        id="featured_image"
                        type="file"
                        accept="image/*"
                        onChange={handleImageUpload}
                        className="bg-slate-700/50 border-slate-600 text-white file:bg-slate-600 file:text-white file:border-0"
                      />
                      {imagePreview && (
                        <div className="mt-2">
                          <img src={imagePreview} alt="Preview" className="w-32 h-32 object-cover rounded" />
                        </div>
                      )}
                    </div>

                    {/* Image Caption */}
                    <div>
                      <Label htmlFor="image_caption" className="text-slate-200">Image Caption</Label>
                      <Input
                        id="image_caption"
                        name="image_caption"
                        value={article.image_caption}
                        onChange={handleInputChange}
                        className="bg-slate-700/50 border-slate-600 text-white"
                        placeholder="Optional image caption"
                      />
                    </div>

                    {/* Video URL */}
                    <div className="md:col-span-2">
                      <Label htmlFor="video_url" className="text-slate-200">Video URL</Label>
                      <Input
                        id="video_url"
                        name="video_url"
                        value={article.video_url}
                        onChange={handleInputChange}
                        className="bg-slate-700/50 border-slate-600 text-white"
                        placeholder="Optional video URL"
                      />
                    </div>

                    {/* Tags */}
                    <div>
                      <Label htmlFor="tags" className="text-slate-200">Tags (comma-separated)</Label>
                      <Input
                        id="tags"
                        value={Array.isArray(article.tags) ? article.tags.join(', ') : ''}
                        onChange={handleTagsChange}
                        className="bg-slate-700/50 border-slate-600 text-white"
                        placeholder="breaking, politics, investigation, local news"
                      />
                    </div>

                    {/* Category Labels */}
                    <div className="md:col-span-2">
                      <Label className="text-slate-200 mb-3 block">Category Labels</Label>
                      <div className="space-y-3">
                        <p className="text-sm text-slate-400">
                          Select multiple category labels that best describe this article:
                        </p>
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 max-h-48 overflow-y-auto p-3 bg-slate-700/20 rounded-lg border border-slate-600">
                          {Array.isArray(availableCategoryLabels) && availableCategoryLabels.map((label) => {
                            const isSelected = Array.isArray(article.category_labels) && article.category_labels.includes(label);
                            return (
                              <div key={label} className="flex items-center space-x-2">
                                <input
                                  type="checkbox"
                                  id={`category-${label}`}
                                  checked={isSelected}
                                  onChange={(e) => {
                                    const currentLabels = Array.isArray(article.category_labels) ? article.category_labels : [];
                                    if (e.target.checked) {
                                      setArticle({
                                        ...article,
                                        category_labels: [...currentLabels, label]
                                      });
                                    } else {
                                      setArticle({
                                        ...article,
                                        category_labels: currentLabels.filter(l => l !== label)
                                      });
                                    }
                                  }}
                                  className="rounded border-slate-500 text-red-600 focus:ring-red-500 focus:ring-offset-0 bg-slate-700"
                                />
                                <Label
                                  htmlFor={`category-${label}`}
                                  className={`text-sm cursor-pointer transition-colors ${
                                    isSelected ? 'text-red-400 font-medium' : 'text-slate-300 hover:text-slate-200'
                                  }`}
                                >
                                  {label}
                                </Label>
                              </div>
                            );
                          })}
                        </div>
                        
                        {/* Selected Labels Preview */}
                        {Array.isArray(article.category_labels) && article.category_labels.length > 0 && (
                          <div className="mt-3">
                            <p className="text-sm text-slate-400 mb-2">Selected ({article.category_labels.length}):</p>
                            <div className="flex flex-wrap gap-2">
                              {article.category_labels.map((label, index) => (
                                <Badge
                                  key={index}
                                  className="bg-red-600/20 text-red-300 border border-red-600/30 px-2 py-1 text-xs"
                                >
                                  {label}
                                  <button
                                    type="button"
                                    onClick={() => {
                                      setArticle({
                                        ...article,
                                        category_labels: article.category_labels.filter(l => l !== label)
                                      });
                                    }}
                                    className="ml-2 text-red-400 hover:text-red-300"
                                  >
                                    ×
                                  </button>
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Content */}
                  <div>
                    <Label htmlFor="content" className="text-slate-200">Content *</Label>
                    <Textarea
                      id="content"
                      name="content"
                      value={article.content}
                      onChange={handleInputChange}
                      required
                      rows={10}
                      className="bg-slate-700/50 border-slate-600 text-white"
                      placeholder="Write your article content here..."
                    />
                  </div>

                  {/* Options */}
                  <div className="flex items-center space-x-6">
                    <div className="flex items-center space-x-2">
                      <Switch
                        id="is_breaking"
                        checked={article.is_breaking}
                        onCheckedChange={(checked) => setArticle({...article, is_breaking: checked})}
                      />
                      <Label htmlFor="is_breaking" className="text-slate-200">Breaking News</Label>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Switch
                        id="is_published"
                        checked={article.is_published}
                        onCheckedChange={(checked) => setArticle({...article, is_published: checked})}
                      />
                      <Label htmlFor="is_published" className="text-slate-200">Published</Label>
                    </div>
                  </div>

                  {/* Submit Buttons */}
                  <div className="flex items-center space-x-4">
                    <Button 
                      type="submit" 
                      disabled={isSubmitting}
                      className="bg-red-600 hover:bg-red-700 text-white"
                    >
                      {isSubmitting ? 'Saving...' : (isEditing ? 'Update Article' : 'Create Article')}
                    </Button>
                    
                    {isEditing && (
                      <Button 
                        type="button" 
                        variant="outline"
                        onClick={() => {
                          setIsEditing(false);
                          setEditingArticle(null);
                          resetForm();
                        }}
                        className="border-slate-600 text-slate-300 hover:bg-slate-700"
                      >
                        Cancel Edit
                      </Button>
                    )}
                  </div>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Articles Tab */}
          <TabsContent value="articles">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">All Articles ({Array.isArray(articles) ? articles.length : 0})</CardTitle>
              </CardHeader>
              <CardContent>
                {Array.isArray(articles) && articles.length > 0 ? (
                  <div className="space-y-4">
                    {articles.map(article => (
                      <div key={article.id} className="flex items-center justify-between p-4 bg-slate-900/50 rounded-lg border border-slate-700">
                        <div className="flex-1">
                          <h3 className="font-semibold text-white">{article.title}</h3>
                          <p className="text-sm text-slate-400 mt-1">
                            {article.content.substring(0, 120)}...
                          </p>
                          <div className="flex items-center space-x-4 mt-2 text-sm text-slate-400">
                            <span className="flex items-center">
                              <Calendar className="w-3 h-3 mr-1" />
                              {formatDate(article.created_at)}
                            </span>
                            <Badge variant="outline" className="border-slate-600 text-slate-400 text-xs">
                              {article.category}
                            </Badge>
                            {Array.isArray(article.tags) && article.tags.length > 0 && (
                              <span className="flex items-center">
                                <Tag className="w-3 h-3 mr-1" />
                                {article.tags.slice(0, 2).join(', ')}
                                {article.tags.length > 2 && '...'}
                              </span>
                            )}
                          </div>
                          
                          {/* Category Labels Display */}
                          {Array.isArray(article.category_labels) && article.category_labels.length > 0 && (
                            <div className="mt-2">
                              <div className="flex flex-wrap gap-1">
                                {article.category_labels.slice(0, 3).map((label, index) => (
                                  <Badge
                                    key={index}
                                    className="bg-red-600/20 text-red-300 border border-red-600/30 text-xs px-2 py-1"
                                  >
                                    {label}
                                  </Badge>
                                ))}
                                {article.category_labels.length > 3 && (
                                  <Badge className="bg-slate-600/20 text-slate-300 border border-slate-600/30 text-xs px-2 py-1">
                                    +{article.category_labels.length - 3}
                                  </Badge>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                        <div className="flex items-center space-x-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleEditArticle(article)}
                            className="border-slate-600 text-slate-300 hover:bg-slate-700"
                          >
                            <Edit2 className="w-3 h-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDeleteArticle(article.slug)}
                            className="border-red-600 text-red-400 hover:bg-red-900/20"
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-slate-400">No articles found. Create your first article!</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Messages Tab */}
          <TabsContent value="messages">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Contact Messages ({Array.isArray(contacts) ? contacts.length : 0})</CardTitle>
              </CardHeader>
              <CardContent>
                {Array.isArray(contacts) && contacts.length > 0 ? (
                  <div className="space-y-4">
                    {contacts.map(contact => (
                      <div key={contact.id || contact.timestamp} className="p-4 bg-slate-900/50 rounded-lg border border-slate-700">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-2">
                              <h3 className="font-semibold text-white">{contact.name}</h3>
                              <Badge variant="outline" className="border-slate-600 text-slate-400 text-xs">
                                {contact.email}
                              </Badge>
                              {contact.is_emergency && (
                                <Badge className="bg-yellow-600 text-white text-xs">Emergency Backup</Badge>
                              )}
                            </div>
                            <p className="text-slate-300 mb-3">{contact.message}</p>
                            <div className="text-sm text-slate-400">
                              <Clock className="w-3 h-3 inline mr-1" />
                              {contact.created_at ? formatDate(contact.created_at) : contact.timestamp}
                            </div>
                          </div>
                          <div className="flex items-center space-x-2 ml-4">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => copyToClipboard(contact.email)}
                              className="border-slate-600 text-slate-300 hover:bg-slate-700"
                            >
                              <Copy className="w-3 h-3" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleReplyToContact(contact)}
                              className="border-slate-600 text-slate-300 hover:bg-slate-700"
                            >
                              <Mail className="w-3 h-3" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-slate-400">No messages yet.</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Recent Messages Summary */}
            <Card className="bg-slate-800/50 border-slate-700 mt-6">
              <CardHeader>
                <CardTitle className="text-white">Recent Messages Summary</CardTitle>
              </CardHeader>
              <CardContent>
                {Array.isArray(contacts) && contacts.length > 0 ? (
                  <div className="space-y-3">
                    {contacts.slice(0, 5).map(contact => (
                      <div key={contact.id || contact.timestamp} className="flex items-center justify-between p-3 bg-slate-900/30 rounded">
                        <div>
                          <span className="text-white font-medium">{contact.name}</span>
                          <span className="text-slate-400 ml-2 text-sm">({contact.email})</span>
                        </div>
                        <div className="text-sm text-slate-400">
                          {contact.created_at ? formatDate(contact.created_at) : contact.timestamp}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-400 text-center py-4">No recent messages</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Site Settings</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSettingsUpdate} className="space-y-6">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="show_breaking_news_banner"
                      checked={settings.show_breaking_news_banner}
                      onCheckedChange={(checked) => setSettings({...settings, show_breaking_news_banner: checked})}
                    />
                    <Label htmlFor="show_breaking_news_banner" className="text-slate-200">
                      Show Breaking News Banner
                    </Label>
                  </div>

                  <div>
                    <Label htmlFor="admin_password" className="text-slate-200">Update Admin Password</Label>
                    <Input
                      id="admin_password"
                      type="password"
                      value={settings.admin_password}
                      onChange={(e) => setSettings({...settings, admin_password: e.target.value})}
                      className="bg-slate-700/50 border-slate-600 text-white"
                      placeholder="Leave empty to keep current password"
                    />
                  </div>

                  <Button type="submit" className="bg-red-600 hover:bg-red-700 text-white">
                    Update Settings
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Dashboard;