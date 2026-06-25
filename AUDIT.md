# Supreme Hardware Store Technical Audit

Audit date: 2026-06-25  
Scope: repository root, backend FastAPI/SQLAlchemy code, migrations, tests, frontend Next.js code, config files, seed/scripts, and static product assets. Binary/image assets were inventoried but not semantically audited beyond path usage.

Severity legend: **Critical** = production blocker or exploitable risk, **Warning** = correctness/security/maintainability issue, **OK** = acceptable or implemented.

## Executive Summary

- **Critical** Backend startup is currently blocked by malformed NUL-prefixed Razorpay keys in `backend/.env`; importing `app.main` with the venv raises a Pydantic settings validation error before the API can boot.
- **Critical** `backend/.env` contains real-looking Supabase credentials and a weak JWT secret. Even if ignored by git, it is present in the project workspace and should be rotated.
- **Critical** `backend/app/routers/shipping.py` imports `get_current_user` from `app.core.security`, but that function exists in `app.routers.auth`, not `app.core.security`.
- **Critical** The checkout page has an unconditional return of an "Order Placed" UI before the real checkout form, making the normal checkout flow unreachable.
- **Critical** Payment verification decrements stock non-atomically and can double-decrement through the admin status endpoint.
- **Critical** Frontend login posts form-encoded `username/password`, but backend `/api/auth/login` expects JSON `email/password`; login is broken.
- **Warning** Several frontend cart/order interfaces do not match backend schemas, causing `itemCount`, cart lines, checkout item totals, and images to be unreliable.
- **Warning** Razorpay webhooks are not implemented/verified, Shiprocket webhook verification uses a hardcoded placeholder secret and is optional, and Shiprocket token cache is process-local only.

## 1. Architecture & Structure

- **OK** The backend has a mostly conventional separation: `routers/`, `services/`, `models/`, `schemas/`, and `core/`.
- **OK** Pricing and search logic are extracted into services; auth helpers are mostly centralized.
- **Warning** `backend/app/routers/shipping.py` is misplaced/wired inconsistently: router prefix is `"/api/shipping"` while `main.py` also includes it under `settings.API_V1_STR`, producing `/api/api/shipping`.
- **Critical** `backend/app/routers/shipping.py:19` imports auth from the wrong module.
- **Warning** `backend/app/routers/__init__.py` imports only `health, categories, products, search`; `main.py` bypasses this and imports many routers directly, making the package initializer stale.
- **Warning** `backend/app/test_parser.py`, `backend/check_db.py`, seed fix/generate/update scripts, `plan.md`, and `phases.txt` are operational/dev files mixed into the project root/backend tree. They are acceptable during development but should be moved to `scripts/` or `docs/`.
- **Warning** Router logic is heavy in `orders.py`, `cart.py`, and `payments.py`; order creation, stock mutation, payment verification, and cart merge would be safer in service-layer functions with tests.
- **Warning** No circular import was conclusively observed, but `orders.py` imports `get_variant_price` from `routers.cart`, which couples routers to each other. Move shared pricing/cart helpers into services.

## 2. Security

