import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { API_BASE_URL } from '../config/api';
import { 
  Bot, 
  Send, 
  RefreshCw, 
  CheckCircle, 
  AlertTriangle, 
  Clock,
  TrendingUp,
  Package,
  DollarSign,
  Settings,
  Zap
} from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useFilterStore } from '../stores/filterStore';

const generateRetailBotResponse = (query, filters, model) => {
  // Simulate API response based on query and filters
  const actions = [
    {
      id: 'pricing-optimization',
      title: 'Optimize Pricing for Beverages Category',
      description: 'Analysis shows 15% price elasticity in beverages. Recommend 8% price increase on premium SKUs during peak hours (6-8 PM) to maximize revenue without significant volume loss.',
      confidence: 89,
      category: 'pricing',
      filters: { categories: ['Beverages'], hour: '18-20' }
    },
    {
      id: 'inventory-restock',
      title: 'Urgent Restock Alert: Coca-Cola 500ml',
      description: 'Current stock levels at 23% capacity. Based on historical demand patterns, recommend immediate restock of 2,500 units to prevent stockouts during weekend rush.',
      confidence: 94,
      category: 'inventory',
      filters: { brands: ['Coca-Cola'] }
    },
    {
      id: 'promotion-strategy',
      title: 'Cross-Category Bundle Promotion',
      description: 'Data indicates 67% of beverage buyers also purchase snacks. Launch "Combo Deal" promotion: Buy 2 beverages + 1 snack for 15% discount to increase basket size.',
      confidence: 82,
      category: 'promotion',
      filters: { categories: ['Beverages', 'Food & Snacks'] }
    },
    {
      id: 'operational-efficiency',
      title: 'Staff Scheduling Optimization',
      description: 'Peak transaction hours (6-8 PM) show 23% of daily volume but only 18% staff allocation. Recommend adding 2 additional staff members during this period.',
      confidence: 91,
      category: 'ops',
      filters: { hour: '18-20' }
    },
    {
      id: 'regional-expansion',
      title: 'Metro Manila Market Expansion',
      description: 'Beverages show 15% higher conversion in Metro Manila vs other regions. Consider opening 2 additional locations in Makati CBD and BGC areas.',
      confidence: 76,
      category: 'ops',
      filters: { barangays: ['Makati CBD', 'BGC'] }
    }
  ];

  // Filter actions based on current filters
  let relevantActions = [...actions];
  
  if (filters.categories.length > 0) {
    relevantActions = relevantActions.filter(action => 
      !action.filters.categories || 
      action.filters.categories.some(cat => filters.categories.includes(cat))
    );
  }

  if (filters.brands.length > 0) {
    relevantActions = relevantActions.filter(action => 
      !action.filters.brands || 
      action.filters.brands.some(brand => filters.brands.includes(brand))
    );
  }

  // Simulate different response times based on model
  const latency = model === 'gpt-4' ? 1200 : 800;
  
  return {
    actions: relevantActions.slice(0, 4),
    diagnostics: {
      data_quality: filters.categories.length > 0 || filters.brands.length > 0 ? 'good' : 'warn',
      latency_ms: latency,
      model_used: model,
      filters_applied: Object.keys(filters).filter(key => 
        Array.isArray(filters[key]) ? filters[key].length > 0 : filters[key]
      ).length
    }
  };
};

const getCategoryIcon = (category) => {
  switch (category) {
    case 'pricing': return DollarSign;
    case 'promotion': return TrendingUp;
    case 'inventory': return Package;
    case 'ops': return Settings;
    default: return Zap;
  }
};

const getCategoryColor = (category) => {
  switch (category) {
    case 'pricing': return 'bg-green-500';
    case 'promotion': return 'bg-blue-500';
    case 'inventory': return 'bg-orange-500';
    case 'ops': return 'bg-purple-500';
    default: return 'bg-gray-500';
  }
};

