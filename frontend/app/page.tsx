"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import { Wrench, ShieldCheck, Truck, ArrowRight, Package, Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { client } from "@/lib/api";

interface Category {
  id: number;
  name: string;
  slug: string;
  image_url?: string | null;
  description?: string | null;
}

interface Product {
  id: number;
  name: string;
  slug: string;
  primary_image?: string;
  min_price?: number;
  max_price?: number;
  variant_count?: number;
}

const stagger = {
  show: { transition: { staggerChildren: 0.08 } },
};
const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

export default function HomePage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loadingCats, setLoadingCats] = useState(true);
  const [loadingProds, setLoadingProds] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const { data: catData } = await client.GET("/api/categories", {});
        if (catData) {
          // Show top-level categories (no parent)
          const topLevel = catData.filter((c: any) => !c.parent_id).slice(0, 8);
          setCategories(topLevel);
        }
      } catch (e) {
        console.error("Failed to fetch categories", e);
      } finally {
        setLoadingCats(false);
      }

      try {
        const { data: prodData } = await client.GET("/api/products", {
          params: { query: { limit: 8, sort: "newest" } as any },
        });
        if (prodData) setProducts((prodData as any).items ?? prodData ?? []);
      } catch (e) {
        console.error("Failed to fetch products", e);
      } finally {
        setLoadingProds(false);
      }
    }
    fetchData();
  }, []);

  return (
    <div className="flex flex-col gap-16 pb-16">

      {/* ─── Hero ─────────────────────────────────────────────────────────── */}
      <section className="relative bg-slate-900 text-white overflow-hidden py-24 sm:py-36">
        {/* Decorative grid */}
        <div
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px)",
            backgroundSize: "60px 60px",
          }}
        />
        {/* Accent glow */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-accent/20 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />

        <div className="container mx-auto px-4 relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: "easeOut" }}
            className="max-w-3xl"
          >
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="inline-flex items-center gap-2 bg-accent/20 border border-accent/30 rounded-full px-4 py-1.5 mb-6 text-accent text-sm font-medium"
            >
              <Star className="w-3.5 h-3.5 fill-current" />
              Wholesale pricing from ₹100 orders
            </motion.div>

            <h1 className="text-5xl sm:text-7xl font-bold tracking-tight mb-6 leading-tight">
              Industrial Grade{" "}
              <span className="text-accent">Hardware</span>{" "}
              &amp; Plumbing
            </h1>
            <p className="text-lg sm:text-xl text-slate-300 mb-10 max-w-xl">
              Premium UPVC pipes, fittings &amp; tools for contractors and builders. Bulk wholesale pricing available instantly.
            </p>
            <div className="flex flex-wrap gap-4">
              <Button size="lg" className="bg-accent hover:bg-accent/90 text-accent-foreground font-semibold text-base px-8">
                <Link href="/category/upvc-pipes">Shop Pipes &amp; Fittings</Link>
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="text-white border-white/40 hover:bg-white/10 font-semibold text-base"
              >
                <Link href="/search">Browse All Products</Link>
              </Button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ─── Category Grid ─────────────────────────────────────────────────── */}
      <section className="container mx-auto px-4">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl sm:text-3xl font-bold">Shop by Category</h2>
            <p className="text-muted-foreground mt-1">Browse our full range of hardware &amp; plumbing supplies</p>
          </div>
        </div>

        {loadingCats ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="space-y-3">
                <Skeleton className="w-full aspect-[4/3] rounded-xl" />
                <Skeleton className="h-5 w-3/4 mx-auto" />
              </div>
            ))}
          </div>
        ) : categories.length > 0 ? (
          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            className="grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6"
          >
            {categories.map((cat) => (
              <motion.div key={cat.id} variants={fadeUp}>
                <Link href={`/category/${cat.slug}`}>
                  <motion.div
                    whileHover={{ scale: 1.02, y: -2 }}
                    whileTap={{ scale: 0.98 }}
                    className="group relative rounded-xl overflow-hidden shadow-sm border bg-card cursor-pointer"
                  >
                    <div className="aspect-[4/3] bg-muted overflow-hidden">
                      {cat.image_url ? (
                        <img
                          src={cat.image_url}
                          alt={cat.name}
                          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center bg-primary/5">
                          <Package className="w-12 h-12 text-primary/30" />
                        </div>
                      )}
                    </div>
                    <div className="p-4 bg-card text-center">
                      <h3 className="font-semibold">{cat.name}</h3>
                    </div>
                  </motion.div>
                </Link>
              </motion.div>
            ))}
          </motion.div>
        ) : (
          // Fallback if API returns nothing (e.g., DB not seeded yet)
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6">
            {["UPVC Pipes", "Fittings", "Valves", "Tools & Accessories"].map((name, i) => (
              <Link key={i} href="/search">
                <motion.div
                  whileHover={{ scale: 1.02 }}
                  className="group rounded-xl overflow-hidden shadow-sm border bg-card"
                >
                  <div className="aspect-[4/3] bg-muted flex items-center justify-center">
                    <Package className="w-10 h-10 text-primary/30" />
                  </div>
                  <div className="p-4 text-center">
                    <h3 className="font-semibold">{name}</h3>
                  </div>
                </motion.div>
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* ─── Featured Products ─────────────────────────────────────────────── */}
      <section className="container mx-auto px-4">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl sm:text-3xl font-bold">Featured Products</h2>
            <p className="text-muted-foreground mt-1">Our most popular industrial fittings and pipes</p>
          </div>
          <Link href="/search" className="flex items-center gap-2 text-primary font-medium">
            View all <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {loadingProds ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="space-y-3">
                <Skeleton className="w-full aspect-square rounded-xl" />
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-1/4" />
              </div>
            ))}
          </div>
        ) : products.length > 0 ? (
          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            className="grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6"
          >
            {products.map((product) => (
              <motion.div key={product.id} variants={fadeUp}>
                <Link href={`/product/${product.slug}`}>
                  <Card className="h-full overflow-hidden hover:shadow-md transition-shadow group cursor-pointer">
                    <div className="aspect-square bg-muted overflow-hidden relative">
                      {product.primary_image ? (
                        <Image
                          src={`/products/${product.primary_image}`}
                          alt={product.name}
                          fill
                          className="object-cover transition-transform duration-500 group-hover:scale-110"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center bg-primary/5">
                          <Package className="w-12 h-12 text-primary/20" />
                        </div>
                      )}
                    </div>
                    <CardContent className="p-4">
                      <h3 className="font-semibold text-sm sm:text-base line-clamp-2 mb-2">{product.name}</h3>
                      {product.min_price != null ? (
                        <p className="text-base font-bold text-primary">
                          ₹{product.min_price.toFixed(0)}
                          {product.max_price && product.max_price !== product.min_price
                            ? ` – ₹${product.max_price.toFixed(0)}`
                            : ""}
                        </p>
                      ) : null}
                    </CardContent>
                  </Card>
                </Link>
              </motion.div>
            ))}
          </motion.div>
        ) : (
          <div className="py-16 text-center text-muted-foreground">
            <Package className="w-12 h-12 mx-auto mb-4 text-muted-foreground/40" />
            <p>No products found. <Link href="/search" className="text-primary underline">Browse all</Link></p>
          </div>
        )}
      </section>

      {/* ─── Trust Badges ──────────────────────────────────────────────────── */}
      <section className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="bg-primary text-primary-foreground rounded-2xl p-8 sm:p-12"
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            {[
              {
                icon: <ShieldCheck className="w-8 h-8" />,
                title: "Premium Quality",
                desc: "Industrial-grade UPVC materials tested to ASTM standards for maximum durability.",
              },
              {
                icon: <Truck className="w-8 h-8" />,
                title: "Pan-India Shipping",
                desc: "Next-day dispatch from our warehouse directly to your site.",
              },
              {
                icon: <Wrench className="w-8 h-8" />,
                title: "Expert Support",
                desc: "Technical team ready to assist with sizing, grades &amp; material selection.",
              },
            ].map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.4 }}
                className="flex flex-col items-center gap-3"
              >
                <div className="bg-primary-foreground/10 p-4 rounded-full text-primary-foreground">
                  {item.icon}
                </div>
                <h3 className="text-xl font-semibold">{item.title}</h3>
                <p className="text-primary-foreground/70 text-sm">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>

    </div>
  );
}