- **Critical** `backend/.env` contains Supabase database URLs with an embedded password and a weak `SECRET_KEY`. Rotate the DB password and JWT secret.
- **Critical** `backend/.env` has malformed NUL-prefixed duplicate Razorpay entries that break settings load.
- **Warning** `backend/app/core/config.py:8-12` includes default DB credentials and a known fallback JWT secret. Defaults should fail closed in production.
- **Warning** JWT access/refresh tokens are signed and expiring, but refresh tokens are stateless and not stored, revoked, rotated with reuse detection, or bound to a session/device.
- **OK** Admin routes found in `backend/app/routers/admin.py` require `get_current_admin_user`; `orders.py` admin status update requires `get_current_admin`; `shipping.py` checks `current_user.is_admin` for shipment creation, but the route cannot import currently.
- **Warning** Product/category/search endpoints are public, which is appropriate for catalog browsing.
- **Warning** `shipping.py` quote accepts `cart_id` or `order_id` and does not verify ownership before calculating weights. If fixed to allow optional auth/guest access, it still needs cart/session/order authorization.
- **OK** SQLAlchemy expression APIs are used broadly; the only raw SQL is parameterized order-counter SQL in `orders.py`.
- **Critical** Razorpay payment verification does not verify that `payload.razorpay_order_id` equals the order's stored `razorpay_order_id`, does not persist `razorpay_payment_id`, and does not prevent re-verification from decrementing stock again.
- **Critical** Razorpay webhook support is absent; the code relies only on client-initiated verification.
- **Critical** Shiprocket webhook signature verification is optional and uses hardcoded `"shiprocket_webhook_secret"` instead of settings.
- **Warning** `payments.py` exposes exception text from Razorpay client failures to clients.
- **Warning** `backend/app/services/shipping.py` reads Shiprocket credentials directly from `os.getenv` rather than shared settings, making behavior diverge from `config.py`.
- **Warning** Shiprocket token is cached in module globals with no locking; concurrent refreshes can stampede, and tokens are lost on process restart.
- **Warning** Guest cart cookies are `HttpOnly` and `SameSite=Lax` but not `Secure`; that is fine locally but must become secure in production.

## 3. Data Integrity

- **OK** `get_db()` rolls back on unhandled exceptions.
- **OK** Order number generation uses a PostgreSQL upsert counter and is likely atomic.
- **Critical** Stock validation at order creation checks availability but does not reserve stock. Multiple pending-payment orders can be created for the same stock.
- **Critical** Stock decrement in `payments.py:93-98` is a read-modify-write loop with no row lock or conditional update, so concurrent payment confirmations can oversell or clobber updates.
- **Critical** `payments.py:96` uses `max(0, stock - quantity)`, hiding oversell instead of failing.
- **Critical** Admin status transition in `orders.py:214-224` also decrements stock when moving into `confirmed`. Since `payments.py` sets `OrderStatus.CONFIRMED` and decrements stock, repeated verification or status workflows can corrupt stock.
- **Warning** Cart merge and add-item flows rely on unique indexes but do not handle `IntegrityError`; concurrent adds of the same variant can fail the request.
- **Warning** A user can create multiple carts because `carts.user_id` is not unique; `get_or_create_cart` uses `scalar_one_or_none()` and can fail if duplicates exist.
- **Warning** Address default handling unsets other defaults and sets the new default without an explicit unique partial index; concurrent requests can leave multiple defaults.
- **OK** Foreign keys and cascades are mostly sensible: product children cascade, carts cascade to items, order items cascade with order, order/user and order/address use `SET NULL` for history.

## 4. API Correctness

- **Critical** Backend startup is blocked by `.env`; after that is fixed, shipping import/prefix issues will still block or misroute shipping.
- **Critical** Frontend expects `/api/shipping/quote`; backend currently registers shipping under `/api/api/shipping/quote`.
- **Warning** `auth.login` expects JSON `LoginRequest`, but frontend sends form data.
- **Warning** Error responses are standard FastAPI `detail` objects but not normalized into a consistent app error schema.
- **Warning** `orders.get_order_detail` route is `/{order_number}` while status route is `/{order_id}/status`; the static `/status` suffix avoids ambiguity, but mixed identifiers make client code error-prone.
- **Warning** `OrderCreate` generated frontend type omits `shipping_cost` and `shipping_service` in `types/api.d.ts`, so generated types are stale relative to backend schema.
- **Warning** Payment endpoints are absent from `frontend/types/api.d.ts`, indicating OpenAPI types are stale or generated before payments were added.
- **Warning** Delete endpoints return `200` with a body; acceptable but `204` would be cleaner for simple deletes.
- **OK** Cart to order flow is wired in backend: cart items become order items, cart is cleared, payment can mark the order paid.
- **Warning** Order to payment is only partially wired: payment ID is not saved and no Payment model/table exists despite the requested relationship `order -> payment`.

