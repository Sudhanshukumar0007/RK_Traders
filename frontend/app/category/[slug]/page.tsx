"use client";

import { useState, useEffect, use, useCallback } from "react";
import Link from "next/link";
import Image from "next/image";
import { motion, AnimatePresence } from "framer-motion";
import { SlidersHorizontal, Package, ChevronDown, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { client } from "@/lib/api";

interface Product {
  id: number;
  name: string;
  slug: string;
  primary_image?: string;
  min_price?: number;
  max_price?: number;
  variant_count?: number;
  component_type?: string;
  pressure_rating?: string;
}

const SORT_OPTIONS = [
  { label: "Newest", value: "newest" },
  { label: "Price: Low → High", value: "price_asc" },
  { label: "Price: High → Low", value: "price_desc" },
  { label: "Name A–Z", value: "name_asc" },
];

const PRESSURE_RATINGS = ["SCH-40", "SCH-80", "Class-3", "Class-6"];
const COMPONENT_TYPES = ["Elbow", "Tee", "Reducer Bush", "Coupler", "End Cap", "Union", "Pipe"];

export default function CategoryPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState("newest");
  const [pressureFilters, setPressureFilters] = useState<string[]>([]);
  const [typeFilters, setTypeFilters] = useState<string[]>([]);
  const [showMobileFilters, setShowMobileFilters] = useState(false);
  const [showSortMenu, setShowSortMenu] = useState(false);
  const LIMIT = 12;

  const fetchProducts = useCallback(async () => {
    setIsLoading(true);
    try {
      const queryParams: Record<string, any> = {
        limit: LIMIT,
        offset: (page - 1) * LIMIT,
        sort,
        category_slug: slug,
      };
      if (pressureFilters.length === 1) queryParams.pressure_rating = pressureFilters[0];
      if (typeFilters.length === 1) queryParams.component_type = typeFilters[0];

      const { data } = await client.GET("/api/products", {
        params: { query: queryParams as any },
      });
      if (data) {
        const d = data as any;
        setProducts(d.items ?? d ?? []);
        setTotal(d.total ?? (d.items ?? d ?? []).length);
      }
    } catch (e) {
      console.error("Failed to fetch products", e);
    } finally {
      setIsLoading(false);
    }
  }, [slug, page, sort, pressureFilters, typeFilters]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  const togglePressure = (val: string) => {
    setPressureFilters((prev) =>
      prev.includes(val) ? prev.filter((x) => x !== val) : [...prev, val]
    );
    setPage(1);
  };
  const toggleType = (val: string) => {
    setTypeFilters((prev) =>
      prev.includes(val) ? prev.filter((x) => x !== val) : [...prev, val]
    );
    setPage(1);
  };
  const clearFilters = () => {
    setPressureFilters([]);
    setTypeFilters([]);
    setPage(1);
  };

  const activeFilterCount = pressureFilters.length + typeFilters.length;
  const totalPages = Math.ceil(total / LIMIT);
  const categoryTitle = slug.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  const FiltersPanel = () => (
    <div className="space-y-6">
      {activeFilterCount > 0 && (
        <button onClick={clearFilters} className="text-xs text-destructive flex items-center gap-1 hover:underline">
          <X className="w-3 h-3" /> Clear all filters ({activeFilterCount})
        </button>
      )}
      <div>
        <h3 className="font-semibold mb-3 text-sm uppercase tracking-wide text-muted-foreground">
          Pressure Rating
        </h3>
        <div className="space-y-2">
          {PRESSURE_RATINGS.map((r) => (
            <label key={r} className="flex items-center gap-2.5 text-sm cursor-pointer group">
              <input
                type="checkbox"
                checked={pressureFilters.includes(r)}
                onChange={() => togglePressure(r)}
                className="rounded border-gray-300 text-primary w-4 h-4"
              />
              <span className="group-hover:text-primary transition-colors">{r}</span>
            </label>
          ))}
        </div>
      </div>
      <div>
        <h3 className="font-semibold mb-3 text-sm uppercase tracking-wide text-muted-foreground">
          Component Type
        </h3>
        <div className="space-y-2">
          {COMPONENT_TYPES.map((t) => (
            <label key={t} className="flex items-center gap-2.5 text-sm cursor-pointer group">
              <input
                type="checkbox"
                checked={typeFilters.includes(t)}
                onChange={() => toggleType(t)}
                className="rounded border-gray-300 text-primary w-4 h-4"
              />
              <span className="group-hover:text-primary transition-colors">{t}</span>
            </label>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col md:flex-row gap-8">

        {/* ─── Sidebar ─────────────────────────────────────────────────── */}
        <aside className="w-full md:w-56 shrink-0">
          <div className="sticky top-24">
            {/* Mobile filter toggle */}
            <div className="flex items-center justify-between mb-4 md:hidden">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowMobileFilters(!showMobileFilters)}
                className="flex items-center gap-2"
              >
                <SlidersHorizontal className="w-4 h-4" />
                Filters
                {activeFilterCount > 0 && (
                  <Badge variant="default" className="h-5 w-5 p-0 text-[10px] flex items-center justify-center">
                    {activeFilterCount}
                  </Badge>
                )}
              </Button>
            </div>

            <AnimatePresence>
              {showMobileFilters && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="md:hidden overflow-hidden border rounded-xl p-4 mb-4"
                >
                  <FiltersPanel />
                </motion.div>
              )}
            </AnimatePresence>

            <div className="hidden md:block">
              <h2 className="text-lg font-bold mb-6">Filters</h2>
              <FiltersPanel />
            </div>
          </div>
        </aside>

        {/* ─── Product Grid ─────────────────────────────────────────────── */}
        <div className="flex-1 min-w-0">
          <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold">{categoryTitle}</h1>
              {!isLoading && (
                <p className="text-sm text-muted-foreground mt-0.5">
                  {total} product{total !== 1 ? "s" : ""} found
                </p>
              )}
            </div>

            {/* Sort */}
            <div className="relative">
              <Button
                variant="outline"
                size="sm"
                className="flex items-center gap-2"
                onClick={() => setShowSortMenu(!showSortMenu)}
              >
                {SORT_OPTIONS.find((o) => o.value === sort)?.label}
                <ChevronDown className="w-3.5 h-3.5" />
              </Button>
              <AnimatePresence>
                {showSortMenu && (
                  <motion.div
                    initial={{ opacity: 0, y: -6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }}
                    className="absolute right-0 top-full mt-1 w-48 bg-card border rounded-lg shadow-lg z-20 overflow-hidden"
                  >
                    {SORT_OPTIONS.map((opt) => (
                      <button
                        key={opt.value}
                        onClick={() => {
                          setSort(opt.value);
                          setShowSortMenu(false);
                          setPage(1);
                        }}
                        className={`w-full text-left px-4 py-2.5 text-sm hover:bg-muted transition-colors ${
                          sort === opt.value ? "text-primary font-medium" : ""
                        }`}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>

          {/* Active filter chips */}
          {activeFilterCount > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {pressureFilters.map((f) => (
                <Badge key={f} variant="secondary" className="flex items-center gap-1 pr-1.5 cursor-pointer" onClick={() => togglePressure(f)}>
                  {f} <X className="w-3 h-3" />
                </Badge>
              ))}
              {typeFilters.map((f) => (
                <Badge key={f} variant="secondary" className="flex items-center gap-1 pr-1.5 cursor-pointer" onClick={() => toggleType(f)}>
                  {f} <X className="w-3 h-3" />
                </Badge>
              ))}
            </div>
          )}

          {isLoading ? (
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="space-y-3">
                  <Skeleton className="w-full aspect-square rounded-xl" />
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-4 w-1/4" />
                </div>
              ))}
            </div>
          ) : products.length === 0 ? (
            <div className="py-24 text-center">
              <Package className="w-12 h-12 mx-auto mb-4 text-muted-foreground/40" />
              <h3 className="text-xl font-semibold mb-2">No products found</h3>
              <p className="text-muted-foreground mb-6">Try adjusting your filters or browse all products.</p>
              <Button onClick={clearFilters} variant="outline">Clear filters</Button>
            </div>
          ) : (
            <>
              <motion.div layout className="grid grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                <AnimatePresence mode="popLayout">
                  {products.map((product) => (
                    <motion.div
                      key={product.id}
                      layout
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.95 }}
                      transition={{ duration: 0.2 }}
                    >
                      <Link href={`/product/${product.slug}`}>
                        <Card className="h-full overflow-hidden hover:shadow-md transition-shadow group cursor-pointer">
                          <div className="aspect-square bg-muted relative overflow-hidden">
                            {product.primary_image ? (
                              <Image
                                src={`/products/${product.primary_image}`}
                                alt={product.name}
                                fill
                                className="object-cover transition-transform duration-500 group-hover:scale-110"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center bg-primary/5">
                                <Package className="w-10 h-10 text-primary/20" />
                              </div>
                            )}
                            {product.pressure_rating && (
                              <div className="absolute top-2 left-2">
                                <Badge variant="secondary" className="text-[10px]">
                                  {product.pressure_rating}
                                </Badge>
                              </div>
                            )}
                          </div>
                          <CardContent className="p-4">
                            <h3 className="font-semibold text-sm sm:text-base line-clamp-2 mb-1">{product.name}</h3>
                            {product.component_type && (
                              <p className="text-xs text-muted-foreground mb-2">{product.component_type}</p>
                            )}
                            {product.min_price != null ? (
                              <p className="text-base font-bold text-primary">
                                ₹{product.min_price.toFixed(0)}
                                {product.max_price && product.max_price !== product.min_price
                                  ? ` – ₹${product.max_price.toFixed(0)}`
                                  : ""}
                              </p>
                            ) : null}
                            {product.variant_count != null && product.variant_count > 1 && (
                              <p className="text-xs text-muted-foreground mt-1">{product.variant_count} size options</p>
                            )}
                          </CardContent>
                        </Card>
                      </Link>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </motion.div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex justify-center items-center gap-3 mt-10">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    Previous
                  </Button>
                  <span className="text-sm text-muted-foreground">
                    Page {page} of {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                  >
                    Next
                  </Button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
