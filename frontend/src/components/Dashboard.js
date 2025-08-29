import React, { useState, useEffect, useContext } from 'react';
import { Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import axios from 'axios';
import { AuthContext } from '../App';
import { 
  LayoutDashboard, 
  FileText, 
  PlusCircle, 
  BarChart3, 
  Settings,
  Eye,
  Edit,
  Trash2,
  Save,
  X
} from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Switch } from './ui/switch';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Dashboard Overview Component
const DashboardOverview = () => {
  const [stats, setStats] = useState({});
  const [recentArticles, setRecentArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, articlesRes] = await Promise.all([
        axios.get(`${API}/dashboard/stats`),
        axios.get(`${API}/dashboard/articles?limit=5`)
      ]);
      setStats(statsRes.data);
      setRecentArticles(articlesRes.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="loading-spinner"></div></div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">Dashboard Overview</h1>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-400">Total Articles</CardTitle>
            <div className="text-2xl font-bold text-white">{stats.total_articles || 0}</div>
          </CardHeader>
        </Card>
        
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-400">Published</CardTitle>
            <div className="text-2xl font-bold text-green-400">{stats.published_articles || 0}</div>
          </CardHeader>
        </Card>
        
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-400">Breaking News</CardTitle>
            <div className="text-2xl font-bold text-red-400">{stats.breaking_news || 0}</div>
          </CardHeader>
        </Card>
        
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-400">Categories</CardTitle>
            <div className="text-2xl font-bold text-blue-400">4</div>
          </CardHeader>
        </Card>
      </div>

      {/* Category Breakdown */}
      {stats.categories && (
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Content by Category</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(stats.categories).map(([category, count]) => (
                <div key={category} className="text-center">
                  <div className="text-2xl font-bold text-slate-300">{count}</div>
                  <div className="text-sm text-slate-400 capitalize">{category}</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Articles */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">Recent Articles</CardTitle>
        </CardHeader>
        <CardContent>
          {recentArticles.length === 0 ? (
            <p className="text-slate-400">No articles yet. Create your first article!</p>
          ) : (
            <div className="space-y-3">
              {recentArticles.map((article) => (
                <div key={article.id} className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg">
                  <div>
                    <h3 className="font-medium text-white">{article.title}</h3>
                    <p className="text-sm text-slate-400 capitalize">{article.category} • {new Date(article.created_at).toLocaleDateString()}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    {article.is_breaking && <Badge variant="destructive" className="text-xs">Breaking</Badge>}
                    <Badge variant={article.is_published ? "success" : "secondary"} className="text-xs">
                      {article.is_published ? "Published" : "Draft"}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// Articles Management Component
const ArticlesManager = () => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchArticles();
  }, []);

  const fetchArticles = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/articles`);
      setArticles(response.data);
    } catch (error) {
      console.error('Error fetching articles:', error);
    } finally {
      setLoading(false);
    }
  };

  const deleteArticle = async (articleId) => {
    if (!window.confirm('Are you sure you want to delete this article?')) return;
    
    try {
      await axios.delete(`${API}/articles/${articleId}`);
      setArticles(articles.filter(a => a.id !== articleId));
      toast.success('Article deleted successfully');
    } catch (error) {
      console.error('Error deleting article:', error);
      toast.error('Failed to delete article');
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="loading-spinner"></div></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white">Manage Articles</h1>
        <Link to="/dashboard/create">
          <Button className="bg-red-600 hover:bg-red-700">
            <PlusCircle className="w-4 h-4 mr-2" />
            Create Article
          </Button>
        </Link>
      </div>

      {articles.length === 0 ? (
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="py-16 text-center">
            <FileText className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-slate-300 mb-2">No articles yet</h3>
            <p className="text-slate-400 mb-6">Get started by creating your first article</p>
            <Link to="/dashboard/create">
              <Button>Create Article</Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {articles.map((article) => (
            <Card key={article.id} className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-white mb-2">{article.title}</h3>
                    <div className="flex items-center space-x-4 text-sm text-slate-400">
                      <Badge className={`category-badge category-${article.category}`}>
                        {article.category}
                      </Badge>
                      <span>{new Date(article.created_at).toLocaleDateString()}</span>
                      <span>By {article.author_name}</span>
                      {article.is_breaking && <Badge variant="destructive" className="text-xs">Breaking</Badge>}
                      <Badge variant={article.is_published ? "success" : "secondary"} className="text-xs">
                        {article.is_published ? "Published" : "Draft"}
                      </Badge>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Link to={`/article/${article.id}`}>
                      <Button variant="outline" size="sm">
                        <Eye className="w-4 h-4" />
                      </Button>
                    </Link>
                    <Link to={`/dashboard/edit/${article.id}`}>
                      <Button variant="outline" size="sm">
                        <Edit className="w-4 h-4" />
                      </Button>
                    </Link>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => deleteArticle(article.id)}
                      className="text-red-400 border-red-400 hover:bg-red-400 hover:text-white"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

// Article Editor Component
const ArticleEditor = ({ articleId = null }) => {
  const [article, setArticle] = useState({
    title: '',
    content: '',
    category: 'news',
    featured_image: '',
    video_url: '',
    is_breaking: false,
    is_published: true,
    tags: []
  });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (articleId) {
      fetchArticle();
    }
  }, [articleId]);

  const fetchArticle = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/articles/${articleId}`);
      setArticle(response.data);
    } catch (error) {
      console.error('Error fetching article:', error);
      toast.error('Failed to load article');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      if (articleId) {
        await axios.put(`${API}/articles/${articleId}`, article);
        toast.success('Article updated successfully');
      } else {
        await axios.post(`${API}/articles`, article);
        toast.success('Article created successfully');
        // Reset form
        setArticle({
          title: '',
          content: '',
          category: 'news',
          featured_image: '',
          video_url: '',
          is_breaking: false,
          is_published: true,
          tags: []
        });
      }
    } catch (error) {
      console.error('Error saving article:', error);
      toast.error('Failed to save article');
    } finally {
      setSaving(false);
    }
  };

  const handleTagsChange = (e) => {
    const tags = e.target.value.split(',').map(tag => tag.trim()).filter(tag => tag);
    setArticle({ ...article, tags });
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="loading-spinner"></div></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white">
          {articleId ? 'Edit Article' : 'Create Article'}
        </h1>
        <Link to="/dashboard/articles">
          <Button variant="outline">
            <X className="w-4 h-4 mr-2" />
            Cancel
          </Button>
        </Link>
      </div>

      <Card className="bg-slate-800/50 border-slate-700">
        <CardContent className="p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Title */}
            <div>
              <Label htmlFor="title" className="text-slate-200">Title</Label>
              <Input
                id="title"
                value={article.title}
                onChange={(e) => setArticle({ ...article, title: e.target.value })}
                className="bg-slate-700/50 border-slate-600 text-white"
                required
              />
            </div>

            {/* Category */}
            <div>
              <Label htmlFor="category" className="text-slate-200">Category</Label>
              <Select value={article.category} onValueChange={(value) => setArticle({ ...article, category: value })}>
                <SelectTrigger className="bg-slate-700/50 border-slate-600 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="news">News</SelectItem>
                  <SelectItem value="music">Music</SelectItem>
                  <SelectItem value="documentaries">Documentaries</SelectItem>
                  <SelectItem value="comedy">Comedy</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Content */}
            <div>
              <Label htmlFor="content" className="text-slate-200">Content</Label>
              <Textarea
                id="content"
                value={article.content}
                onChange={(e) => setArticle({ ...article, content: e.target.value })}
                className="bg-slate-700/50 border-slate-600 text-white min-h-[300px]"
                required
              />
            </div>

            {/* Featured Image */}
            <div>
              <Label htmlFor="featured_image" className="text-slate-200">Featured Image URL</Label>
              <Input
                id="featured_image"
                value={article.featured_image}
                onChange={(e) => setArticle({ ...article, featured_image: e.target.value })}
                className="bg-slate-700/50 border-slate-600 text-white"
                placeholder="https://example.com/image.jpg"
              />
            </div>

            {/* Video URL */}
            <div>
              <Label htmlFor="video_url" className="text-slate-200">Video URL</Label>
              <Input
                id="video_url"
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
                placeholder="breaking, politics, investigation"
              />
            </div>

            {/* Switches */}
            <div className="flex items-center space-x-8">
              <div className="flex items-center space-x-2">
                <Switch
                  checked={article.is_breaking}
                  onCheckedChange={(checked) => setArticle({ ...article, is_breaking: checked })}
                />
                <Label className="text-slate-200">Breaking News</Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch
                  checked={article.is_published}
                  onCheckedChange={(checked) => setArticle({ ...article, is_published: checked })}
                />
                <Label className="text-slate-200">Published</Label>
              </div>
            </div>

            <Button 
              type="submit" 
              disabled={saving}
              className="w-full bg-red-600 hover:bg-red-700"
            >
              <Save className="w-4 h-4 mr-2" />
              {saving ? 'Saving...' : (articleId ? 'Update Article' : 'Create Article')}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

// Main Dashboard Component
const Dashboard = () => {
  const { user } = useContext(AuthContext);
  const location = useLocation();

  const sidebarItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Overview' },
    { path: '/dashboard/articles', icon: FileText, label: 'Articles' },
    { path: '/dashboard/create', icon: PlusCircle, label: 'Create Article' },
    { path: '/dashboard/analytics', icon: BarChart3, label: 'Analytics' },
    { path: '/dashboard/settings', icon: Settings, label: 'Settings' },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <div className="min-h-screen bg-slate-900 flex">
      {/* Sidebar */}
      <div className="dashboard-sidebar w-64 flex-shrink-0">
        <div className="p-6">
          <h2 className="text-xl font-bold text-white mb-6">Dashboard</h2>
          <p className="text-sm text-slate-400 mb-8">Welcome, {user?.username}</p>
        </div>
        <nav className="space-y-2">
          {sidebarItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`sidebar-item flex items-center space-x-3 ${isActive(item.path) ? 'active' : ''}`}
            >
              <item.icon className="w-5 h-5" />
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>
      </div>

      {/* Main Content */}
      <div className="dashboard-content flex-1 p-8">
        <Routes>
          <Route index element={<DashboardOverview />} />
          <Route path="articles" element={<ArticlesManager />} />
          <Route path="create" element={<ArticleEditor />} />
          <Route path="edit/:id" element={<ArticleEditor articleId={location.pathname.split('/').pop()} />} />
          <Route path="analytics" element={<div className="text-white">Analytics coming soon...</div>} />
          <Route path="settings" element={<div className="text-white">Settings coming soon...</div>} />
          <Route path="*" element={<Navigate to="/dashboard" />} />
        </Routes>
      </div>
    </div>
  );
};

export default Dashboard;