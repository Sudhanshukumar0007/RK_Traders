"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowLeft, MapPin, CreditCard, Receipt, Truck, Package, Check, Clock, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { isAuthenticated } from "@/lib/auth";
import { client } from "@/lib/api";

interface OrderItem {
  id: number;
  variant_id: number;
  quantity: number;
  unit_price: number;
  total_price: number;
  variant?: { sku: string; size_label: string };
  product?: { name: string; slug: string; primary_image?: string };
}

interface ShippingAddress {
  full_address: string;
  city: string;
  state: string;
  pincode: string;
  phone: string;
}

interface OrderDetail {
  id: number;
  order_number: string;
  status: string;
  payment_status: string;
  subtotal: number;
  shipping_cost: number;
  total: number;
  created_at: string;
  items: OrderItem[];
  shipping_address?: ShippingAddress;
  awb_code?: string;
  courier_name?: string;
  tracking_status?: string;
  estimated_delivery?: string;
}

const ORDER_TIMELINE = [
  { status: "pending", label: "Order Placed", icon: Clock },
  { status: "confirmed", label: "Confirmed", icon: Check },
  { status: "processing", label: "Processing", icon: Package },
  { status: "shipped", label: "Shipped", icon: Truck },
  { status: "delivered", label: "Delivered", icon: Check },
];

const STATUS_ORDER = ["pending", "confirmed", "processing", "shipped", "delivered"];

const PAYMENT_COLORS: Record<string, string> = {
  paid: "bg-green-100 text-green-800",
  pending: "bg-yellow-100 text-yellow-800",
  failed: "bg-red-100 text-red-800",
  refunded: "bg-gray-100 text-gray-700",
};