## 5. Frontend Quality

- **Critical** `frontend/app/checkout/page.tsx:298-334` returns an order-placed screen unconditionally for authenticated users before declaring `steps`; the actual checkout form is unreachable.
- **Critical** `frontend/lib/auth.ts:58-67` posts form-encoded login credentials; backend expects JSON.
- **Warning** `frontend/lib/cart.tsx:28-43` defines cart items as `unit_price`, `total_price`, `variant`, `product`, and `total_items`; backend returns `live_price`, `product_name`, `sku`, `size_label`, `primary_image_url`, and `item_count`.
- **Warning** Cart removal decrements `total_items` by 1 instead of the removed item's quantity.
- **Warning** `Header` only checks auth on mount; login/logout in other tabs or token expiry are not reflected until refresh.
- **Warning** Login/register merge carts manually with direct `fetch` instead of using shared API helpers.
- **Warning** Loading/error states exist on many pages, but not consistently. Admin products/orders catch errors only in console; cart refresh silently swallows failures.
- **Warning** Extensive `any` usage remains in production pages: search, category, home, product, account, account orders, checkout, admin metric card, and header suggestions.
- **Warning** Multiple production pages use `<img>` instead of Next `<Image>`: search, cart, checkout, account order detail, product thumbnails/gallery, and home category images.
- **Warning** Product page image pathing prepends `/products/` to `image_url`; seed data must be consistent or images will break. Some pages expect `primary_image`, others `primary_image_url`.
- **Warning** Razorpay SDK is loaded with Next `Script`, which is safer than manual script injection, but code does not check that `window.Razorpay` exists before constructing it, and no cleanup is needed/implemented for event handlers.
- **Warning** The checkout success UI is duplicated.
- **OK** `openapi-fetch` client is instantiated once in `frontend/lib/api.ts` and reused where used.

## 6. Performance

- **OK** Important indexes exist for slugs, product active/category filters, search vector, variants, carts, cart items, and order listing.
- **Warning** No index exists on `orders.awb_code`, but webhook lookup queries by AWB.
- **Warning** No index exists on `orders.razorpay_order_id`, useful for payment/webhook reconciliation.
- **Warning** Product list joins `ProductImage` on `is_primary`; if data has multiple primary images per product, rows can duplicate. Enforce one primary image per product or use a lateral/subquery.
- **OK** Main list/detail queries use aggregate subqueries and `selectinload`, so major catalog N+1 issues are mostly avoided.
- **Warning** Search fuzzy fallback loads all products/variants into process memory. Fine for small catalog, but needs invalidation and pagination strategy as catalog grows.
- **Warning** Admin metrics run four separate aggregate queries; acceptable now, but can be combined later.
- **Warning** Many frontend images use `<img>`, bypassing Next image optimization, sizing, and layout stabilization.

## 7. Testing Coverage

- **OK** `backend/tests/test_pricing.py` covers pricing tiers, rounding, invalid quantities, and savings.
- **OK** `backend/tests/test_search_service.py` covers query normalization and fuzzy matching.
- **OK** `backend/tests/test_catalog_api.py` covers categories, product listing/detail, variant pricing, and search.
- **OK** `backend/tests/test_orders_cart_auth.py` covers register/login/profile/refresh, address CRUD, cart operations/merge, wholesale cart pricing, order creation, admin stock status transitions, and order number concurrency.
- **Critical** No tests cover Razorpay signature verification, replay/idempotency, mismatched Razorpay order IDs, saving payment IDs, or stock decrement on payment confirmation.
- **Critical** No tests cover concurrent payment confirmations or atomic stock decrement.
- **Warning** No tests cover shipping quote/ship/track, Shiprocket webhook signature handling, or Shiprocket token refresh.
- **Warning** No tests cover admin metrics/order listing.
- **Warning** No frontend tests are present for login, cart context mapping, checkout, Razorpay SDK loading, or admin route guard.
- **Warning** Running `python -c "import app.main"` with the venv currently fails due to malformed `.env`, so the test suite is likely blocked in the current local environment.

