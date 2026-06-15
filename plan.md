PHASE 0: Project Scaffolding & Architecture Setup
Create a new full-stack e-commerce project for a hardware/plumbing supplies shop called "Supreme Hardware Store" (placeholder name, will rename later).

TECH STACK:
- Frontend: Next.js 14+ (App Router), TypeScript, Tailwind CSS, Framer Motion
- Backend: FastAPI (Python) with SQLAlchemy ORM
- Database: PostgreSQL
- Search: PostgreSQL full-text search + RapidFuzz for fuzzy fallback
- Auth: JWT-based auth (access + refresh tokens)
- File storage: Local filesystem for now (structure code so it can swap to S3-compatible storage later)

PROJECT STRUCTURE:
- /frontend - Next.js app
- /backend - FastAPI app
  - /app/models - SQLAlchemy models
  - /app/schemas - Pydantic schemas
  - /app/routers - API route modules (products, orders, auth, cart, search, shipping)
  - /app/services - business logic (pricing, search, shipping calc)
  - /app/core - config, database session, security utils
- /docker-compose.yml for local dev (postgres + backend + frontend)
- /.env.example with all required environment variables documented

SETUP TASKS:
1. Initialize Next.js with TypeScript, Tailwind, App Router, and ESLint
2. Install Framer Motion, lucide-react (icons), and a form library (react-hook-form + zod)
3. Initialize FastAPI project with proper folder structure above
4. Set up SQLAlchemy with PostgreSQL connection via environment variables
5. Set up Alembic for database migrations
6. Create docker-compose.yml with a postgres service, and instructions to run backend/frontend separately in dev
7. Create a basic health-check endpoint (GET /health) and confirm frontend can call it
8. Set up CORS properly between frontend (localhost:3000) and backend (localhost:8000)

Do NOT implement any business logic yet. This phase is purely scaffolding. Confirm the basic stack runs end-to-end (frontend loads, calls /health, gets a response from backend, backend connects to postgres).

PHASE 1: Database Schema & Product Catalog Model
Design and implement the database schema for the hardware catalog. This must support complex multi-dimensional product variants (the way plumbing/UPVC fittings are sold).

CORE ENTITIES:

1. **Category** (hierarchical/nested)
   - id, name, slug, parent_id (self-referential for subcategories e.g. "Plumbing > UPVC Fittings > Reducer Bush")
   - image_url, description

2. **Brand**
   - id, name, slug, logo_url

3. **Product** (the "parent" item, e.g. "UPVC Reducer Bush")
   - id, name, slug, description, category_id, brand_id
   - component_type (e.g. "Reducer Bush", "Elbow", "Tee", "Coupler")
   - material (e.g. "UPVC")
   - pressure_rating (e.g. "SCH-40", "SCH-80", nullable since not all products have this)
   - is_active, created_at, updated_at
   - meta_title, meta_description (for SEO)

4. **ProductVariant** (the actual sellable SKU — size/dimension combination)
   - id, product_id, sku (unique)
   - size_label (e.g. "1½ x 1¼", "2 x 1")
   - size_dimensions (JSON field for flexible storage: {outer_dia, inner_dia, length, unit})
   - weight_grams (for shipping calc)
   - dimensions_cm (JSON: {length, width, height} — for volumetric weight calc)
   - mrp (retail price, decimal)
   - wholesale_price (decimal, nullable)
   - wholesale_min_qty (the "Box Qty" / "Pack Qty" threshold that triggers wholesale pricing)
   - stock_quantity, low_stock_threshold
   - is_active

5. **ProductImage**
   - id, product_id, variant_id (nullable — image can belong to product or specific variant), image_url, alt_text, display_order, is_primary

6. **ProductAttribute** (for flexible/extra specs not covered by core fields)
   - id, product_id, attribute_name, attribute_value (e.g. "Color: White", "Connection Type: Solvent Weld")

PRICING LOGIC REQUIREMENTS:
- Build a pricing service function `calculate_price(variant_id, quantity)` that returns MRP per unit if quantity < wholesale_min_qty, and wholesale_price per unit if quantity >= wholesale_min_qty
- Function should also return total price, savings amount, and savings percentage when wholesale applies

