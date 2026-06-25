"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Package, Info } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { client } from "@/lib/api";

interface SearchResult {
  id: number;
  name: string;
  slug: string;
  primary_image?: string;
  min_price?: number;
  max_price?: number;
  component_type?: string;
  pressure_rating?: string;
}

interface SearchResponse {
  results: SearchResult[];
  total: number;
  fuzzy_used: boolean;
  corrected_query?: string;
}

function SearchResults() {
  const searchParams = useSearchParams();
  const q = searchParams.get("q") || "";

  const [data, setData] = useState<SearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!q) return;
    let cancelled = false;
    setIsLoading(true);
    setData(null);

    async function doSearch() {
      try {
        const { data: res } = await client.GET("/api/search", {
          params: { query: { q } },
        });
        if (!cancelled && res) {
          const r = res as any;
          setData({
            results: r.results ?? [],
            total: r.total ?? (r.results ?? []).length,
            fuzzy_used: r.fuzzy_fallback_used ?? r.fuzzy_used ?? false,
            corrected_query: r.query,
          });
        }
      } catch (e) {
        console.error("Search failed", e);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    doSearch();
    return () => { cancelled = true; };
  }, [q]);

  if (!q) {
    return (
      <div className="py-24 flex flex-col items-center justify-center text-center max-w-md mx-auto">
        <div className="bg-muted p-6 rounded-full mb-6">
          <Search className="w-12 h-12 text-muted-foreground" />
        </div>
        <h2 className="text-2xl font-bold mb-2">Search our catalog</h2>
        <p className="text-muted-foreground">
          Type a product name, size, or component type in the search bar above.
        </p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold mb-2">Search Results</h1>

        {/* Fuzzy match indicator */}
        <AnimatePresence>
          {data?.fuzzy_used && (
            <motion.div
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-start gap-2 bg-accent/10 border border-accent/20 rounded-lg px-4 py-2.5 text-sm mb-3 max-w-lg"
            >
              <Info className="w-4 h-4 text-accent mt-0.5 shrink-0" />
              <span>
                Showing fuzzy matches for{" "}
                <strong>"{q}"</strong>
                {data.corrected_query && data.corrected_query !== q && (
                  <> — did you mean <strong>"{data.corrected_query}"</strong>?</>
                )}
              </span>
            </motion.div>
          )}
        </AnimatePresence>

        {!isLoading && data && (
          <p className="text-muted-foreground">
            {data.total} result{data.total !== 1 ? "s" : ""} for{" "}
            <span className="font-semibold text-foreground">"{q}"</span>
          </p>
        )}
      </div>

      {isLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 sm:gap-6">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="space-y-3">
              <Skeleton className="w-full aspect-square rounded-xl" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/4" />
            </div>
          ))}
        </div>
      ) : data && data.results.length > 0 ? (
        <motion.div
          className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 sm:gap-6"
          initial="hidden"
          animate="show"
          variants={{ show: { transition: { staggerChildren: 0.06 } } }}
        >
          {data.results.map((product) => (
            <motion.div
              key={product.id}
              variants={{ hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0, transition: { duration: 0.3 } } }}
            >
              <Link href={`/product/${product.slug}`}>
                <Card className="h-full overflow-hidden hover:shadow-md transition-shadow group cursor-pointer">
                  <div className="aspect-square bg-muted relative overflow-hidden">
                    {product.primary_image ? (
                      <img
                        src={product.primary_image}
                        alt={product.name}
                        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-primary/5">
                        <Package className="w-8 h-8 text-primary/20" />
                      </div>
                    )}
                    {product.pressure_rating && (
                      <div className="absolute top-2 left-2">
                        <Badge variant="secondary" className="text-[10px]">{product.pressure_rating}</Badge>
                      </div>
                    )}
                  </div>
                  <CardContent className="p-4">
                    <h3 className="font-semibold text-sm sm:text-base line-clamp-2 mb-1">{product.name}</h3>
                    {product.component_type && (
                      <p className="text-xs text-muted-foreground mb-2">{product.component_type}</p>
                    )}
                    {product.min_price != null && (
                      <p className="text-base font-bold text-primary">
                        ₹{product.min_price.toFixed(0)}
                        {product.max_price && product.max_price !== product.min_price
                          ? ` – ₹${product.max_price.toFixed(0)}`
                          : ""}
                      </p>
                    )}
                  </CardContent>
                </Card>
              </Link>
            </motion.div>
          ))}
        </motion.div>
      ) : (
        <div className="py-24 flex flex-col items-center justify-center text-center max-w-md mx-auto">
          <div className="bg-muted p-6 rounded-full mb-6">
            <Search className="w-12 h-12 text-muted-foreground" />
          </div>
          <h2 className="text-2xl font-bold mb-2">No results found</h2>
          <p className="text-muted-foreground">
            We couldn't find anything matching <strong>"{q}"</strong>. Try checking your spelling or using more general terms like "elbow" or "reducer".
          </p>
        </div>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense
      fallback={
        <div className="container mx-auto px-4 py-16 text-center text-muted-foreground">
          Loading search results...
        </div>
      }
    >
      <SearchResults />
    </Suspense>
  );
}
