"use client";

import { useState, useEffect, use } from "react";
import Image from "next/image";
import { motion, AnimatePresence } from "framer-motion";
import { ShoppingCart, ShieldCheck, Truck, Plus, Minus, Package, Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent } from "@/components/ui/card";
import { useCart } from "@/lib/cart";
import { client } from "@/lib/api";
import Link from "next/link";
import { toast } from "sonner";

interface Variant {
  id: number;
  sku: string;
  size_label: string;
  mrp: number;
  wholesale_price?: number;
  wholesale_min_qty?: number;
  stock_quantity: number;
  is_active: boolean;
}

interface ProductAttribute {
  attribute_name: string;
  attribute_value: string;
}

interface ProductImage {
  image_url: string;
  alt_text?: string;
  is_primary: boolean;
}

interface Product {
  id: number;
  name: string;
  slug: string;
  description?: string;
  material?: string;
  component_type?: string;
  pressure_rating?: string;
  meta_title?: string;
  meta_description?: string;
  variants: Variant[];
  images: ProductImage[];
  attributes: ProductAttribute[];
  related_products?: { id: number; name: string; slug: string; primary_image?: string; min_price?: number }[];
}

interface PriceBreakdown {
  unit_price: number;
  total_price: number;
  tier_applied: string;
  savings_amount?: number;
  savings_percent?: number;
}

function AnimatedNumber({ value }: { value: number }) {
  return (
    <AnimatePresence mode="wait">
      <motion.span
        key={value}
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 8 }}
        transition={{ duration: 0.2 }}
        className="inline-block"
      >
        ₹{value.toFixed(2)}
      </motion.span>
    </AnimatePresence>
  );
}

