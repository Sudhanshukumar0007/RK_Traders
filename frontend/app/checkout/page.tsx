"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import Script from "next/script";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  CheckCircle2, Lock, ChevronRight, Loader2, MapPin, Package, CreditCard, AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useCart } from "@/lib/cart";
import { isAuthenticated, getToken } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/api";

const addressSchema = z.object({
  name: z.string().min(2, "Name required"),
  phone: z.string().regex(/^[6-9]\d{9}$/, "Enter valid 10-digit mobile"),
  full_address: z.string().min(5, "Enter full address"),
  city: z.string().min(2, "City required"),
  state: z.string().min(2, "State required"),
  pincode: z.string().regex(/^\d{6}$/, "Enter valid 6-digit pincode"),
});

type AddressForm = z.infer<typeof addressSchema>;

type Step = "address" | "review" | "payment" | "success";

interface ShippingQuote {
  courier_name: string;
  rate: number;
  estimated_days: string;
  service_name: string;
}

export default function CheckoutPage() {
  const router = useRouter();
  const { cart, isLoading: cartLoading, clearCart, refreshCart } = useCart();
  const [step, setStep] = useState<Step>("address");
  const [addressData, setAddressData] = useState<AddressForm | null>(null);
  const [shippingQuotes, setShippingQuotes] = useState<ShippingQuote[]>([]);
  const [selectedShipping, setSelectedShipping] = useState<ShippingQuote | null>(null);
  const [quotesLoading, setQuotesLoading] = useState(false);
  const [orderNumber, setOrderNumber] = useState("");
  const [isPlacing, setIsPlacing] = useState(false);
  const [placeError, setPlaceError] = useState("");

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<AddressForm>({ resolver: zodResolver(addressSchema) });

  const pincode = watch("pincode");

  // ─── Auth guard ───────────────────────────────────────────────────────────
  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login?next=/checkout");
    }
  }, [router]);

  // ─── Fetch shipping quotes when pincode is valid ───────────────────────────
  useEffect(() => {
    if (!pincode || !/^\d{6}$/.test(pincode) || !cart) return;
    let cancelled = false;
    setQuotesLoading(true);

    async function fetchQuotes() {
      try {
        const token = getToken();
        const res = await fetch(`${API_BASE_URL}/api/shipping/quote`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          credentials: "include",
          body: JSON.stringify({ pincode, cart_id: cart?.id }),
        });
        if (!cancelled && res.ok) {
          const data = await res.json();
          setShippingQuotes(data.quotes || data || []);
          // Auto-select cheapest
          const cheapest = (data.quotes || data || []).sort((a: ShippingQuote, b: ShippingQuote) => a.rate - b.rate)[0];
          if (cheapest) setSelectedShipping(cheapest);
        }
      } catch {
        // Shipping service not available; use flat-rate fallback
        if (!cancelled) {
          const fallback: ShippingQuote = {
            courier_name: "Standard Delivery",
            rate: 100,
            estimated_days: "3–5 business days",
            service_name: "Standard",
          };
          setShippingQuotes([fallback]);
          setSelectedShipping(fallback);
        }
      } finally {
        if (!cancelled) setQuotesLoading(false);
      }
    }
    fetchQuotes();
    return () => { cancelled = true; };
  }, [pincode, cart]);

  // ─── Submit address, go to review ─────────────────────────────────────────
  const onAddressSubmit = (data: AddressForm) => {
    setAddressData(data);
    setStep("review");
  };

  // ─── Place order ──────────────────────────────────────────────────────────
  const handlePlaceOrder = async () => {
    if (!addressData || !cart) return;
    setIsPlacing(true);
    setPlaceError("");

    try {
      const token = getToken();
      
      // 1. Create or get Address
      const addressRes = await fetch(`${API_BASE_URL}/api/addresses`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          label: "Delivery",
          full_address: addressData.full_address,
          city: addressData.city,
          state: addressData.state,
          pincode: addressData.pincode,
          phone: addressData.phone,
          is_default: false,
        }),
      });
      
      if (!addressRes.ok) throw new Error("Failed to save address");
      const savedAddress = await addressRes.json();

      // 2. Create Order
      const res = await fetch(`${API_BASE_URL}/api/orders`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
        body: JSON.stringify({
          shipping_address_id: savedAddress.id,
          shipping_cost: selectedShipping?.rate ?? 100,
          shipping_service: selectedShipping?.courier_name ?? "Standard",
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Order creation failed" }));
        throw new Error(err.detail || "Order creation failed");
      }

      const order = await res.json();
      
      // 3. Create Razorpay Order
      const rzpRes = await fetch(`${API_BASE_URL}/api/payments/${order.id}/create-razorpay-order`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        }
      });
      
      if (!rzpRes.ok) throw new Error("Failed to initialize payment");
      const rzpData = await rzpRes.json();
      
      // 4. Open Razorpay Checkout
      const options = {
        key: rzpData.key_id,
        amount: rzpData.amount,
        currency: rzpData.currency,
        name: "Supreme Hardware Store",
        description: `Order ${order.order_number}`,
        order_id: rzpData.razorpay_order_id,
        handler: async function (response: any) {
          // 5. Verify payment
          try {
            const verifyRes = await fetch(`${API_BASE_URL}/api/payments/${order.id}/verify`, {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
              },
              body: JSON.stringify({
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature
              })
            });
            
            if (!verifyRes.ok) {
              setPlaceError("Payment verification failed. If money was deducted, it will be refunded.");
              return;
            }
            
            setOrderNumber(order.order_number);
            await refreshCart();
            setStep("success");
          } catch (e: any) {
             setPlaceError("Payment verification error.");
          }
        },
        prefill: {
          name: addressData.name,
          contact: addressData.phone,
        },
        theme: {
          color: "#0f172a"
        }
      };
      
      const rzp = new (window as any).Razorpay(options);
      rzp.on('payment.failed', function (response: any){
        setPlaceError(response.error.description || "Payment failed");
      });
      rzp.open();

    } catch (err: any) {
      setPlaceError(err.message || "Something went wrong. Please try again.");
    } finally {
      setIsPlacing(false);
    }
  };

  const subtotal = cart?.subtotal ?? 0;
  const shippingCost = selectedShipping?.rate ?? 100;
  const total = subtotal + shippingCost;

  // ─── Loading ──────────────────────────────────────────────────────────────
  if (cartLoading && !cart) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-5xl">
        <Skeleton className="h-9 w-32 mb-8" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-4">
            <Skeleton className="h-64 rounded-xl" />
          </div>
          <Skeleton className="h-56 rounded-xl" />
        </div>
      </div>
    );
  }

  // ─── Empty cart ───────────────────────────────────────────────────────────
  if (!cartLoading && (!cart || cart.items.length === 0) && step !== "success") {
    return (
      <div className="container mx-auto px-4 py-24 text-center">
        <Package className="w-12 h-12 mx-auto mb-4 text-muted-foreground/40" />
        <h1 className="text-2xl font-bold mb-2">Your cart is empty</h1>
        <p className="text-muted-foreground mb-6">Add items to your cart before checking out.</p>
        <Link href="/search"><Button>Browse Products</Button></Link>
      </div>
    );
  }

  // ─── Success ──────────────────────────────────────────────────────────────
  if (step === "success") {
    return (
      <div className="container mx-auto px-4 py-24 flex flex-col items-center justify-center text-center max-w-md">
        <motion.div
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
        >
          <CheckCircle2 className="w-20 h-20 text-green-500 mb-6 mx-auto" />
          <h1 className="text-3xl font-bold mb-4">Order Confirmed!</h1>
          <p className="text-muted-foreground mb-8 text-lg">
            Thank you for your purchase. Your order number is <span className="font-bold text-foreground">{orderNumber}</span>.
          </p>
          <Button asChild size="lg" className="w-full">
            <Link href="/">Return to Home</Link>
          </Button>
        </motion.div>
      </div>
    );
  }

  if (!isAuthenticated()) return null;



  const steps: { key: Step; label: string; icon: React.ElementType }[] = [
    { key: "address", label: "Address", icon: MapPin },
    { key: "review", label: "Review", icon: Package },
    { key: "payment", label: "Payment", icon: CreditCard },
  ];
  const stepIndex = steps.findIndex((s) => s.key === step);

  return (
    <div className="container mx-auto px-4 py-8 mb-8 max-w-5xl">
      <Script src="https://checkout.razorpay.com/v1/checkout.js" strategy="lazyOnload" />
      <h1 className="text-3xl font-bold mb-8">Checkout</h1>

      {/* Step indicator */}
      <div className="flex items-center gap-0 mb-8 w-full max-w-sm">
        {steps.map((s, i) => (
          <div key={s.key} className="flex items-center">
            <div
              className={`flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold border-2 transition-all ${
                i < stepIndex
                  ? "bg-primary border-primary text-primary-foreground"
                  : i === stepIndex
                  ? "border-primary text-primary"
                  : "border-muted-foreground/30 text-muted-foreground"
              }`}
            >
              {i < stepIndex ? "✓" : i + 1}
            </div>
            <span className={`ml-2 text-sm font-medium hidden sm:inline ${i === stepIndex ? "text-primary" : "text-muted-foreground"}`}>
              {s.label}
            </span>
            {i < steps.length - 1 && (
              <div className={`w-8 sm:w-12 h-0.5 mx-2 ${i < stepIndex ? "bg-primary" : "bg-border"}`} />
            )}
          </div>
        ))}
      </div>

      <div className="flex flex-col lg:flex-row gap-8">

        {/* ─── Left: Steps ──────────────────────────────────────────── */}
        <div className="flex-[2] space-y-6">

          <AnimatePresence mode="wait">

            {/* STEP 1: Address */}
            {step === "address" && (
              <motion.div
                key="address"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.25 }}
              >
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <MapPin className="w-5 h-5 text-primary" /> Shipping Address
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <form onSubmit={handleSubmit(onAddressSubmit)} className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="name">Full Name</Label>
                          <Input id="name" placeholder="Ramesh Kumar" {...register("name")} className={errors.name ? "border-destructive" : ""} />
                          {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="phone">Mobile Number</Label>
                          <Input id="phone" type="tel" placeholder="9876543210" {...register("phone")} className={errors.phone ? "border-destructive" : ""} />
                          {errors.phone && <p className="text-xs text-destructive">{errors.phone.message}</p>}
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="full_address">Address</Label>
                        <Input id="full_address" placeholder="House / Flat No., Street, Area" {...register("full_address")} className={errors.full_address ? "border-destructive" : ""} />
                        {errors.full_address && <p className="text-xs text-destructive">{errors.full_address.message}</p>}
                      </div>
                      <div className="grid grid-cols-3 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="city">City</Label>
                          <Input id="city" placeholder="Mumbai" {...register("city")} className={errors.city ? "border-destructive" : ""} />
                          {errors.city && <p className="text-xs text-destructive">{errors.city.message}</p>}
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="state">State</Label>
                          <Input id="state" placeholder="Maharashtra" {...register("state")} className={errors.state ? "border-destructive" : ""} />
                          {errors.state && <p className="text-xs text-destructive">{errors.state.message}</p>}
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="pincode">Pincode</Label>
                          <Input id="pincode" placeholder="400001" maxLength={6} {...register("pincode")} className={errors.pincode ? "border-destructive" : ""} />
                          {errors.pincode && <p className="text-xs text-destructive">{errors.pincode.message}</p>}
                        </div>
                      </div>

                      {/* Shipping quote preview */}
                      {pincode && /^\d{6}$/.test(pincode) && (
                        <div className="mt-2">
                          {quotesLoading ? (
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              <Loader2 className="w-3.5 h-3.5 animate-spin" /> Fetching shipping rates...
                            </div>
                          ) : shippingQuotes.length > 0 ? (
                            <div className="space-y-2">
                              <p className="text-sm font-medium text-muted-foreground">Available shipping options:</p>
                              {shippingQuotes.map((q, i) => (
                                <label key={i} className={`flex items-center justify-between p-3 border rounded-lg cursor-pointer transition-all ${selectedShipping?.courier_name === q.courier_name ? "border-primary bg-primary/5" : "hover:bg-muted"}`}>
                                  <div className="flex items-center gap-3">
                                    <input type="radio" checked={selectedShipping?.courier_name === q.courier_name} onChange={() => setSelectedShipping(q)} className="text-primary" />
                                    <div>
                                      <p className="text-sm font-medium">{q.courier_name}</p>
                                      <p className="text-xs text-muted-foreground">{q.estimated_days}</p>
                                    </div>
                                  </div>
                                  <span className="font-bold text-sm">₹{q.rate}</span>
                                </label>
                              ))}
                            </div>
                          ) : null}
                        </div>
                      )}

                      <div className="pt-2">
                        <Button type="submit" disabled={isSubmitting} className="flex items-center gap-2">
                          Continue to Review <ChevronRight className="w-4 h-4" />
                        </Button>
                      </div>
                    </form>
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {/* STEP 2: Review */}
            {step === "review" && addressData && (
              <motion.div
                key="review"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.25 }}
              >
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span className="flex items-center gap-2"><Package className="w-5 h-5 text-primary" /> Review Order</span>
                      <Button variant="ghost" size="sm" onClick={() => setStep("address")}>Edit Address</Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Address summary */}
                    <div className="bg-muted/50 rounded-lg p-4 text-sm">
                      <p className="font-semibold">{addressData.name}</p>
                      <p className="text-muted-foreground">{addressData.full_address}, {addressData.city}, {addressData.state} — {addressData.pincode}</p>
                      <p className="text-muted-foreground">+91 {addressData.phone}</p>
                    </div>

                    {/* Items */}
                    <div className="space-y-3">
                      {cart?.items.map((item) => (
                        <div key={item.id} className="flex items-center gap-3">
                          <div className="w-12 h-12 bg-muted rounded overflow-hidden shrink-0">
                            {item.product?.primary_image ? (
                              <img src={item.product.primary_image} alt={item.product.name} className="w-full h-full object-cover" />
                            ) : <Package className="w-6 h-6 text-primary/20 m-3" />}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium line-clamp-1">{item.product?.name}</p>
                            <p className="text-xs text-muted-foreground">{item.variant?.size_label} × {item.quantity}</p>
                          </div>
                          <p className="text-sm font-bold shrink-0">₹{item.total_price.toFixed(2)}</p>
                        </div>
                      ))}
                    </div>

                    {placeError && (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex items-start gap-2 bg-destructive/10 text-destructive text-sm rounded-lg px-4 py-3"
                      >
                        <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                        {placeError}
                      </motion.div>
                    )}

                    <div className="flex flex-wrap gap-3 pt-2">
                      <Button onClick={handlePlaceOrder} disabled={isPlacing} size="lg" className="flex items-center gap-2">
                        {isPlacing ? (
                          <><Loader2 className="w-4 h-4 animate-spin" /> Placing Order...</>
                        ) : (
                          <><Lock className="w-4 h-4" /> Place Order — ₹{total.toFixed(2)}</>
                        )}
                      </Button>
                      <Button variant="ghost" onClick={() => setStep("address")}>← Back</Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}

          </AnimatePresence>
        </div>

        {/* ─── Right: Order Summary ─────────────────────────────────── */}
        <div className="flex-1">
          <Card className="sticky top-24">
            <CardContent className="p-6">
              <h2 className="font-bold mb-4">Order Summary</h2>

              <div className="space-y-3 mb-4 max-h-64 overflow-y-auto">
                {cart?.items.map((item) => (
                  <div key={item.id} className="flex gap-3">
                    <div className="w-14 h-14 bg-muted rounded overflow-hidden shrink-0">
                      {item.product?.primary_image ? (
                        <img src={item.product.primary_image} alt={item.product.name} className="w-full h-full object-cover" />
                      ) : null}
                    </div>
                    <div className="flex-1 min-w-0 text-sm">
                      <p className="font-medium line-clamp-1">{item.product?.name}</p>
                      <p className="text-muted-foreground">{item.variant?.size_label} × {item.quantity}</p>
                      <p className="font-bold mt-0.5">₹{item.total_price.toFixed(2)}</p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="border-t pt-4 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Subtotal</span>
                  <span>₹{subtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Shipping</span>
                  <span>{selectedShipping ? `₹${selectedShipping.rate}` : "—"}</span>
                </div>
                <div className="border-t pt-2 mt-2 flex justify-between items-center">
                  <span className="font-bold">Total</span>
                  <span className="font-bold text-lg text-primary">₹{total.toFixed(2)}</span>
                </div>
              </div>

              <div className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">
                <Lock className="w-3.5 h-3.5" />
                Secured by 256-bit SSL encryption
              </div>
            </CardContent>
          </Card>
        </div>

      </div>
    </div>
  );
}
