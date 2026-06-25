"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { IndianRupee, ShoppingCart, Users, Package } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

interface Metrics {
  total_revenue: number;
  total_orders: number;
  total_customers: number;
  total_products: number;
}

export default function AdminDashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const token = getToken();
        const res = await fetch(`${API_BASE_URL}/api/admin/metrics`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setMetrics(data);
        }
      } catch (error) {
        console.error("Failed to fetch metrics", error);
      } finally {
        setLoading(false);
      }
    };
    fetchMetrics();
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground mt-2">Overview of your store's performance.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard 
          title="Total Revenue" 
          value={metrics ? `₹${metrics.total_revenue.toFixed(2)}` : null} 
          icon={IndianRupee} 
          loading={loading} 
        />
        <MetricCard 
          title="Total Orders" 
          value={metrics?.total_orders.toString() ?? null} 
          icon={ShoppingCart} 
          loading={loading} 
        />
        <MetricCard 
          title="Total Customers" 
          value={metrics?.total_customers.toString() ?? null} 
          icon={Users} 
          loading={loading} 
        />
        <MetricCard 
          title="Total Products" 
          value={metrics?.total_products.toString() ?? null} 
          icon={Package} 
          loading={loading} 
        />
      </div>
    </div>
  );
}

function MetricCard({ title, value, icon: Icon, loading }: { title: string, value: string | null, icon: any, loading: boolean }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <Icon className="w-4 h-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-8 w-24" />
        ) : (
          <div className="text-2xl font-bold">{value}</div>
        )}
      </CardContent>
    </Card>
  );
}
