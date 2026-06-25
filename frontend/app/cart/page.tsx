"use client";

import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Trash2, ShoppingCart, Plus, Minus, ArrowRight, Package, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useCart } from "@/lib/cart";
import { toast } from "sonner";
import { useState } from "react";

const WHOLESALE_MIN_QTY = 50; // same fallback used for display; real logic is in cart API

export default function CartPage() {
  const { cart, isLoading, updateQuantity, removeItem, itemCount } = useCart();
  const [updatingItems, setUpdatingItems] = useState<Set<number>>(new Set());

  const handleUpdate = async (itemId: number, newQty: number) => {
    setUpdatingItems((prev) => new Set(prev).add(itemId));
    try {
      await updateQuantity(itemId, newQty);
    } catch (err: any) {
      toast.error(err.message || "Failed to update quantity");
    } finally {
      setUpdatingItems((prev) => {
        const next = new Set(prev);
        next.delete(itemId);
        return next;
      });
    }
  };

  const handleRemove = async (itemId: number, name: string) => {
    try {
      await removeItem(itemId);
      toast.success(`${name} removed from cart`);
    } catch (err: any) {
      toast.error(err.message || "Failed to remove item");
    }
  };

  const items = cart?.items ?? [];
  const subtotal = cart?.subtotal ?? 0;
  const shipping = 100; // flat-rate placeholder (replaced in Phase 5)
  const total = subtotal + shipping;

  // ─── Loading ──────────────────────────────────────────────────────────────
  if (isLoading && !cart) {
    return (
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-8">Shopping Cart</h1>
        <div className="flex flex-col lg:flex-row gap-8">
          <div className="flex-[2] space-y-4">
            {[1, 2].map((i) => (
              <Card key={i}>
                <CardContent className="p-4 flex gap-4">
                  <Skeleton className="w-24 h-24 rounded-lg shrink-0" />
                  <div className="flex-1 space-y-3">
                    <Skeleton className="h-5 w-3/4" />
                    <Skeleton className="h-4 w-1/3" />
                    <Skeleton className="h-8 w-28" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          <div className="flex-1">
            <Card>
              <CardContent className="p-6 space-y-4">
                <Skeleton className="h-6 w-1/3" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-12 w-full mt-4" />
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  // ─── Empty cart ───────────────────────────────────────────────────────────
  if (items.length === 0) {
    return (
      <div className="container mx-auto px-4 py-24 flex flex-col items-center justify-center text-center">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", bounce: 0.5 }}
          className="bg-muted p-6 rounded-full mb-6"
        >
          <ShoppingCart className="w-16 h-16 text-muted-foreground" />
        </motion.div>
        <h2 className="text-2xl font-bold mb-3">Your cart is empty</h2>
        <p className="text-muted-foreground mb-8 max-w-sm">
          Add some products to get started. Browse our full catalog of UPVC pipes and fittings.
        </p>
        <Button size="lg" >
          <Link href="/search">Browse Products</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 mb-4">
      <h1 className="text-3xl font-bold mb-8">
        Shopping Cart{" "}
        <span className="text-lg font-normal text-muted-foreground">
          ({itemCount} item{itemCount !== 1 ? "s" : ""})
        </span>
      </h1>

      <div className="flex flex-col lg:flex-row gap-8">

        {/* ─── Cart Items ──────────────────────────────────────────────── */}
        <div className="flex-[2] space-y-4">
          <AnimatePresence mode="popLayout">
            {items.map((item) => {
              const isWholesale =
                item.unit_price < (item.variant as any)?.mrp &&
                item.quantity >= WHOLESALE_MIN_QTY;
              const isUpdating = updatingItems.has(item.id);

              return (
                <motion.div
                  key={item.id}
                  layout
                  initial={{ opacity: 0, scale: 0.96 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.96, transition: { duration: 0.18 } }}
                >
                  <Card className={isUpdating ? "opacity-70 pointer-events-none" : ""}>
                    <CardContent className="p-4 sm:p-5 flex gap-4">
                      {/* Image */}
                      <div className="w-20 h-20 sm:w-24 sm:h-24 shrink-0 bg-muted rounded-lg overflow-hidden">
                        {item.product?.primary_image ? (
                          <img
                            src={item.product.primary_image}
                            alt={item.product.name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <Package className="w-8 h-8 text-primary/20" />
                          </div>
                        )}
                      </div>

                      <div className="flex-1 flex flex-col justify-between min-w-0">
                        <div className="flex justify-between items-start gap-2">
                          <div className="min-w-0">
                            <h3 className="font-semibold line-clamp-1">
                              {item.product?.name ?? "Product"}
                            </h3>
                            <p className="text-sm text-muted-foreground">
                              {item.variant?.size_label ?? item.variant?.sku}
                            </p>
                            {isWholesale && (
                              <Badge className="mt-1 bg-accent text-accent-foreground text-[10px] font-bold">
                                Wholesale Pricing
                              </Badge>
                            )}
                          </div>
                          <p className="font-bold whitespace-nowrap shrink-0">
                            ₹{item.total_price.toFixed(2)}
                          </p>
                        </div>

                        <div className="flex items-center justify-between mt-3">
                          {/* Quantity stepper */}
                          <div className="flex items-center border rounded-lg bg-background overflow-hidden">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 rounded-none"
                              onClick={() => handleUpdate(item.id, item.quantity - 1)}
                              disabled={isUpdating}
                            >
                              <Minus className="w-3 h-3" />
                            </Button>
                            <span className="w-8 text-center text-sm font-semibold">
                              {isUpdating ? <Loader2 className="w-3 h-3 animate-spin mx-auto" /> : item.quantity}
                            </span>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 rounded-none"
                              onClick={() => handleUpdate(item.id, item.quantity + 1)}
                              disabled={isUpdating}
                            >
                              <Plus className="w-3 h-3" />
                            </Button>
                          </div>

                          <p className="text-xs text-muted-foreground hidden sm:block">
                            ₹{item.unit_price.toFixed(2)} / unit
                          </p>

                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-destructive hover:text-destructive hover:bg-destructive/10"
                            onClick={() => handleRemove(item.id, item.product?.name ?? "Item")}
                            disabled={isUpdating}
                          >
                            <Trash2 className="w-4 h-4 sm:mr-1.5" />
                            <span className="hidden sm:inline">Remove</span>
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>

        {/* ─── Order Summary ───────────────────────────────────────────── */}
        <div className="flex-1">
          <Card className="sticky top-24">
            <CardContent className="p-6">
              <h2 className="text-xl font-bold mb-6">Order Summary</h2>

              <div className="space-y-3 text-sm mb-6">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Subtotal</span>
                  <span className="font-medium">₹{subtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Shipping</span>
                  <span className="font-medium text-muted-foreground">Calculated at checkout</span>
                </div>

                <div className="border-t pt-3 mt-3">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-base">Estimated Total</span>
                    <span className="font-bold text-xl text-primary">₹{subtotal.toFixed(2)}</span>
                  </div>
                </div>
              </div>

              <Button size="lg" className="w-full" >
                <Link href="/checkout" className="flex items-center justify-center gap-2">
                  Proceed to Checkout <ArrowRight className="w-4 h-4" />
                </Link>
              </Button>

              <Button variant="ghost" size="sm" className="w-full mt-3 text-muted-foreground" >
                <Link href="/search">← Continue Shopping</Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
