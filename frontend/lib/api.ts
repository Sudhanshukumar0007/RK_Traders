import { paths } from "@/types/api";
import createClient from "openapi-fetch";

// The generated types are in @/types/api
// This creates a typed client instance

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export const client = createClient<paths>({ baseUrl: API_BASE_URL });

export function getAuthToken() {
  if (typeof window !== "undefined") {
    return localStorage.getItem("access_token");
  }
  return null;
}

// Interceptor to inject the token into requests
client.use({
  onRequest({ request }) {
    const token = getAuthToken();
    if (token) {
      request.headers.set("Authorization", `Bearer ${token}`);
    }
    return request;
  },
});