export function RetailBotInsights() {
  const navigate = useNavigate();
  const filters = useFilterStore();
  const { setFilter, getQueryString } = useFilterStore();
  
  const [query, setQuery] = useState('');
  const [selectedModel, setSelectedModel] = useState('gpt-4');
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);

  const handleSendQuery = async () => {
    if (!query.trim()) return;

    setIsLoading(true);
    
    // Add user message to chat history
    const userMessage = {
      type: 'user',
      content: query,
      timestamp: new Date()
    };
    
    setChatHistory(prev => [...prev, userMessage]);

    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, selectedModel === 'gpt-4' ? 1200 : 800));
    
    const botResponse = generateRetailBotResponse(query, filters, selectedModel);
    setResponse(botResponse);
    
    // Add bot response to chat history
    const botMessage = {
      type: 'bot',
      content: `I've analyzed your query "${query}" and generated ${botResponse.actions.length} actionable recommendations based on your current filters.`,
      timestamp: new Date(),
      response: botResponse
    };
    
    setChatHistory(prev => [...prev, botMessage]);
    setQuery('');
    setIsLoading(false);
  };

  const handleApplyAction = (action) => {
    // Apply filters from the action
    if (action.filters) {
      Object.entries(action.filters).forEach(([key, value]) => {
        setFilter(key, value);
      });
    }
    
    // Navigate to appropriate page based on action category
    switch (action.category) {
      case 'pricing':
      case 'promotion':
        navigate(`/products?${getQueryString()}`);
        break;
      case 'inventory':
        navigate(`/products?${getQueryString()}`);
        break;
      case 'ops':
        navigate(`/trends?${getQueryString()}`);
        break;
      default:
        navigate(`/?${getQueryString()}`);
    }
  };

  const handleRefresh = () => {
    if (chatHistory.length > 0) {
      const lastUserQuery = chatHistory.filter(msg => msg.type === 'user').pop();
      if (lastUserQuery) {
        setQuery(lastUserQuery.content);
        handleSendQuery();
      }
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground flex items-center space-x-3">
            <Bot className="h-8 w-8 text-primary" />
            <span>RetailBot & AdBot</span>
          </h1>
          <p className="text-muted-foreground mt-2">
            AI-powered retail intelligence assistant for actionable insights and recommendations
          </p>
        </div>
        
        <div className="flex items-center space-x-4">
          <Select value={selectedModel} onValueChange={setSelectedModel}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="gpt-4">GPT-4</SelectItem>
              <SelectItem value="gpt-3.5">GPT-3.5</SelectItem>
            </SelectContent>
          </Select>
          
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isLoading || chatHistory.length === 0}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chat Interface */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Chat with RetailBot</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Chat History */}
              <div className="h-64 overflow-y-auto border rounded-lg p-4 space-y-3 bg-muted/20">
                {chatHistory.length === 0 ? (
                  <div className="text-center text-muted-foreground py-8">
                    <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Ask RetailBot anything about your retail data!</p>
                    <p className="text-sm mt-2">Try: "Which products are underperforming?" or "How can I optimize inventory?"</p>
                  </div>
                ) : (
                  chatHistory.map((message, index) => (
                    <div key={index} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[80%] p-3 rounded-lg ${
                        message.type === 'user' 
                          ? 'bg-primary text-primary-foreground' 
                          : 'bg-background border'
                      }`}>
                        <p className="text-sm">{message.content}</p>
                        <p className="text-xs opacity-70 mt-1">
                          {message.timestamp.toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  ))
                )}
                
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-background border p-3 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                        <span className="text-sm">RetailBot is thinking...</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Chat Input */}
              <div className="flex space-x-2">
                <Textarea
                  placeholder="Ask RetailBot about your retail data... (e.g., 'Which SKUs are underperforming this week?')"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendQuery();
                    }
                  }}
                  className="flex-1"
                  rows={2}
                />
                <Button 
                  onClick={handleSendQuery} 
                  disabled={isLoading || !query.trim()}
                  className="px-4"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Action Cards */}
          {response && response.actions.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Recommended Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {response.actions.map((action) => {
                    const IconComponent = getCategoryIcon(action.category);
                    return (
                      <div key={action.id} className="border rounded-lg p-4 space-y-3">
                        <div className="flex items-start justify-between">
                          <div className="flex items-center space-x-3">
                            <div className={`p-2 rounded-lg ${getCategoryColor(action.category)}`}>
                              <IconComponent className="h-4 w-4 text-white" />
                            </div>
                            <div>
                              <h3 className="font-semibold text-foreground">{action.title}</h3>
                              <Badge variant="outline" className="mt-1">
                                {action.category}
                              </Badge>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className="text-xs text-muted-foreground">Confidence:</span>
                            <div className="flex items-center space-x-1">
                              <div className="w-16 h-2 bg-muted rounded-full overflow-hidden">
                                <div 
                                  className="h-full bg-green-500 transition-all duration-300"
                                  style={{ width: `${action.confidence}%` }}
                                />
                              </div>
                              <span className="text-xs font-medium">{action.confidence}%</span>
                            </div>
                          </div>
                        </div>
                        
                        <p className="text-sm text-muted-foreground leading-relaxed">
                          {action.description}
                        </p>
                        
                        <div className="flex justify-end">
                          <Button 
                            size="sm" 
                            onClick={() => handleApplyAction(action)}
                            className="flex items-center space-x-2"
                          >
                            <CheckCircle className="h-4 w-4" />
                            <span>Apply Action</span>
                          </Button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Diagnostics Panel */}
        <div className="space-y-4">
          {response && (
            <Card>
              <CardHeader>
                <CardTitle>Diagnostics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Data Quality</span>
                    <div className="flex items-center space-x-2">
                      {response.diagnostics.data_quality === 'good' ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <AlertTriangle className="h-4 w-4 text-yellow-500" />
                      )}
                      <Badge variant={response.diagnostics.data_quality === 'good' ? 'default' : 'secondary'}>
                        {response.diagnostics.data_quality}
                      </Badge>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Response Time</span>
                    <div className="flex items-center space-x-2">
                      <Clock className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">{response.diagnostics.latency_ms}ms</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Model Used</span>
                    <Badge variant="outline">{response.diagnostics.model_used}</Badge>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Filters Applied</span>
                    <span className="text-sm">{response.diagnostics.filters_applied}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Queries</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {[
                  'Which products are underperforming this week?',
                  'How can I optimize inventory levels?',
                  'What are the best promotion opportunities?',
                  'Which regions need more attention?'
                ].map((quickQuery, index) => (
                  <Button
                    key={index}
                    variant="ghost"
                    size="sm"
                    className="w-full justify-start text-left h-auto p-3"
                    onClick={() => setQuery(quickQuery)}
                  >
                    <span className="text-sm">{quickQuery}</span>
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

