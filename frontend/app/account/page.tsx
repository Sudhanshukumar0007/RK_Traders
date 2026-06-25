"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { User, Package, MapPin, LogOut, Tag, Loader2, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { getMe, logout, isAuthenticated, type AuthUser } from "@/lib/auth";
import { client } from "@/lib/api";
import { useCart } from "@/lib/cart";

interface Order {
  id: number;
  order_number: string;
  status: string;
  total: number;
  created_at: string;
  items_count?: number;
}

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  confirmed: "bg-blue-100 text-blue-800",
  processing: "bg-indigo-100 text-indigo-800",
  shipped: "bg-purple-100 text-purple-800",
  delivered: "bg-green-100 text-green-800",
  cancelled: "bg-red-100 text-red-800",
};

export default function AccountPage() {
  const router = useRouter();
  const { clearCart, refreshCart } = useCart();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [recentOrders, setRecentOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    async function load() {
      try {
        const [me, ordersRes] = await Promise.all([
          getMe(),
          client.GET("/api/orders", { params: { query: { limit: 3 } } }),
        ]);
        setUser(me);
        if (ordersRes.data) setRecentOrders((ordersRes.data as any).items || ordersRes.data || []);
      } catch {
        logout();
        router.replace("/login");
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [router]);

  const handleLogout = async () => {
    logout();
    clearCart();
    await refreshCart();
    router.push("/");
  };

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <Skeleton className="h-9 w-48 mb-8" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <Skeleton className="h-48 rounded-xl" />
          <div className="md:col-span-2 space-y-4">
            <Skeleton className="h-6 w-32" />
            <div className="grid grid-cols-2 gap-4">
              <Skeleton className="h-28 rounded-xl" />
              <Skeleton className="h-28 rounded-xl" />
            </div>
            <Skeleton className="h-6 w-32 mt-4" />
            <Skeleton className="h-40 rounded-xl" />
          </div>
        </div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="container mx-auto px-4 py-8 mb-20 sm:mb-8 max-w-4xl">
      <h1 className="text-3xl font-bold mb-8">My Account</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">

        {/* ─── Sidebar ──────────────────────────────────────────────── */}
        <div className="md:col-span-1 space-y-4">
          <Card className="bg-muted/50">
            <CardContent className="p-6 flex flex-col items-center text-center">
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mb-4 text-primary"
              >
                <User className="w-10 h-10" />
              </motion.div>
              <h2 className="font-bold text-lg">{user.name}</h2>
              <p className="text-muted-foreground text-sm">{user.email}</p>
              {user.is_wholesale_customer && (
                <Badge className="mt-2 bg-accent text-accent-foreground text-xs">
                  <Tag className="w-3 h-3 mr-1" /> Wholesale Account
                </Badge>
              )}
              {user.phone && (
                <p className="text-sm text-muted-foreground mt-2">{user.phone}</p>
              )}
              <Button
                variant="outline"
                size="sm"
                className="mt-4 w-full text-destructive hover:text-destructive hover:bg-destructive/10"
                onClick={handleLogout}
              >
                <LogOut className="w-4 h-4 mr-2" />
                Sign Out
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* ─── Main Content ─────────────────────────────────────────── */}
        <div className="md:col-span-2 space-y-6">

          <h2 className="text-xl font-bold">Quick Links</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Link href="/account/orders">
              <Card className="hover:shadow-md transition-shadow h-full cursor-pointer group">
                <CardContent className="p-6 flex items-start gap-4">
                  <div className="bg-primary/10 p-3 rounded-lg text-primary shrink-0 group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                    <Package className="w-6 h-6" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold mb-1">My Orders</h3>
                    <p className="text-sm text-muted-foreground">View order history, track shipments.</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-muted-foreground mt-1 shrink-0" />
                </CardContent>
              </Card>
            </Link>
            <Link href="/account/addresses">
              <Card className="hover:shadow-md transition-shadow h-full cursor-pointer group">
                <CardContent className="p-6 flex items-start gap-4">
                  <div className="bg-primary/10 p-3 rounded-lg text-primary shrink-0 group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                    <MapPin className="w-6 h-6" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold mb-1">Saved Addresses</h3>
                    <p className="text-sm text-muted-foreground">Manage your delivery addresses.</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-muted-foreground mt-1 shrink-0" />
                </CardContent>
              </Card>
            </Link>
          </div>

          {/* Recent Orders */}
          <h2 className="text-xl font-bold pt-2">Recent Orders</h2>
          {recentOrders.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center text-muted-foreground">
                <Package className="w-10 h-10 mx-auto mb-3 text-muted-foreground/40" />
                <p>No orders yet.</p>
                <Button variant="outline" size="sm" className="mt-4" >
                  <Link href="/search">Start Shopping</Link>
                </Button>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="p-0">
                <div className="divide-y">
                  {recentOrders.map((order) => (
                    <div key={order.id} className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <p className="font-bold text-primary">{order.order_number}</p>
                        <p className="text-sm text-muted-foreground">
                          {new Date(order.created_at).toLocaleDateString("en-IN", {
                            day: "numeric", month: "short", year: "numeric",
                          })}
                        </p>
                        <p className="font-medium mt-1">₹{Number(order.total).toFixed(2)}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${STATUS_COLORS[order.status] ?? "bg-gray-100 text-gray-700"}`}>
                          {order.status}
                        </span>
                        <Button variant="outline" size="sm" >
                          <Link href={`/account/orders/${order.order_number}`}>View</Link>
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="p-4 bg-muted/50 text-center rounded-b-lg border-t">
                  <Link href="/account/orders" className="text-sm font-medium text-primary hover:underline">
                    View all orders →
                  </Link>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

      </div>
    </div>
  );
}