export default function OrderDetailsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAuthenticated()) { router.replace("/login"); return; }
    async function load() {
      try {
        const { data, error: apiErr } = await client.GET("/api/orders/{order_number}", {
          params: { path: { order_number: id } },
        });
        if (apiErr || !data) throw new Error("Order not found");
        setOrder(data as OrderDetail);
      } catch (e: any) {
        setError(e.message || "Failed to load order");
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [id, router]);

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <Skeleton className="h-8 w-28 mb-6" />
        <Skeleton className="h-9 w-64 mb-2" />
        <Skeleton className="h-5 w-48 mb-8" />
        <div className="grid grid-cols-3 gap-4 mb-8">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-32 rounded-xl" />)}
        </div>
        <Skeleton className="h-64 rounded-xl" />
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="container mx-auto px-4 py-24 text-center">
        <AlertCircle className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
        <h1 className="text-xl font-bold mb-2">Order not found</h1>
        <p className="text-muted-foreground mb-6">{error}</p>
        <Link href="/account/orders"><Button>Back to Orders</Button></Link>
      </div>
    );
  }

  const currentStatusIdx = STATUS_ORDER.indexOf(order.status);

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl mb-20 sm:mb-8">
      <div className="mb-8">
        <Link href="/account/orders">
          <Button variant="ghost" size="sm" className="mb-4 -ml-2 text-muted-foreground">
            <ArrowLeft className="w-4 h-4 mr-2" />Back to Orders
          </Button>
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold mb-1">Order {order.order_number}</h1>
            <p className="text-muted-foreground">
              Placed on{" "}
              {new Date(order.created_at).toLocaleDateString("en-IN", {
                day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit",
              })}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge className={PAYMENT_COLORS[order.payment_status] ?? "bg-gray-100 text-gray-700"}>
              Payment: {order.payment_status}
            </Badge>
            <Button variant="outline" size="sm">
              <Receipt className="w-4 h-4 mr-2" /> Download Invoice
            </Button>
          </div>
        </div>
      </div>

      {/* ─── Status Timeline ─────────────────────────────────────────── */}
      {order.status !== "cancelled" && (
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="flex items-center justify-between relative">
              {/* Progress line */}
              <div className="absolute left-0 right-0 top-5 h-0.5 bg-border z-0 mx-10" />
              <motion.div
                className="absolute left-0 top-5 h-0.5 bg-primary z-0 mx-10"
                style={{ right: `${((ORDER_TIMELINE.length - 1 - Math.max(0, currentStatusIdx)) / (ORDER_TIMELINE.length - 1)) * 100}%` }}
                initial={{ scaleX: 0 }}
                animate={{ scaleX: 1 }}
                transition={{ duration: 0.8, ease: "easeOut" }}
              />

              {ORDER_TIMELINE.map((step, i) => {
                const isDone = i <= currentStatusIdx;
                const isCurrent = i === currentStatusIdx;
                const Icon = step.icon;
                return (
                  <div key={step.status} className="flex flex-col items-center gap-2 z-10 flex-1">
                    <motion.div
                      initial={{ scale: 0.6, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ delay: i * 0.1 }}
                      className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all ${
                        isDone
                          ? "bg-primary border-primary text-primary-foreground"
                          : "bg-background border-border text-muted-foreground"
                      } ${isCurrent ? "ring-4 ring-primary/20" : ""}`}
                    >
                      <Icon className="w-4 h-4" />
                    </motion.div>
                    <span className={`text-[10px] sm:text-xs font-medium text-center ${isDone ? "text-primary" : "text-muted-foreground"}`}>
                      {step.label}
                    </span>
                  </div>
                );
              })}
            </div>

            {order.awb_code && (
              <div className="mt-6 pt-4 border-t flex flex-wrap items-center justify-between gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Tracking Number</p>
                  <p className="font-mono font-bold text-primary">{order.awb_code}</p>
                  {order.courier_name && <p className="text-sm text-muted-foreground">via {order.courier_name}</p>}
                </div>
                {order.estimated_delivery && (
                  <div>
                    <p className="text-sm text-muted-foreground">Expected Delivery</p>
                    <p className="font-semibold">{order.estimated_delivery}</p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* ─── Info Cards ──────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {order.shipping_address && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <MapPin className="w-4 h-4 text-primary" /> Shipping Address
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground space-y-1">
              <p>{order.shipping_address.full_address}</p>
              <p>{order.shipping_address.city}, {order.shipping_address.state} — {order.shipping_address.pincode}</p>
              <p className="pt-1">Phone: {order.shipping_address.phone}</p>
            </CardContent>
          </Card>
        )}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <CreditCard className="w-4 h-4 text-primary" /> Payment
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground space-y-1">
            <p className="font-medium text-foreground capitalize">{order.payment_status}</p>
            <p>Razorpay (UPI / Cards / Net Banking)</p>
          </CardContent>
        </Card>
      </div>

      {/* ─── Order Items ─────────────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle>Order Items ({order.items.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4 mb-6 divide-y">
            {order.items.map((item) => (
              <div key={item.id} className="flex flex-col sm:flex-row sm:items-center gap-4 pt-4 first:pt-0">
                <div className="w-16 h-16 sm:w-20 sm:h-20 bg-muted rounded-lg overflow-hidden shrink-0">
                  {item.product?.primary_image ? (
                    <img src={item.product.primary_image} alt={item.product.name} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <Package className="w-6 h-6 text-primary/20" />
                    </div>
                  )}
                </div>
                <div className="flex-1 flex flex-col sm:flex-row justify-between sm:items-center gap-2">
                  <div>
                    <Link href={`/product/${item.product?.slug ?? ""}`} className="font-bold text-base hover:text-primary transition-colors">
                      {item.product?.name ?? "Product"}
                    </Link>
                    <p className="text-sm text-muted-foreground">{item.variant?.size_label ?? item.variant?.sku}</p>
                  </div>
                  <div className="flex items-center sm:flex-col sm:items-end justify-between sm:justify-start gap-2">
                    <p className="text-sm text-muted-foreground">Qty: {item.quantity} × ₹{Number(item.unit_price).toFixed(2)}</p>
                    <p className="font-bold">₹{Number(item.total_price).toFixed(2)}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-end">
            <div className="w-full sm:w-64 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Subtotal</span>
                <span>₹{Number(order.subtotal).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Shipping</span>
                <span>₹{Number(order.shipping_cost).toFixed(2)}</span>
              </div>
              <div className="border-t pt-2 mt-2 flex justify-between items-center">
                <span className="font-bold text-base">Total</span>
                <span className="font-bold text-xl text-primary">₹{Number(order.total).toFixed(2)}</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