export default function ProductPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const { addItem } = useCart();

  const [product, setProduct] = useState<Product | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeImage, setActiveImage] = useState(0);
  const [selectedVariant, setSelectedVariant] = useState<Variant | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [activeTab, setActiveTab] = useState<"description" | "specs" | "shipping">("description");
  const [priceBreakdown, setPriceBreakdown] = useState<PriceBreakdown | null>(null);
  const [priceLoading, setPriceLoading] = useState(false);
  const [addingToCart, setAddingToCart] = useState(false);

  // Load product data
  useEffect(() => {
    async function fetchProduct() {
      setIsLoading(true);
      try {
        const { data, error: apiErr } = await client.GET("/api/products/{slug}", {
          params: { path: { slug } },
        });
        if (apiErr || !data) throw new Error("Product not found");
        // API returns { product: {...}, related_products: [...] }
        const prod = (data as any).product ?? data;
        setProduct(prod as unknown as Product);
        const firstActive = (prod as any).variants?.find((v: any) => v.is_active);
        if (firstActive) setSelectedVariant(firstActive);
      } catch (e: any) {
        setError(e.message || "Failed to load product");
      } finally {
        setIsLoading(false);
      }
    }
    fetchProduct();
  }, [slug]);

  // Fetch price breakdown whenever variant or quantity changes
  useEffect(() => {
    if (!selectedVariant || !product) return;
    let cancelled = false;

    async function fetchPrice() {
      setPriceLoading(true);
      try {
        const { data } = await client.GET(
          "/api/products/{slug}/variants/{variant_id}/price",
          {
            params: {
              path: { slug, variant_id: selectedVariant!.id },
              query: { quantity },
            },
          }
        );
        if (!cancelled && data) setPriceBreakdown(data as PriceBreakdown);
      } catch {
        // Fallback: calculate locally
        if (!cancelled && selectedVariant) {
          const isWholesale =
            selectedVariant.wholesale_price != null &&
            selectedVariant.wholesale_min_qty != null &&
            quantity >= selectedVariant.wholesale_min_qty;
          const unitPrice = isWholesale
            ? selectedVariant.wholesale_price!
            : selectedVariant.mrp;
          const savings = isWholesale
            ? (selectedVariant.mrp - selectedVariant.wholesale_price!) * quantity
            : 0;
          setPriceBreakdown({
            unit_price: unitPrice,
            total_price: unitPrice * quantity,
            tier_applied: isWholesale ? "wholesale" : "retail",
            savings_amount: savings,
            savings_percent: isWholesale
              ? Math.round(((selectedVariant.mrp - selectedVariant.wholesale_price!) / selectedVariant.mrp) * 100)
              : 0,
          });
        }
      } finally {
        if (!cancelled) setPriceLoading(false);
      }
    }
    fetchPrice();
    return () => { cancelled = true; };
  }, [selectedVariant, quantity, slug, product]);

  const handleAddToCart = async () => {
    if (!selectedVariant) return;
    setAddingToCart(true);
    try {
      await addItem(selectedVariant.id, quantity);
      toast.success(`${product?.name} added to cart`, {
        description: `${quantity} × ${selectedVariant.size_label}`,
      });
    } catch (err: any) {
      toast.error(err.message || "Failed to add to cart");
    } finally {
      setAddingToCart(false);
    }
  };

  // ─── Loading state ────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-12">
          <div className="flex flex-col gap-4">
            <Skeleton className="aspect-square rounded-2xl w-full" />
            <div className="flex gap-4">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="w-20 h-20 rounded-xl" />)}
            </div>
          </div>
          <div className="space-y-4">
            <Skeleton className="h-10 w-3/4" />
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-2/3" />
            <div className="flex gap-3 mt-6">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-10 w-24 rounded-lg" />)}
            </div>
            <Skeleton className="h-40 w-full rounded-2xl mt-4" />
          </div>
        </div>
      </div>
    );
  }

  // ─── Error state ──────────────────────────────────────────────────────────
  if (error || !product) {
    return (
      <div className="container mx-auto px-4 py-24 text-center">
        <AlertCircle className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
        <h1 className="text-2xl font-bold mb-2">Product not found</h1>
        <p className="text-muted-foreground mb-6">{error}</p>
        <Link href="/search">
          <Button>Browse all products</Button>
        </Link>
      </div>
    );
  }

  const images = product.images?.length > 0
    ? product.images.map((img) => `/products/${img.image_url}`)
    : ["https://placehold.co/600x600/f8fafc/334155?text=No+Image"];

  const isWholesale = priceBreakdown?.tier_applied === "wholesale";
  const totalPrice = priceBreakdown?.total_price ?? (selectedVariant ? selectedVariant.mrp * quantity : 0);
  const unitPrice = priceBreakdown?.unit_price ?? selectedVariant?.mrp ?? 0;

  const AddToCartButton = ({ className = "" }: { className?: string }) => (
    <Button
      size="lg"
      className={`${className} flex items-center gap-2`}
      onClick={handleAddToCart}
      disabled={addingToCart || !selectedVariant || selectedVariant.stock_quantity === 0}
    >
      {addingToCart ? (
        <><Loader2 className="w-5 h-5 animate-spin" /> Adding...</>
      ) : selectedVariant?.stock_quantity === 0 ? (
        "Out of Stock"
      ) : (
        <><ShoppingCart className="w-5 h-5" /> Add to Cart</>
      )}
    </Button>
  );

  return (
    <div className="container mx-auto px-4 py-8 mb-20 sm:mb-8">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-12">

        {/* ─── Image Gallery ───────────────────────────────────────────── */}
        <div className="flex flex-col gap-4">
          <div className="aspect-square bg-muted rounded-2xl overflow-hidden relative">
            <AnimatePresence mode="wait">
              <motion.img
                key={activeImage}
                src={images[activeImage]}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.25 }}
                className="w-full h-full object-cover"
                alt={product.name}
              />
            </AnimatePresence>
          </div>
          {images.length > 1 && (
            <div className="flex gap-3 overflow-x-auto pb-2">
              {images.map((img, idx) => (
                <button
                  key={idx}
                  onClick={() => setActiveImage(idx)}
                  className={`shrink-0 w-20 h-20 rounded-xl overflow-hidden border-2 transition-all ${
                    activeImage === idx
                      ? "border-primary ring-2 ring-primary/20"
                      : "border-transparent opacity-60 hover:opacity-100"
                  }`}
                >
                  <img src={img} className="w-full h-full object-cover" alt={`View ${idx + 1}`} />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* ─── Product Details ─────────────────────────────────────────── */}
        <div className="flex flex-col">
          <div className="flex flex-wrap gap-2 mb-3">
            {product.material && (
              <Badge variant="secondary">{product.material}</Badge>
            )}
            {product.pressure_rating && (
              <Badge variant="outline">{product.pressure_rating}</Badge>
            )}
            {product.component_type && (
              <Badge variant="outline">{product.component_type}</Badge>
            )}
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold mb-3">{product.name}</h1>
          {product.description && (
            <p className="text-muted-foreground mb-6 leading-relaxed">{product.description}</p>
          )}

          {/* ─── Variant selector ──────────────────────────────────── */}
          {product.variants.length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold mb-3 text-sm">
                Select Size
                {selectedVariant && (
                  <span className="ml-2 text-primary font-bold">— {selectedVariant.size_label}</span>
                )}
              </h3>
              <div className="flex flex-wrap gap-2">
                {product.variants.filter((v) => v.is_active).map((v) => (
                  <motion.button
                    key={v.id}
                    whileTap={{ scale: 0.96 }}
                    onClick={() => {
                      setSelectedVariant(v);
                      setQuantity(1);
                    }}
                    className={`px-3 py-2 rounded-lg border text-sm font-medium transition-all ${
                      selectedVariant?.id === v.id
                        ? "border-primary bg-primary/10 text-primary shadow-sm"
                        : v.stock_quantity === 0
                        ? "border-dashed border-muted-foreground/40 text-muted-foreground line-through cursor-not-allowed"
                        : "border-border hover:bg-muted"
                    }`}
                    disabled={v.stock_quantity === 0}
                  >
                    {v.size_label}
                    {v.stock_quantity === 0 && <span className="ml-1 text-[10px]">OOS</span>}
                  </motion.button>
                ))}
              </div>
            </div>
          )}

          {/* ─── Pricing & Quantity ────────────────────────────────── */}
          {selectedVariant && (
            <div className="bg-muted/50 p-6 rounded-2xl mb-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Total Price</p>
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className="text-3xl font-bold text-primary">
                      {priceLoading ? (
                        <span className="text-muted-foreground text-xl">...</span>
                      ) : (
                        <AnimatedNumber value={totalPrice} />
                      )}
                    </span>
                    <AnimatePresence>
                      {isWholesale && (
                        <motion.div
                          initial={{ scale: 0.8, opacity: 0 }}
                          animate={{ scale: 1, opacity: 1 }}
                          exit={{ scale: 0.8, opacity: 0 }}
                          className="flex items-center gap-1"
                        >
                          <Badge className="bg-accent text-accent-foreground text-xs font-bold">
                            🏷️ Wholesale Pricing
                          </Badge>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">
                    ₹{unitPrice.toFixed(2)} / unit
                    {isWholesale && priceBreakdown?.savings_percent && (
                      <span className="ml-2 text-green-600 font-medium">
                        Save {priceBreakdown.savings_percent}%
                      </span>
                    )}
                  </p>
                </div>

                {selectedVariant.stock_quantity > 0 && selectedVariant.stock_quantity <= 20 && (
                  <Badge variant="destructive" className="text-[10px]">
                    Only {selectedVariant.stock_quantity} left
                  </Badge>
                )}
              </div>

              {/* Quantity stepper */}
              <div className="flex items-center gap-4 flex-wrap">
                <div className="flex items-center border rounded-lg bg-background overflow-hidden">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setQuantity(Math.max(1, quantity - 1))}
                    className="rounded-none h-10 w-10"
                  >
                    <Minus className="w-4 h-4" />
                  </Button>
                  <span className="w-12 text-center font-semibold text-base">{quantity}</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setQuantity(quantity + 1)}
                    className="rounded-none h-10 w-10"
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>

                {selectedVariant.wholesale_min_qty && !isWholesale && (
                  <p className="text-sm text-muted-foreground">
                    Order{" "}
                    <button
                      className="font-bold text-foreground underline-offset-2 hover:underline"
                      onClick={() => setQuantity(selectedVariant.wholesale_min_qty!)}
                    >
                      {selectedVariant.wholesale_min_qty}+
                    </button>{" "}
                    for wholesale price (₹{selectedVariant.wholesale_price?.toFixed(2)}/unit)
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Desktop add to cart */}
          <div className="hidden sm:block mb-8">
            <AddToCartButton className="w-full sm:w-auto px-10 text-base" />
          </div>

          {/* ─── Tabs ─────────────────────────────────────────────── */}
          <div className="border-t pt-6">
            <div className="flex gap-6 border-b mb-6">
              {(["description", "specs", "shipping"] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`pb-3 text-sm font-semibold capitalize transition-colors relative ${
                    activeTab === tab ? "text-primary" : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {tab}
                  {activeTab === tab && (
                    <motion.div
                      layoutId="tab-indicator"
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary rounded-full"
                    />
                  )}
                </button>
              ))}
            </div>

            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.2 }}
                className="text-muted-foreground text-sm leading-relaxed min-h-[100px]"
              >
                {activeTab === "description" && (
                  <p>{product.description || "No description available."}</p>
                )}
                {activeTab === "specs" && (
                  <ul className="space-y-0 divide-y">
                    {product.material && (
                      <li className="grid grid-cols-2 py-2.5">
                        <span className="font-medium text-foreground">Material</span>
                        <span>{product.material}</span>
                      </li>
                    )}
                    {product.pressure_rating && (
                      <li className="grid grid-cols-2 py-2.5">
                        <span className="font-medium text-foreground">Pressure Rating</span>
                        <span>{product.pressure_rating}</span>
                      </li>
                    )}
                    {product.attributes?.map((attr) => (
                      <li key={attr.attribute_name} className="grid grid-cols-2 py-2.5">
                        <span className="font-medium text-foreground">{attr.attribute_name}</span>
                        <span>{attr.attribute_value}</span>
                      </li>
                    ))}
                    {!product.material && !product.pressure_rating && (!product.attributes || product.attributes.length === 0) && (
                      <li className="py-4 text-center">No specifications available.</li>
                    )}
                  </ul>
                )}
                {activeTab === "shipping" && (
                  <div className="space-y-4">
                    <div className="flex items-start gap-3">
                      <Truck className="w-5 h-5 text-primary mt-0.5 shrink-0" />
                      <div>
                        <p className="font-semibold text-foreground">Fast Dispatch</p>
                        <p>Usually ships within 24–48 hours of order confirmation.</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <ShieldCheck className="w-5 h-5 text-primary mt-0.5 shrink-0" />
                      <div>
                        <p className="font-semibold text-foreground">Secure Packaging</p>
                        <p>Packed to industrial standards to prevent damage during transit.</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <Package className="w-5 h-5 text-primary mt-0.5 shrink-0" />
                      <div>
                        <p className="font-semibold text-foreground">Pan-India Delivery</p>
                        <p>We ship to all major cities and towns across India via Shiprocket.</p>
                      </div>
                    </div>
                  </div>
                )}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* ─── Related Products ──────────────────────────────────────────── */}
      {product.related_products && product.related_products.length > 0 && (
        <section className="mt-16 pt-8 border-t">
          <h2 className="text-xl font-bold mb-6">Related Products</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {product.related_products.map((rel) => (
              <Link key={rel.id} href={`/product/${rel.slug}`}>
                <Card className="h-full hover:shadow-md transition-shadow group">
                  <div className="aspect-square bg-muted overflow-hidden rounded-t-xl">
                    {rel.primary_image ? (
                      <Image 
                        src={`/products/${rel.primary_image}`} 
                        alt={rel.name} 
                        fill 
                        className="object-cover group-hover:scale-105 transition-transform duration-300" 
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Package className="w-8 h-8 text-primary/20" />
                      </div>
                    )}
                  </div>
                  <CardContent className="p-3">
                    <h3 className="text-sm font-medium line-clamp-2">{rel.name}</h3>
                    {rel.min_price != null && (
                      <p className="text-sm font-bold text-primary mt-1">from ₹{rel.min_price.toFixed(0)}</p>
                    )}
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* ─── Sticky mobile Add to Cart ────────────────────────────────── */}
      <div className="fixed bottom-16 left-0 right-0 p-4 bg-background border-t shadow-[0_-4px_10px_rgba(0,0,0,0.05)] sm:hidden z-40 flex items-center gap-4">
        <div className="flex-1">
          <p className="text-lg font-bold text-primary">
            {priceLoading ? "..." : `₹${totalPrice.toFixed(2)}`}
          </p>
          <p className="text-xs text-muted-foreground">Qty: {quantity}</p>
        </div>
        <AddToCartButton className="flex-[2]" />
      </div>
    </div>
  );
}
