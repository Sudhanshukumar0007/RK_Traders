"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, ExternalLink, Package, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { isAuthenticated } from "@/lib/auth";
import { client } from "@/lib/api";

interface Order {
  id: number;
  order_number: string;
  status: string;
  total: number;
  created_at: string;
  items?: any[];
}

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  confirmed: "bg-blue-100 text-blue-800",
  processing: "bg-indigo-100 text-indigo-800",
  shipped: "bg-purple-100 text-purple-800",
  delivered: "bg-green-100 text-green-800",
  cancelled: "bg-red-100 text-red-800",
};

export default function OrdersPage() {
  const router = useRouter();
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const LIMIT = 10;

  useEffect(() => {
    if (!isAuthenticated()) { router.replace("/login"); return; }
    async function load() {
      setIsLoading(true);
      try {
        const { data } = await client.GET("/api/orders", {
          params: { query: { limit: LIMIT, offset: (page - 1) * LIMIT } },
        });
        if (data) {
          const list = (data as any).items || data || [];
          const tot = (data as any).total || list.length;
          setOrders(list);
          setTotal(tot);
        }
      } catch (e) {
        console.error("Failed to load orders", e);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [page, router]);

  const totalPages = Math.ceil(total / LIMIT);

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl mb-20 sm:mb-8">
      <div className="mb-8">
        <Button variant="ghost" size="sm" className="mb-4 -ml-2 text-muted-foreground" >
          <Link href="/account"><ArrowLeft className="w-4 h-4 mr-2" />Back to Account</Link>
        </Button>
        <h1 className="text-3xl font-bold">My Orders</h1>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardContent className="p-5">
                <div className="flex justify-between items-center">
                  <div className="space-y-2">
                    <Skeleton className="h-5 w-40" />
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-4 w-24" />
                  </div>
                  <div className="space-y-2">
                    <Skeleton className="h-6 w-20 rounded-full" />
                    <Skeleton className="h-8 w-24 rounded" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : orders.length === 0 ? (
        <div className="py-24 text-center">
          <Package className="w-12 h-12 mx-auto mb-4 text-muted-foreground/40" />
          <h2 className="text-xl font-bold mb-2">No orders yet</h2>
          <p className="text-muted-foreground mb-6">You haven't placed any orders yet.</p>
          <Button ><Link href="/search">Start Shopping</Link></Button>
        </div>
      ) : (
        <>
          <div className="space-y-4">
            {orders.map((order) => (
              <Card key={order.id}>
                <CardContent className="p-0">
                  <div className="p-4 sm:p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-3 mb-1 flex-wrap">
                        <p className="font-bold text-primary">{order.order_number}</p>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-medium uppercase tracking-wider ${STATUS_COLORS[order.status] ?? "bg-gray-100 text-gray-700"}`}>
                          {order.status}
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {new Date(order.created_at).toLocaleDateString("en-IN", {
                          day: "numeric", month: "long", year: "numeric",
                        })}
                      </p>
                      <p className="font-medium mt-2">₹{Number(order.total).toFixed(2)}</p>
                    </div>
                    <div className="flex flex-col sm:items-end gap-2">
                      <Button variant="outline" size="sm" >
                        <Link href={`/account/orders/${order.order_number}`}>View Details</Link>
                      </Button>
                      {order.status === "shipped" && (
                        <Button variant="ghost" size="sm" className="text-primary hover:text-primary" >
                          <Link href={`/account/orders/${order.order_number}`}>
                            <ExternalLink className="w-4 h-4 mr-2" /> Track Shipment
                          </Link>
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-3 mt-8">
              <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}>
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">Page {page} of {totalPages}</span>
              <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages}>
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
