import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { API_BASE_URL } from '../config/api';

export function TransactionTrends() {
  const [hourlyData, setHourlyData] = useState([]);
  const [regionalData, setRegionalData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTrendsData();
  }, []);

  const fetchTrendsData = async () => {
    try {
      setLoading(true);
      
      // Fetch volume data for hourly trends
      const volumeResponse = await fetch(`${API_BASE_URL}/volume`);
      const volumeData = await volumeResponse.json();
      
      // Fetch transactions for regional analysis
      const transactionsResponse = await fetch(`${API_BASE_URL}/transactions?limit=1000`);
      const transactionsData = await transactionsResponse.json();
      
      // Process hourly data from API
      if (volumeData.hourly && volumeData.hourly.length > 0) {
        const processedHourly = volumeData.hourly.map(item => ({
          hour: `${item.hour}:00`,
          transactions: item.volume,
          amount: item.volume * 156 // Simulate amount from volume
        }));
        setHourlyData(processedHourly);
      }
      
      // Process regional data from transactions
      const transactions = transactionsData.data || [];
      if (transactions.length > 0) {
        const regionCounts = {};
        transactions.forEach(t => {
          const region = t.region || 'Unknown';
          regionCounts[region] = (regionCounts[region] || 0) + 1;
        });
        
        const processedRegional = Object.entries(regionCounts).map(([region, count]) => ({
          region,
          transactions: count,
          percentage: ((count / transactions.length) * 100).toFixed(1)
        }));
        setRegionalData(processedRegional);
      }
      
    } catch (error) {
      console.error('Error fetching trends data:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    loading ? (
      <div className="p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="h-64 bg-gray-200 rounded-lg"></div>
            <div className="h-64 bg-gray-200 rounded-lg"></div>
          </div>
        </div>
      </div>
    ) : (
      <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Transaction Trends</h1>
        <p className="text-muted-foreground">
          Temporal and regional transaction dynamics analysis
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Hourly Transaction Volume</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={hourlyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis />
                <Tooltip />
                <Area 
                  type="monotone" 
                  dataKey="transactions" 
                  stroke="hsl(var(--primary))" 
                  fill="hsl(var(--primary))"
                  fillOpacity={0.3}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Regional Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={regionalData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="region" />
                <YAxis />
                <Tooltip />
                <Bar 
                  dataKey="transactions" 
                  fill="hsl(var(--chart-2))"
                />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Transaction Value Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center bg-muted/20 rounded-lg">
              <p className="text-muted-foreground">Box Plot Placeholder</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Peak Hours Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Morning Peak (8-10 AM)</span>
                <span className="text-sm text-muted-foreground">2,847 transactions</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Lunch Peak (12-2 PM)</span>
                <span className="text-sm text-muted-foreground">3,456 transactions</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Evening Peak (6-8 PM)</span>
                <span className="text-sm text-muted-foreground">4,123 transactions</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
    )
  );
}

