"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  ReactNode,
} from "react";
import { API_BASE_URL, getAuthToken } from "./api";

// ─── Types ────────────────────────────────────────────────────────────────────

export interface CartVariant {
  id: number;
  sku: string;
  size_label: string;
}

export interface CartProduct {
  id: number;
  name: string;
  slug: string;
  primary_image?: string;
}

export interface CartItem {
  id: number;
  variant_id: number;
  quantity: number;
  unit_price: number;
  total_price: number;
  variant?: CartVariant;
  product?: CartProduct;
}

export interface Cart {
  id: number;
  items: CartItem[];
  total_items: number;
  subtotal: number;
}

interface CartContextValue {
  cart: Cart | null;
  itemCount: number;
  isLoading: boolean;
  addItem: (variantId: number, quantity: number) => Promise<void>;
  updateQuantity: (itemId: number, quantity: number) => Promise<void>;
  removeItem: (itemId: number) => Promise<void>;
  refreshCart: () => Promise<void>;
  clearCart: () => void;
}

// ─── Context ──────────────────────────────────────────────────────────────────

const CartContext = createContext<CartContextValue | null>(null);

// ─── Fetch helper (attaches auth token + sends cookies) ───────────────────────

async function cartFetch(path: string, options?: RequestInit) {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  return fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    credentials: "include", // sends the guest-cart session cookie
  });
}

// ─── Provider ─────────────────────────────────────────────────────────────────

export function CartProvider({ children }: { children: ReactNode }) {
  const [cart, setCart] = useState<Cart | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const refreshCart = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await cartFetch("/api/cart");
      if (res.ok) {
        const data = await res.json();
        setCart(data);
      }
    } catch (err) {
      console.error("Failed to load cart", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshCart();
  }, [refreshCart]);

  const addItem = useCallback(
    async (variantId: number, quantity: number) => {
      const res = await cartFetch("/api/cart/items", {
        method: "POST",
        body: JSON.stringify({ variant_id: variantId, quantity }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Failed to add item" }));
        throw new Error(err.detail || "Failed to add item");
      }
      await refreshCart();
    },
    [refreshCart]
  );

  const updateQuantity = useCallback(
    async (itemId: number, quantity: number) => {
      if (quantity < 1) {
        return removeItem(itemId);
      }
      const res = await cartFetch(`/api/cart/items/${itemId}`, {
        method: "PATCH",
        body: JSON.stringify({ quantity }),
      });
      if (!res.ok) throw new Error("Failed to update quantity");
      await refreshCart();
    },
    [refreshCart]
  );

  const removeItem = useCallback(
    async (itemId: number) => {
      // Optimistic UI — remove from local state immediately
      setCart((prev) =>
        prev
          ? {
              ...prev,
              items: prev.items.filter((i) => i.id !== itemId),
              total_items: Math.max(0, prev.total_items - 1),
            }
          : prev
      );
      const res = await cartFetch(`/api/cart/items/${itemId}`, {
        method: "DELETE",
      });
      if (!res.ok) {
        // Revert on error
        await refreshCart();
        throw new Error("Failed to remove item");
      }
      await refreshCart();
    },
    [refreshCart]
  );

  const clearCart = useCallback(() => setCart(null), []);

  const itemCount = cart?.total_items ?? 0;

  return (
    <CartContext.Provider
      value={{
        cart,
        itemCount,
        isLoading,
        addItem,
        updateQuantity,
        removeItem,
        refreshCart,
        clearCart,
      }}
    >
      {children}
    </CartContext.Provider>
  );
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useCart(): CartContextValue {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be used inside <CartProvider>");
  return ctx;
}