TASKS:
1. Create all SQLAlchemy models with proper relationships, indexes (especially on slug, sku, category_id, component_type, pressure_rating for filtering)
2. Create Alembic migration for all tables
3. Create Pydantic schemas for each model (Create, Update, Read variants)
4. Implement the pricing calculation service with unit tests covering: below threshold, at threshold, above threshold, no wholesale price set
5. Create a seed script that inserts ~15-20 sample products based on typical UPVC plumbing items (reducer bush, elbow, tee, coupler, end cap, pipe — across SCH-40/SCH-80, various fractional sizes) with realistic data so we have something to build the frontend against

Confirm migrations run cleanly and seed script populates the database correctly.

PHASE 2: Backend API — Products, Categories, Search
Build the core read-facing API endpoints for the catalog.

ENDPOINTS REQUIRED:

1. GET /api/categories
   - Returns hierarchical category tree (nested children)

2. GET /api/products
   - Paginated list of products with filters: category_id, brand_id, component_type, pressure_rating, material, min_price, max_price
   - Sort options: price_asc, price_desc, newest, name_asc
   - Each product returns: name, slug, primary image, price range (min-max across variants), category, brand, available variant count

3. GET /api/products/{slug}
   - Full product detail: all images, all variants with sizes/prices/stock, attributes, related products (same category, limit 4-6)

