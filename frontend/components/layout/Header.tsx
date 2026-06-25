"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useDebounce } from "use-debounce";
import { Search, ShoppingCart, User, Wrench, Loader2, LogOut, Package } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { client } from "@/lib/api";
import { useCart } from "@/lib/cart";
import { isAuthenticated, logout, getCachedUser } from "@/lib/auth";

export function Header() {
  const router = useRouter();
  const { itemCount } = useCart();
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedQuery] = useDebounce(searchQuery, 300);
  const [isSearching, setIsSearching] = useState(false);
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [authed, setAuthed] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);

  // Check auth status on mount (client-side only)
  useEffect(() => {
    setAuthed(isAuthenticated());
  }, []);

  // Fetch search suggestions
  useEffect(() => {
    async function fetchSuggestions() {
      if (debouncedQuery.length < 2) {
        setSuggestions([]);
        return;
      }
      setIsSearching(true);
      try {
        const { data } = await client.GET("/api/search", {
          params: { query: { q: debouncedQuery } },
        });
        if (data && data.results) {
          setSuggestions(data.results.slice(0, 5));
        }
      } catch (error) {
        console.error("Failed to fetch suggestions", error);
      } finally {
        setIsSearching(false);
      }
    }
    fetchSuggestions();
  }, [debouncedQuery]);

  // Close dropdowns on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      setShowDropdown(false);
      router.push(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const handleLogout = () => {
    logout();
    setAuthed(false);
    setShowUserMenu(false);
    router.push("/");
    router.refresh();
  };

  const cachedUser = getCachedUser();

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4 flex h-16 items-center justify-between gap-4">

        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 text-primary font-bold text-xl tracking-tight shrink-0">
          <Wrench className="w-6 h-6 text-accent" />
          <span className="hidden sm:inline-block">Supreme Hardware</span>
        </Link>

        {/* Search Bar */}
        <div className="flex-1 max-w-xl relative" ref={dropdownRef}>
          <form onSubmit={handleSearchSubmit} className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search products, sizes, components..."
              className="w-full pl-9 bg-muted/50 border-muted"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setShowDropdown(true);
              }}
              onFocus={() => setShowDropdown(true)}
            />
          </form>

          {/* Suggestions Dropdown */}
          <AnimatePresence>
            {showDropdown && searchQuery.length >= 2 && (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.15 }}
                className="absolute top-full mt-1 w-full bg-card border rounded-md shadow-lg overflow-hidden z-50"
              >
                {isSearching ? (
                  <div className="p-4 flex justify-center text-muted-foreground">
                    <Loader2 className="h-5 w-5 animate-spin" />
                  </div>
                ) : suggestions.length > 0 ? (
                  <ul className="py-2">
                    {suggestions.map((item, idx) => (
                      <li key={idx}>
                        <Link
                          href={`/product/${item.slug}`}
                          onClick={() => setShowDropdown(false)}
                          className="block px-4 py-2 hover:bg-muted text-sm"
                        >
                          {item.name}
                        </Link>
                      </li>
                    ))}
                    <li className="px-2 pt-2 border-t mt-2">
                      <Button
                        variant="ghost"
                        className="w-full text-xs text-primary"
                        onClick={() => {
                          setShowDropdown(false);
                          router.push(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
                        }}
                      >
                        View all results for "{searchQuery}"
                      </Button>
                    </li>
                  </ul>
                ) : (
                  <div className="p-4 text-sm text-center text-muted-foreground">No products found.</div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 sm:gap-2">

          {/* User / Account */}
          {authed ? (
            <div className="relative hidden sm:block" ref={userMenuRef}>
              <Button variant="ghost" size="icon" onClick={() => setShowUserMenu(!showUserMenu)}>
                <User className="h-5 w-5" />
              </Button>
              <AnimatePresence>
                {showUserMenu && (
                  <motion.div
                    initial={{ opacity: 0, y: -8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.15 }}
                    className="absolute right-0 top-full mt-1 w-52 bg-card border rounded-lg shadow-lg z-50 overflow-hidden"
                  >
                    {cachedUser && (
                      <div className="px-4 py-3 border-b">
                        <p className="font-semibold text-sm truncate">{cachedUser.name}</p>
                        <p className="text-xs text-muted-foreground truncate">{cachedUser.email}</p>
                      </div>
                    )}
                    <Link href="/account" onClick={() => setShowUserMenu(false)} className="flex items-center gap-2 px-4 py-2.5 text-sm hover:bg-muted transition-colors">
                      <User className="w-4 h-4" /> My Account
                    </Link>
                    <Link href="/account/orders" onClick={() => setShowUserMenu(false)} className="flex items-center gap-2 px-4 py-2.5 text-sm hover:bg-muted transition-colors">
                      <Package className="w-4 h-4" /> My Orders
                    </Link>
                    <button onClick={handleLogout} className="w-full flex items-center gap-2 px-4 py-2.5 text-sm hover:bg-muted transition-colors text-destructive border-t">
                      <LogOut className="w-4 h-4" /> Sign Out
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ) : (
            <Link href="/login" className="hidden sm:flex">
              <Button variant="ghost" size="icon">
                <User className="h-5 w-5" />
                <span className="sr-only">Sign in</span>
              </Button>
            </Link>
          )}

          {/* Cart */}
          <Link href="/cart">
            <Button variant="ghost" size="icon" className="relative">
              <ShoppingCart className="h-5 w-5" />
              <AnimatePresence>
                {itemCount > 0 && (
                  <motion.span
                    key={itemCount}
                    initial={{ scale: 0.5, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.5, opacity: 0 }}
                    className="absolute -top-1 -right-1"
                  >
                    <Badge
                      variant="default"
                      className="h-5 w-5 flex items-center justify-center p-0 text-[10px] bg-accent text-accent-foreground"
                    >
                      {itemCount > 99 ? "99+" : itemCount}
                    </Badge>
                  </motion.span>
                )}
              </AnimatePresence>
              <span className="sr-only">Cart</span>
            </Button>
          </Link>
        </div>

      </div>
    </header>
  );
}
