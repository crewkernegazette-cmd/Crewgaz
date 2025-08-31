import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../App';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Label } from './ui/label';
import { Card, CardHeader, CardContent, CardTitle } from './ui/card';
import { Switch } from './ui/switch';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { 
  PlusCircle, 
  FileText, 
  Users, 
  Settings as SettingsIcon,
  Upload,
  X,
  Eye,
  Calendar,
  Tag,
  Image as ImageIcon,
  Video,
  AlertTriangle,
  Edit,
  Trash2,
  Save
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = BACKEND_URL;

const Dashboard = () => {
  const { user, logout } = useContext(AuthContext);
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState(null);
  const [articles, setArticles] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
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
    tags: []
  });
  const [editingArticle, setEditingArticle] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [selectedImageFile, setSelectedImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  
  // UI states
  const [uploadingImage, setUploadingImage] = useState(false);
  const [creatingArticle, setCreatingArticle] = useState(false);
  
  // Settings state
  const [settings, setSettings] = useState({
    maintenance_mode: false,
    show_breaking_news_banner: true
  });
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [statsRes, articlesRes, contactsRes, settingsRes] = await Promise.all([
        axios.get(`${API}/dashboard/stats`),
        axios.get(`${API}/dashboard/articles`),
        axios.get(`${API}/contacts`),
        axios.get(`${API}/settings`)
      ]);

      setStats(statsRes.data);
      setArticles(articlesRes.data);
      setContacts(contactsRes.data);
      setSettings(settingsRes.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setError('Failed to load dashboard data');
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    console.log('🔍 Image upload started:', file.name, file.type, file.size);

    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast.error('Please select an image file');
      return;
    }

    // Validate file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Image size must be less than 5MB');
      return;
    }

    setUploadingImage(true);
    try {
      // Method 1: Use backend upload (base64 conversion)
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API}/upload-image`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      console.log('📡 Backend response:', response.data);
      
      // Backend returns data URI directly - use as-is
      const imageUrl = response.data.url;
      console.log('🖼️  Setting image URL:', imageUrl.substring(0, 100) + '...');
      
      setArticle({ ...article, featured_image: imageUrl });
      toast.success('Image uploaded successfully');
    } catch (error) {
      console.error('❌ Error uploading image:', error);
      
      // Fallback: Client-side compression and base64 conversion
      console.log('🔄 Trying client-side fallback...');
      try {
        const compressedDataUrl = await compressImage(file);
        console.log('✅ Client-side compression successful:', compressedDataUrl.substring(0, 100) + '...');
        setArticle({ ...article, featured_image: compressedDataUrl });
        toast.success('Image processed successfully (fallback)');
      } catch (fallbackError) {
        console.error('❌ Fallback also failed:', fallbackError);
        toast.error('Failed to process image');
      }
    } finally {
      setUploadingImage(false);
    }
  };

  // Client-side image compression function
  const compressImage = (file, maxWidth = 800, quality = 0.8) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (event) => {
        const img = new Image();
        img.onload = () => {
          const canvas = document.createElement('canvas');
          const ctx = canvas.getContext('2d');
          
          // Calculate new dimensions
          let { width, height } = img;
          if (width > maxWidth) {
            height = (height * maxWidth) / width;
            width = maxWidth;
          }
          
          canvas.width = width;
          canvas.height = height;
          
          // Draw and compress
          ctx.drawImage(img, 0, 0, width, height);
          const compressedDataUrl = canvas.toDataURL('image/jpeg', quality);
          
          console.log('🎨 Image compressed:', {
            original: file.size,
            compressed: compressedDataUrl.length,
            ratio: (compressedDataUrl.length / file.size * 100).toFixed(1) + '%'
          });
          
          resolve(compressedDataUrl);
        };
        img.onerror = reject;
        img.src = event.target.result;
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  const handleTagsChange = (e) => {
    const tags = e.target.value.split(',').map(tag => tag.trim()).filter(tag => tag);
    setArticle({ ...article, tags });
  };

  const handleImageChange = async (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedImageFile(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target.result);
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
      tags: []
    });
    setSelectedImageFile(null);
    setImagePreview(null);
  };

  const handleCreateArticle = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!article.title.trim()) {
      toast.error('Please enter a title');
      return;
    }
    if (!article.content.trim()) {
      toast.error('Please enter content');
      return;
    }

    setCreatingArticle(true);
    try {
      console.log('📰 Creating article with Cloudinary image:', article.title);
      
      // Create FormData for multipart upload
      const formData = new FormData();
      formData.append('title', article.title);
      formData.append('subheading', article.subheading || '');
      formData.append('content', article.content);
      formData.append('category', article.category);
      formData.append('publisher_name', article.publisher_name || 'The Crewkerne Gazette');
      formData.append('image_caption', article.image_caption || '');
      formData.append('video_url', article.video_url || '');
      formData.append('tags', JSON.stringify(article.tags));
      formData.append('is_breaking', article.is_breaking);
      formData.append('is_published', article.is_published);
      
      // Add image file if selected
      if (selectedImageFile) {
        formData.append('featured_image', selectedImageFile);
      }
      
      const response = await axios.post(`${API}/articles`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      console.log('✅ Article created with Cloudinary image:', response.data);
      
      toast.success('Article created successfully!');
      resetForm();
      fetchDashboardData(); // Refresh data
      setActiveTab('articles'); // Switch to articles tab
    } catch (error) {
      console.error('❌ Error creating article:', error);
      toast.error('Failed to create article');
    } finally {
      setCreatingArticle(false);
    }
  };

  const handleSettingsUpdate = async (setting, value) => {
    try {
      if (setting === 'maintenance_mode') {
        await axios.post(`${API}/settings/maintenance`, { maintenance_mode: value });
        toast.success(`Maintenance mode ${value ? 'enabled' : 'disabled'}`);
      } else if (setting === 'show_breaking_news_banner') {
        await axios.post(`${API}/settings/breaking-news-banner`, { show_breaking_news_banner: value });
        toast.success(`Breaking news banner ${value ? 'enabled' : 'disabled'}`);
      }
      
      setSettings({ ...settings, [setting]: value });
    } catch (error) {
      console.error('Error updating settings:', error);
      toast.error('Failed to update settings');
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
      tags: articleToEdit.tags || []
    });
    setActiveTab('create'); // Switch to create tab for editing
  };

  const handleUpdateArticle = async (e) => {
    e.preventDefault();
    
    if (!editingArticle) return;
    
    // Validation
    if (!article.title.trim()) {
      toast.error('Please enter a title');
      return;
    }
    if (!article.content.trim()) {
      toast.error('Please enter content');
      return;
    }

    setCreatingArticle(true);
    try {
      console.log('📝 Updating article:', editingArticle.id, article.title);
      const response = await axios.put(`${API}/articles/${editingArticle.id}`, article);
      console.log('✅ Article updated:', response.data);
      
      toast.success('Article updated successfully!');
      resetForm();
      setIsEditing(false);
      setEditingArticle(null);
      fetchDashboardData(); // Refresh data
      setActiveTab('articles'); // Switch to articles tab
    } catch (error) {
      console.error('❌ Error updating article:', error);
      toast.error('Failed to update article');
    } finally {
      setCreatingArticle(false);
    }
  };

  const handleDeleteArticle = async (articleId, articleTitle) => {
    if (!window.confirm(`Are you sure you want to delete "${articleTitle}"? This action cannot be undone.`)) {
      return;
    }

    try {
      console.log('🗑️ Deleting article:', articleId);
      await axios.delete(`${API}/articles/${articleId}`);
      console.log('✅ Article deleted:', articleId);
      
      toast.success('Article deleted successfully!');
      fetchDashboardData(); // Refresh data
    } catch (error) {
      console.error('❌ Error deleting article:', error);
      toast.error('Failed to delete article');
    }
  };

  const cancelEdit = () => {
    setIsEditing(false);
    setEditingArticle(null);
    resetForm();
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-GB', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
          <p className="text-slate-300 mt-4">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Dashboard Error</h1>
          <p className="text-slate-300 mb-6">{error}</p>
          <Button onClick={fetchDashboardData} className="bg-red-600 hover:bg-red-700">
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="container mx-auto px-4 py-8">
        {/* Dashboard Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Dashboard</h1>
            <p className="text-slate-400">Welcome back, {user?.username}</p>
            {stats?.emergency_mode && (
              <div className="flex items-center space-x-2 mt-2">
                <AlertTriangle className="w-4 h-4 text-yellow-500" />
                <span className="text-yellow-500 text-sm">Emergency Mode Active</span>
              </div>
            )}
          </div>
          <Button 
            onClick={logout}
            variant="outline" 
            className="border-slate-600 text-slate-300 hover:border-red-400 hover:text-red-400"
          >
            Logout
          </Button>
        </div>

        {/* Dashboard Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4 bg-slate-800/50 border border-slate-700">
            <TabsTrigger value="overview" className="data-[state=active]:bg-red-600">
              <FileText className="w-4 h-4 mr-2" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="create" className="data-[state=active]:bg-red-600">
              <PlusCircle className="w-4 h-4 mr-2" />
              Create
            </TabsTrigger>
            <TabsTrigger value="articles" className="data-[state=active]:bg-red-600">
              <FileText className="w-4 h-4 mr-2" />
              Articles
            </TabsTrigger>
            <TabsTrigger value="settings" className="data-[state=active]:bg-red-600">
              <SettingsIcon className="w-4 h-4 mr-2" />
              Settings
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {stats && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card className="bg-slate-800/50 border-slate-700">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg text-white">Total Articles</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-red-400">{stats.total_articles}</div>
                  </CardContent>
                </Card>
                <Card className="bg-slate-800/50 border-slate-700">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg text-white">Published</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-green-400">{stats.published_articles}</div>
                  </CardContent>
                </Card>
                <Card className="bg-slate-800/50 border-slate-700">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg text-white">Breaking News</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-yellow-400">{stats.breaking_news}</div>
                  </CardContent>
                </Card>
                <Card className="bg-slate-800/50 border-slate-700">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg text-white">Contacts</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-blue-400">{stats.total_contacts}</div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Recent Articles */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Recent Articles</CardTitle>
              </CardHeader>
              <CardContent>
                {articles.length > 0 ? (
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
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-400 text-center py-8">No articles yet. Create your first article!</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Create/Edit Article Tab */}
          <TabsContent value="create" className="space-y-6">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center justify-between">
                  {isEditing ? 'Edit Article' : 'Create New Article'}
                  {isEditing && (
                    <Button 
                      onClick={cancelEdit}
                      variant="outline"
                      size="sm"
                      className="border-slate-600 text-slate-400 hover:border-slate-400"
                    >
                      <X className="w-4 h-4 mr-2" />
                      Cancel Edit
                    </Button>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={isEditing ? handleUpdateArticle : handleCreateArticle} className="space-y-6">
                  {/* Basic Info */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="title" className="text-slate-200">Title *</Label>
                      <Input
                        id="title"
                        value={article.title}
                        onChange={(e) => setArticle({ ...article, title: e.target.value })}
                        className="bg-slate-700/50 border-slate-600 text-white"
                        placeholder="Enter article title..."
                        required
                      />
                    </div>
                    <div>
                      <Label htmlFor="category" className="text-slate-200">Category</Label>
                      <Select value={article.category} onValueChange={(value) => setArticle({ ...article, category: value })}>
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
                  </div>

                  {/* Subheading */}
                  <div>
                    <Label htmlFor="subheading" className="text-slate-200">Subheading</Label>
                    <Input
                      id="subheading"
                      value={article.subheading}
                      onChange={(e) => setArticle({ ...article, subheading: e.target.value })}
                      className="bg-slate-700/50 border-slate-600 text-white"
                      placeholder="Optional subheading..."
                    />
                  </div>

                  {/* Content */}
                  <div>
                    <Label htmlFor="content" className="text-slate-200">Content *</Label>
                    <Textarea
                      id="content"
                      value={article.content}
                      onChange={(e) => setArticle({ ...article, content: e.target.value })}
                      className="bg-slate-700/50 border-slate-600 text-white min-h-[200px]"
                      placeholder="Write your article content..."
                      required
                    />
                  </div>

                  {/* Publisher */}
                  <div>
                    <Label htmlFor="publisher" className="text-slate-200">Publisher</Label>
                    <Input
                      id="publisher"
                      value={article.publisher_name}
                      onChange={(e) => setArticle({ ...article, publisher_name: e.target.value })}
                      className="bg-slate-700/50 border-slate-600 text-white"
                      placeholder="Publisher name..."
                    />
                  </div>

                  {/* Featured Image */}
                  <div>
                    <Label className="text-slate-200">Featured Image</Label>
                    
                    {/* Image Preview */}
                    {article.featured_image && (
                      <div className="relative mb-4">
                        <img 
                          src={article.featured_image} 
                          alt="Preview" 
                          className="w-full h-48 object-cover rounded-lg border border-slate-600"
                          onError={(e) => {
                            console.error('Image preview error:', e);
                            setArticle({ ...article, featured_image: '' });
                            toast.error('Invalid image format');
                          }}
                        />
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => setArticle({ ...article, featured_image: '' })}
                          className="absolute top-2 right-2 bg-red-600 hover:bg-red-700 text-white border-red-600"
                        >
                          <X className="w-4 h-4" />
                        </Button>
                      </div>
                    )}

                    {/* Upload Button */}
                    <div>
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleImageUpload}
                        className="hidden"
                        id="image-upload"
                        disabled={uploadingImage}
                      />
                      <Label
                        htmlFor="image-upload"
                        className={`cursor-pointer inline-flex items-center px-4 py-2 border border-slate-600 rounded-md shadow-sm text-sm font-medium text-slate-200 bg-slate-700/50 hover:bg-slate-600/50 transition-colors ${
                          uploadingImage ? 'opacity-50 cursor-not-allowed' : ''
                        }`}
                      >
                        {uploadingImage ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-slate-200 mr-2"></div>
                            Processing...
                          </>
                        ) : (
                          <>
                            <ImageIcon className="w-4 h-4 mr-2" />
                            Upload Image
                          </>
                        )}
                      </Label>
                    </div>
                  </div>

                  {/* Image Caption */}
                  <div>
                    <Label htmlFor="image-caption" className="text-slate-200">Image Caption</Label>
                    <Input
                      id="image-caption"
                      value={article.image_caption}
                      onChange={(e) => setArticle({ ...article, image_caption: e.target.value })}
                      className="bg-slate-700/50 border-slate-600 text-white"
                      placeholder="Optional image caption..."
                    />
                  </div>

                  {/* Video URL */}
                  <div>
                    <Label htmlFor="video-url" className="text-slate-200">Video URL</Label>
                    <Input
                      id="video-url"
                      value={article.video_url}
                      onChange={(e) => setArticle({ ...article, video_url: e.target.value })}
                      className="bg-slate-700/50 border-slate-600 text-white"
                      placeholder="https://youtube.com/embed/..."
                    />
                  </div>

                  {/* Tags */}
                  <div>
                    <Label htmlFor="tags" className="text-slate-200">Tags (comma-separated)</Label>
                    <Input
                      id="tags"
                      value={article.tags.join(', ')}
                      onChange={handleTagsChange}
                      className="bg-slate-700/50 border-slate-600 text-white"
                      placeholder="breaking, politics, investigation, local news"
                    />
                  </div>

                  {/* Switches */}
                  <div className="flex items-center space-x-8">
                    <div className="flex items-center space-x-2">
                      <Switch
                        checked={article.is_breaking}
                        onCheckedChange={(checked) => setArticle({ ...article, is_breaking: checked })}
                        className="data-[state=checked]:bg-red-600"
                      />
                      <Label className="text-slate-200">Breaking News</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Switch
                        checked={article.is_published}
                        onCheckedChange={(checked) => setArticle({ ...article, is_published: checked })}
                        className="data-[state=checked]:bg-green-600"
                      />
                      <Label className="text-slate-200">Published</Label>
                    </div>
                  </div>

                  {/* Submit */}
                  <div className="flex items-center space-x-4">
                    <Button 
                      type="submit" 
                      className="bg-red-600 hover:bg-red-700"
                      disabled={creatingArticle}
                    >
                      {creatingArticle ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          {isEditing ? 'Updating...' : 'Creating...'}
                        </>
                      ) : (
                        <>
                          {isEditing ? <Save className="w-4 h-4 mr-2" /> : <PlusCircle className="w-4 h-4 mr-2" />}
                          {isEditing ? 'Update Article' : 'Create Article'}
                        </>
                      )}
                    </Button>
                    <Button 
                      type="button" 
                      variant="outline"
                      onClick={isEditing ? cancelEdit : resetForm}
                      className="border-slate-600 text-slate-300 hover:border-slate-400"
                    >
                      {isEditing ? 'Cancel' : 'Reset'}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Articles Tab */}
          <TabsContent value="articles" className="space-y-6">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">All Articles ({articles.length})</CardTitle>
              </CardHeader>
              <CardContent>
                {articles.length > 0 ? (
                  <div className="space-y-4">
                    {articles.map(article => (
                      <div key={article.id} className="flex items-center justify-between p-4 bg-slate-900/50 rounded-lg border border-slate-700">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3">
                            <h3 className="font-semibold text-white">{article.title}</h3>
                            {article.is_breaking && (
                              <Badge className="bg-red-600 text-white text-xs">Breaking</Badge>
                            )}
                            {!article.is_published && (
                              <Badge variant="outline" className="border-yellow-600 text-yellow-400 text-xs">Draft</Badge>
                            )}
                          </div>
                          {article.subheading && (
                            <p className="text-slate-400 text-sm mt-1">{article.subheading}</p>
                          )}
                          <div className="flex items-center space-x-4 mt-2 text-sm text-slate-400">
                            <span className="flex items-center">
                              <Calendar className="w-3 h-3 mr-1" />
                              {formatDate(article.created_at)}
                            </span>
                            <Badge variant="outline" className="border-slate-600 text-slate-400 text-xs">
                              {article.category}
                            </Badge>
                            {article.tags.length > 0 && (
                              <span className="flex items-center">
                                <Tag className="w-3 h-3 mr-1" />
                                {article.tags.slice(0, 2).join(', ')}
                                {article.tags.length > 2 && '...'}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => window.open(`/article/${article.id}`, '_blank')}
                            className="border-slate-600 text-slate-400 hover:border-slate-400"
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleEditArticle(article)}
                            className="border-blue-600 text-blue-400 hover:border-blue-400"
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDeleteArticle(article.id, article.title)}
                            className="border-red-600 text-red-400 hover:border-red-400"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <FileText className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-400">No articles yet. Create your first article!</p>
                    <Button 
                      onClick={() => setActiveTab('create')}
                      className="bg-red-600 hover:bg-red-700 mt-4"
                    >
                      <PlusCircle className="w-4 h-4 mr-2" />
                      Create Article
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Site Settings */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white">Site Settings</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label className="text-slate-200 font-medium">Maintenance Mode</Label>
                      <p className="text-sm text-slate-400">Put the site in maintenance mode</p>
                    </div>
                    <Switch
                      checked={settings.maintenance_mode}
                      onCheckedChange={(checked) => handleSettingsUpdate('maintenance_mode', checked)}
                      className="data-[state=checked]:bg-yellow-600"
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label className="text-slate-200 font-medium">Breaking News Banner</Label>
                      <p className="text-sm text-slate-400">Show breaking news banner on homepage</p>
                    </div>
                    <Switch
                      checked={settings.show_breaking_news_banner}
                      onCheckedChange={(checked) => handleSettingsUpdate('show_breaking_news_banner', checked)}
                      className="data-[state=checked]:bg-red-600"
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Contact Messages */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white">Recent Messages ({contacts.length})</CardTitle>
                </CardHeader>
                <CardContent>
                  {contacts.length > 0 ? (
                    <div className="space-y-4 max-h-64 overflow-y-auto">
                      {contacts.slice(0, 5).map(contact => (
                        <div key={contact.id} className="p-3 bg-slate-900/50 rounded-lg border border-slate-700">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium text-white">{contact.email}</span>
                            <Badge 
                              variant={contact.status === 'new' ? 'default' : 'outline'}
                              className={contact.status === 'new' ? 'bg-green-600 text-white' : 'border-slate-600 text-slate-400'}
                            >
                              {contact.status}
                            </Badge>
                          </div>
                          <p className="text-sm text-slate-300 line-clamp-2">{contact.inquiry}</p>
                          <p className="text-xs text-slate-500 mt-2">{formatDate(contact.created_at)}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-400 text-center py-4">No messages yet.</p>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Dashboard;