4. GET /api/search
   - Query param: q (search string)
   - SEARCH STRATEGY:
     a. First try PostgreSQL full-text search (tsvector/tsquery) on product name, description, component_type, attributes
     b. If full-text returns < 3 results OR query looks like it has typos, fall back to RapidFuzz fuzzy matching against a cached list of product names/component types/size labels
     c. Return matched products ranked by relevance, with a flag indicating if fuzzy matching was used
   - Must handle queries like "1.5 inch elbow sch40", "reducer bush 1 1/2 x 1 1/4", common misspellings like "elebow", "rudcer"
   - Implement query normalization: convert fractions written as "1.5" to "1½" equivalents and vice versa, normalize units (inch/in/")

5. GET /api/products/{slug}/variants/{variant_id}/price?quantity={n}
   - Returns price breakdown using the pricing service from Phase 1 (unit price, total, tier applied, savings)

TASKS:
1. Implement all endpoints with proper pagination (limit/offset or cursor-based), error handling, and response schemas
2. Add database indexes/GIN index for full-text search on relevant columns
3. Write the query normalization utility as a separate testable module (handle common fraction notations: 1/2, ½, 0.5; common unit variants)
3. Build a small RapidFuzz-based matcher service that caches product/variant names in memory and refreshes periodically
4. Write integration tests for search covering: exact match, typo, fraction notation variants, no results
5. Add basic rate limiting to /api/search to prevent abuse

Test all endpoints via the seeded data from Phase 1 and confirm search handles the typo/fraction cases correctly.

PHASE 3: Backend API — Cart, Auth, Orders
Build authentication, cart, and order management.

AUTH:
1. POST /api/auth/register (email, password, name, phone)
2. POST /api/auth/login (returns JWT access + refresh tokens)
3. POST /api/auth/refresh
4. GET /api/auth/me (current user profile)
5. Password hashing with bcrypt, JWT with reasonable expiry (access: 30min, refresh: 7 days)

USER MODEL ADDITIONS:
- User: id, email, password_hash, name, phone, is_wholesale_customer (boolean flag — affects default pricing display), created_at
- Address: id, user_id, label (Home/Work/Site), full_address, city, state, pincode, phone, is_default

CART:
- Cart can exist for both authenticated users (persisted in DB) and guests (session-based, stored in DB with a session token in a cookie — NOT in-memory/JSON files)
- CartItem: cart_id, variant_id, quantity, price_snapshot (price at time of add, for display consistency)

ENDPOINTS:
1. GET /api/cart — returns current cart (creates one if doesn't exist) with live price recalculation per item using the pricing service (so wholesale tiers update dynamically as quantity changes)
2. POST /api/cart/items — add item {variant_id, quantity}
3. PATCH /api/cart/items/{item_id} — update quantity
4. DELETE /api/cart/items/{item_id}
5. POST /api/cart/merge — merge guest cart into user cart on login

ORDERS:
- Order: id, user_id, order_number (human-readable, e.g. SHP-20260615-0001), status (pending/confirmed/processing/shipped/delivered/cancelled), subtotal, shipping_cost, total, shipping_address_id, payment_status, created_at
- OrderItem: order_id, variant_id, quantity, unit_price, total_price (snapshot at order time — never reference live prices for historical orders)

ENDPOINTS:
1. POST /api/orders — create order from current cart (validates stock, locks in prices, calculates shipping — shipping calc is a stub for now, returns flat rate, will be replaced in Phase 5)
2. GET /api/orders — list current user's orders (paginated)
3. GET /api/orders/{order_number} — order detail
4. PATCH /api/orders/{order_id}/status — admin-only, update order status

TASKS:
1. Implement all models, migrations, schemas, endpoints
2. Implement stock validation: order creation must check stock_quantity, decrement on confirmation, and fail gracefully with clear error if insufficient stock
3. Write tests for: guest cart → registered user cart merge, wholesale pricing applied correctly in cart based on quantity, order creation with stock validation, order creation with insufficient stock (should fail)
4. Add role-based access (basic admin flag on User model) for the order status update endpoint

Confirm full flow works: register → add items to cart at varying quantities (test wholesale threshold) → create order → verify stock decremented.

PHASE 4: Frontend — Storefront UI, Product Showcase & Framer Motion
Build the customer-facing storefront. This is the most visually important phase — prioritize a clean, modern, trustworthy hardware-store aesthetic (think industrial but polished: clean whites/grays, a strong accent color like safety orange or steel blue, clear typography, generous whitespace). Reference real hardware/industrial e-commerce sites for tone — not flashy, but precise and professional.

PAGES TO BUILD:

1. **Homepage**
   - Hero section with animated entrance (Framer Motion fade/slide on load)
   - "Shop by Category" grid — animated cards with hover scale/lift effect, category images
   - "Featured Products" carousel/grid — products animate in with staggered entrance (Framer Motion `staggerChildren`), hover reveals quick "Add to Cart" overlay with smooth transition
   - "New Arrivals" section, similarly animated
   - Trust badges section (e.g. "Bulk Pricing Available", "Pan-India Shipping", "Quality Assured") with subtle icon animations on scroll into view (use `whileInView`)

2. **Category/Listing Page** (/category/[slug])
   - Sidebar filters: category tree, component type, pressure rating (SCH-40/80), price range slider — filters animate open/closed on mobile (collapsible)
   - Product grid with smooth layout animations when filters change (use Framer Motion `layout` prop so grid reflows smoothly)
   - Sort dropdown
   - Pagination or infinite scroll (your choice — infinite scroll with a loading skeleton looks more modern)
   - Each product card: image (hover = secondary image crossfade), name, size range, price range, "View Options" CTA

3. **Product Detail Page** (/product/[slug])
   - Image gallery: main image with thumbnail strip, smooth crossfade transitions between images (Framer Motion AnimatePresence), pinch-zoom or click-to-zoom on main image
   - Variant selector: size/dimension options as a clean button grid (not a dropdown — these are physical dimensions, visual selection matters). Selecting a variant animates price update smoothly (animate number change)
   - Quantity selector with live price recalculation — when quantity crosses the wholesale threshold, show an animated "Wholesale pricing applied!" badge that fades/scales in, and show the per-unit savings
   - Sticky "Add to Cart" bar on mobile that appears on scroll (slide up from bottom)
   - Tabs for Description / Specifications / Shipping Info — animated tab content transitions
   - "Related Products" carousel at bottom

4. **Search Results Page** (/search)
   - Search bar with debounced live suggestions dropdown (animated open/close)
   - If fuzzy match was used, show a subtle "Showing results for 'X' (did you mean...)" note
   - Results grid same styling as category page

5. **Cart Page** (/cart)
   - Line items with quantity steppers — quantity changes animate the price update (number tween, not instant jump)
   - When an item crosses into wholesale pricing, animate a highlight/badge
   - Animated empty-cart state (illustration + CTA to shop)
   - Order summary sidebar (sticky on desktop)

6. **Checkout Page** (/checkout)
   - Multi-step form (Address → Review → Payment) with animated step transitions (slide between steps)
   - Address form with validation (react-hook-form + zod)
   - Order review summary
   - Placeholder payment step (Razorpay integration comes in Phase 6)

7. **Account Pages** (/account, /account/orders, /account/orders/[id])
   - Order history list, order detail with status timeline (animated progress indicator showing pending → confirmed → shipped → delivered)

GLOBAL COMPONENTS:
- Sticky header: logo, search bar, cart icon with animated item-count badge (bounces/scales when item added), account menu
- Mobile: bottom nav bar (Home, Search, Cart, Account) with active-state animation
- Toast notifications for "Added to cart" etc. (animated slide-in/out)
- Footer with links, contact info, trust badges

ANIMATION PRINCIPLES TO FOLLOW:
- Keep animations fast (150-300ms) and purposeful — never decorative-only or slow enough to feel sluggish
- Use `whileInView` for scroll-triggered reveals on homepage sections
- Use `layout` animations for grid reflows (filter changes, etc.)
- Use `AnimatePresence` for route transitions, modal/drawer open-close, image gallery changes
- Price changes should use a number-tween component (animate digits, not jump-cut)
- Respect `prefers-reduced-motion` — wrap animations to disable/reduce when set

TASKS:
1. Build a shared design system first: color tokens, typography scale, button/input/card components in Tailwind, all in a /components/ui folder
2. Build the global layout (header, footer, mobile nav)
3. Build pages in order: Homepage → Category → Product Detail → Search → Cart → Checkout → Account
4. Wire all pages to the Phase 2/3 backend APIs (use a typed API client, e.g. with a shared fetch wrapper + TypeScript types matching Pydantic schemas)
5. Implement loading skeletons for all data-fetching states
6. Ensure mobile responsiveness throughout — test at 375px width minimum (contractors on phones is a core use case)

Confirm the full customer journey works end-to-end against the live backend: browse → search → view product → select variant → adjust quantity to trigger wholesale pricing → add to cart → checkout flow → place order.

PHASE 5: Shipping & Logistics Integration
Implement shipping cost calculation and 3PL integration.

VOLUMETRIC WEIGHT CALCULATION:
- Implement a shipping service function that calculates billable weight per order:
  - Volumetric weight (kg) = (length_cm × width_cm × height_cm) / 5000 (standard divisor, confirm with chosen carrier's actual formula)
  - Billable weight = max(actual weight, volumetric weight) — summed across all items in the order, with consideration for whether items can be packed together or need separate boxes (simple version: sum actual weights and sum volumetric weights separately, then take the max of the two totals)
- This depends on dimensions_cm and weight_grams fields on ProductVariant from Phase 1 — if any seeded products are missing these, backfill them with realistic estimates (e.g. a 3-meter SCH-40 pipe vs. a small fitting)

3PL INTEGRATION (Shiprocket recommended for ease of India-wide courier aggregation):
1. POST /api/shipping/quote — given a cart/order and destination pincode, call Shiprocket's serviceability/rate API to return available courier options with estimated cost and delivery time
2. On order confirmation (after payment success in Phase 6):
   - POST /api/orders/{id}/ship — create the order in Shiprocket, generate AWB (waybill), assign courier
   - Store awb_code, courier_name, shipping_label_url on the Order model
3. GET /api/orders/{order_number}/tracking — fetch live tracking status from Shiprocket and return normalized status + tracking history
4. Webhook endpoint POST /api/webhooks/shiprocket — receive shipment status updates from Shiprocket, update order status accordingly (map Shiprocket statuses to internal order statuses)

TASKS:
1. Add shipping-related fields to Order model: awb_code, courier_name, shipping_label_url, tracking_status, estimated_delivery
2. Implement the volumetric weight calculation service with unit tests (test cases: single small item, single heavy item, mixed cart, very light but bulky item like a large pipe)
3. Build a Shiprocket API client wrapper (config-driven, API credentials via environment variables, with token refresh handling)
4. Implement the quote, ship, and tracking endpoints
5. Implement the webhook handler with signature verification
6. Update checkout flow (frontend) to show shipping cost dynamically once a pincode is entered, before payment
7. Update Account > Order Detail page to show tracking info and a "Track Shipment" link/timeline once shipped

Test with Shiprocket's sandbox/test credentials. Confirm: quote returns sensible cost difference between a "small fittings only" order and an "order with long pipes" order, and that the full ship → track → webhook update cycle works in sandbox.

PHASE 6: Payments Integration
Integrate Razorpay for payment processing.

FLOW:
1. POST /api/orders/{id}/create-payment — creates a Razorpay order, returns razorpay_order_id and key to frontend
2. Frontend opens Razorpay checkout widget with returned order_id
3. On success, Razorpay returns payment_id, order_id, signature to frontend
4. POST /api/orders/{id}/verify-payment — backend verifies signature using Razorpay webhook secret, updates Order.payment_status to "paid" and Order.status to "confirmed"
5. POST /api/webhooks/razorpay — webhook for async payment events (payment.captured, payment.failed, refund.processed) as a fallback/source of truth in case client-side verification is missed

REFUNDS (admin-initiated):
- POST /api/orders/{id}/refund — admin endpoint, calls Razorpay refund API, updates payment_status to "refunded" or "partially_refunded"

TASKS:
1. Add payment fields to Order: razorpay_order_id, razorpay_payment_id, payment_status (pending/paid/failed/refunded/partially_refunded)
2. Implement payment creation, verification, and webhook endpoints with proper signature verification (HMAC SHA256)
3. Wire the order creation flow (Phase 3) so it doesn't decrement stock until payment is verified — instead, reserve stock with a short expiry (e.g. 15 min) when order is created in "pending payment" state, release reservation if payment doesn't complete
4. Frontend: integrate Razorpay checkout widget in the checkout page's payment step, handle success/failure/cancel states with appropriate UI feedback and animations (success = animated checkmark, failure = clear retry CTA)
5. Build admin order detail view with a refund action

Test full flow in Razorpay test mode: place order → pay with test card → verify order moves to "confirmed" + stock decremented → confirm webhook also fires and is idempotent (doesn't double-process if both client verification and webhook arrive).

PHASE 7: Admin Dashboard
Build an admin panel for managing the store (separate route group, e.g. /admin, protected by admin role check).

PAGES:
1. **Dashboard** — key metrics: total orders, revenue (today/week/month), low-stock alerts, recent orders list
2. **Products** — CRUD for products and variants, bulk image upload, stock quantity editor, toggle active/inactive
3. **Categories** — manage category tree (drag-to-reorder nice-to-have, not required)
4. **Orders** — list with filters (status, date range), order detail with status update controls, manual shipping actions (trigger ship, view label)
5. **Customers** — list users, view order history per user, toggle is_wholesale_customer flag

TASKS:
1. Build admin auth guard (middleware checking is_admin flag, redirect if not authorized)
2. Build all CRUD interfaces using forms with validation
3. Implement bulk product import via CSV (map columns to ProductVariant fields — useful for onboarding the full Supreme UPVC catalog)
4. Add low-stock alert logic (compare stock_quantity to low_stock_threshold, surface on dashboard)
5. Keep admin UI clean and functional — minimal animation here, prioritize density and speed of data entry over visual flourish (this is a tool, not a showcase)

Confirm: admin can add a new product with multiple variants, upload images, see it appear on the storefront, update an order's status, and process a CSV bulk import of sample products.

Notes for you

Phase order matters: each phase builds on the prior one's data models. Don't skip ahead.
Phase 4 (frontend showcase) is intentionally detailed since that's your priority — the Framer Motion specifics are concrete enough that Antigravity shouldn't need to guess at "what feels premium."
CSV bulk import in Phase 7 is how you'll actually load the full Supreme UPVC catalog once it's digitized — worth planning that data format early.
Consider running Phase 5 (shipping) in Shiprocket sandbox mode for a while before going live — volumetric weight formulas and rate cards vary by carrier and you'll want to validate real costs against your actual product dimensions.