## 8. Bugs & Broken Wiring

### TODOs, Placeholders, Mocks In Production Paths

- **Critical** `backend/.env` contains placeholder Razorpay keys encoded with NUL bytes and real-looking database credentials.
- **Warning** `backend/app/services/shipping.py` falls back to mock shipping quotes and mock AWB generation whenever credentials are missing.
- **Warning** `backend/app/services/shipping.py` has hardcoded Shiprocket API base and pickup postcode.
- **Critical** `backend/app/routers/shipping.py` hardcodes webhook signature secret.
- **Warning** `frontend/app/cart/page.tsx` uses flat-rate shipping placeholder.
- **Warning** `frontend/app/product/[slug]/page.tsx` uses `placehold.co` fallback image in product UI.
- **Warning** `backend/app/seed.py` is sample seed data, acceptable for development but not production runtime.
- **Warning** `backend/app/test_parser.py` references a local Excel filename and should not be production code.

### Imports Referencing Missing/Wrong Files or Symbols

- **Critical** `backend/app/routers/shipping.py:19` imports `get_current_user` from `app.core.security`; the symbol is in `app.routers.auth`.
- **Warning** `backend/app/routers/__init__.py` is stale and does not re-export all router modules used by `main.py`.
- **Warning** `backend/requirements.txt` contains a NUL-encoded `razorpay>=1.4.1` line, which may break clean installs.

### Schema/Model/Client Field Mismatches

- **Warning** Frontend generated `OrderCreate` type lacks `shipping_cost` and `shipping_service`, while backend schema accepts them.
- **Warning** Frontend generated OpenAPI types lack payment endpoints.
- **Warning** Frontend cart types expect `total_items`, but backend returns `item_count`.
- **Warning** Frontend cart item types expect nested `product` and `variant` objects plus `unit_price`/`total_price`, but backend returns flattened product/variant labels and `live_price`.
- **Warning** Backend `Order` has `razorpay_payment_id`, but `payments.py` never sets it and `OrderRead` does not expose it.
- **Warning** There is no Payment model/table, so the requested `order -> payment` relationship is not modeled end-to-end.

## Prioritized Fix List

1. **Critical** Rotate the exposed Supabase password and JWT secret; remove `backend/.env` from any sharing path and recreate it without NUL bytes.
2. **Critical** Fix `backend/requirements.txt` NUL corruption and install/verify dependencies from a clean venv.
3. **Critical** Fix `shipping.py` import to use `app.routers.auth.get_current_user`, change router prefix to `"/shipping"`, and verify backend startup.
4. **Critical** Fix frontend login to send JSON `{ email, password }` or change backend to accept OAuth2 form data consistently.
5. **Critical** Remove the unconditional checkout success return and restore the real checkout flow.
6. **Critical** Make payment confirmation idempotent: verify stored Razorpay order ID, persist payment ID, reject replay, and avoid decrementing stock twice.
7. **Critical** Implement atomic stock decrement with row locks or conditional SQL updates, and decide whether stock is reserved at order creation or only captured after payment.
8. **Critical** Add tests for Razorpay signature verification, payment replay, mismatched order IDs, and concurrent stock decrement.
9. **Warning** Replace Shiprocket webhook hardcoded/optional signature verification with a configured required secret; add webhook tests.
10. **Warning** Normalize cart API response types in the frontend to backend `CartRead`, regenerate OpenAPI types, and remove stale hand-written cart fields.
11. **Warning** Add DB constraints/indexes: unique user cart or active cart invariant, AWB index, Razorpay order ID index, and default-address uniqueness strategy.
12. **Warning** Move shared router helper logic into services and remove router-to-router dependencies.
13. **Warning** Replace remaining production `<img>` usages with Next `<Image>` where dimensions are known.
14. **Warning** Add frontend smoke tests for login, cart badge/count, checkout page rendering, and admin guard.
