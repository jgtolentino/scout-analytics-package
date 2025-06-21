import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { API_BASE_URL } from '../config/api';

export default function ProductMix() {
  const [loading, setLoading] = useState(true);
  const [categories, setCategories] = useState([]);
  const [productPerformance, setProductPerformance] = useState([]);
  const [substitutions, setSubstitutions] = useState([]);

  useEffect(() => {
    fetchProductData();
  }, []);

  const fetchProductData = async () => {
    try {
      setLoading(true);
      
      // Fetch products data
      const productsResponse = await fetch(`${API_BASE_URL}/products`);
      const productsData = await productsResponse.json();
      
      // Fetch substitutions data
      const substitutionsResponse = await fetch(`${API_BASE_URL}/substitutions`);
      const substitutionsData = await substitutionsResponse.json();
      
      // Process categories from products data
      if (productsData.data && productsData.data.length > 0) {
        const categoryMap = {};
        productsData.data.forEach(product => {
          const category = product.category || 'Others';
          if (!categoryMap[category]) {
            categoryMap[category] = { count: 0, revenue: 0 };
          }
          categoryMap[category].count++;
          categoryMap[category].revenue += product.price * 100; // Simulate revenue
        });
        
        const totalProducts = productsData.data.length;
        const processedCategories = Object.entries(categoryMap).map(([name, data], index) => ({
          name,
          share: ((data.count / totalProducts) * 100).toFixed(1),
          revenue: data.revenue,
          color: ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00'][index % 5]
        }));
        setCategories(processedCategories);
        
        // Set top products
        const topProducts = productsData.data.slice(0, 5).map(product => ({
          name: product.name,
          revenue: product.price * 100,
          units: Math.floor(Math.random() * 2000) + 500
        }));
        setProductPerformance(topProducts);
      }
      
      // Process substitutions data
      if (substitutionsData.data && substitutionsData.data.length > 0) {
        setSubstitutions(substitutionsData.data.slice(0, 10));
      }
      
    } catch (error) {
      console.error('Error fetching product data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="h-64 bg-gray-200 rounded-lg"></div>
            <div className="h-64 bg-gray-200 rounded-lg"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Product Mix Analysis</h1>
        <p className="text-muted-foreground">
          Category share and SKU substitution patterns
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Category Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={categories}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, share }) => `${name}: ${share}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="share"
                >
                  {categories.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Product Performance (Pareto)</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={productPerformance}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="revenue" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Brand Substitution Flow</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center text-muted-foreground">
              Sankey Diagram Placeholder
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Category Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {categories.map((category, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div 
                      className="w-4 h-4 rounded-full" 
                      style={{ backgroundColor: category.color }}
                    ></div>
                    <span className="font-medium">{category.name}</span>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold">{category.share}%</div>
                    <div className="text-sm text-muted-foreground">
                      ₱{category.revenue.toLocaleString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {substitutions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Top Substitutions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {substitutions.slice(0, 3).map((sub, index) => (
                <div key={index} className="flex justify-between items-center">
                  <span>{sub.original_product} → {sub.substitute_product}</span>
                  <span className="text-muted-foreground">{sub.count || 'N/A'} switches</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

