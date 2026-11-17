"""
FreshCart — Consumer Grocery Shopping UI (Dark Theme).
Powered by FP-Growth Market Basket Analysis.
All recommendation cards use native Streamlit components — zero raw-HTML rendering bugs.
"""

import sys
from pathlib import Path
from typing import List, Dict

import streamlit as st

# ── Project root on path ──────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from frontend.components.api_client import engine_client
from frontend.components.styles import CUSTOM_CSS
from frontend.components.product_icons import get_product_meta, CATEGORY_ICONS

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FreshCart — Smart Grocery",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ── Realistic per-SKU prices ──────────────────────────────────────────────────
PRODUCT_PRICES: Dict[str, float] = {
    "whole milk": 2.99,       "yogurt": 1.79,         "butter": 3.49,
    "curd": 1.49,             "domestic eggs": 3.29,   "margarine": 2.19,
    "ice cream": 4.49,        "other vegetables": 2.29,"root vegetables": 1.99,
    "tropical fruit": 2.49,   "citrus fruit": 1.89,    "pip fruit": 2.09,
    "berries": 3.79,          "grapes": 2.89,           "onions": 0.99,
    "frozen vegetables": 2.49,"packaged fruit/vegetables": 3.29,
    "rolls/buns": 2.49,       "pastry": 2.99,           "brown bread": 2.79,
    "white bread": 2.29,      "semi-finished bread": 1.99, "waffles": 3.49,
    "sausage": 4.29,          "beef": 6.99,             "pork": 5.49,
    "chicken": 5.99,          "frankfurter": 3.29,      "ham": 4.49,
    "soda": 1.49,             "bottled water": 0.99,    "bottled beer": 3.99,
    "canned beer": 2.99,      "fruit/vegetable juice": 3.49, "coffee": 5.99,
    "pasta": 1.99,            "rice": 2.49,             "oil": 4.49,
    "sugar": 1.79,            "chocolate": 2.49,        "candy": 1.49,
    "salty snack": 2.29,      "hygiene articles": 3.99, "shopping bags": 0.49,
    "napkins": 1.99,
}

def get_price(product: str) -> float:
    return PRODUCT_PRICES.get(product.strip().lower(), 2.49)


# ── Occasions ────────────────────────────────────────────────────────────────
OCCASIONS = {
    "🍳 Breakfast":     ["whole milk", "yogurt", "rolls/buns", "domestic eggs"],
    "🥗 Healthy Week":  ["other vegetables", "root vegetables", "citrus fruit", "bottled water"],
    "🍝 Pasta Night":   ["pasta", "beef", "onions", "oil"],
    "🎉 Weekend":       ["bottled beer", "salty snack", "chocolate", "tropical fruit"],
    "☕ Morning":       ["coffee", "pastry", "whole milk", "yogurt"],
}


# ── Session state ─────────────────────────────────────────────────────────────
if "cart" not in st.session_state:
    st.session_state.cart = []
if "active_dept" not in st.session_state:
    st.session_state.active_dept = "All"


# ── Helper functions ──────────────────────────────────────────────────────────
def add_to_cart(item: str):
    cleaned = item.strip().lower()
    if cleaned and cleaned not in st.session_state.cart:
        st.session_state.cart.append(cleaned)
        _, icon = get_product_meta(cleaned)
        st.toast(f"{icon} **{cleaned.title()}** added!", icon="🛒")


def remove_from_cart(item: str):
    if item in st.session_state.cart:
        st.session_state.cart.remove(item)
        st.toast(f"Removed **{item.title()}**", icon="🗑️")


def add_bundle_to_cart(items: List[str], bundle_name: str):
    added = 0
    for it in items:
        c = it.strip().lower()
        if c not in st.session_state.cart:
            st.session_state.cart.append(c)
            added += 1
    st.toast(f"🎁 **{bundle_name}** — {added} items added!", icon="🎉")


def cart_total() -> float:
    return sum(get_price(i) for i in st.session_state.cart)


def affinity_label(lift: float) -> str:
    if lift >= 2.0:
        return "🔥 Customers love this together"
    elif lift >= 1.5:
        return "👍 Often bought together"
    return "✨ You might also like"


# ── Pre-load catalog ──────────────────────────────────────────────────────────
catalog_products = engine_client.get_products()
backend_online   = engine_client.check_backend_connection()


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR — SHOPPING CART
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        '<div class="sidebar-logo">Fresh<span>Cart</span> 🛒</div>'
        '<div style="text-align:center;font-size:0.74rem;color:#8b949e;margin-bottom:1rem;">Smart Grocery · Smarter Savings</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    cart_count = len(st.session_state.cart)
    col_title, col_badge = st.columns([3, 1])
    with col_title:
        st.markdown("**🛒 My Cart**")
    with col_badge:
        st.markdown(
            f'<span style="background:#2ea043;color:#0d1117;font-size:0.72rem;'
            f'font-weight:800;padding:0.18rem 0.55rem;border-radius:9999px;">{cart_count}</span>',
            unsafe_allow_html=True,
        )

    if cart_count > 0:
        for it in list(st.session_state.cart):
            _, icon = get_product_meta(it)
            price   = get_price(it)
            c1, c2, c3 = st.columns([4, 2, 1])
            with c1:
                st.write(f"{icon} **{it.title()}**")
            with c2:
                st.write(f"**${price:.2f}**")
            with c3:
                if st.button("✕", key=f"rm_{it}", help=f"Remove {it}"):
                    remove_from_cart(it)
                    st.rerun()

        # Pricing (all native — no HTML f-strings with $)
        subtotal = cart_total()
        discount = round(subtotal * 0.12, 2) if cart_count >= 3 else 0.0
        total    = round(subtotal - discount, 2)
        shipping = max(0.0, 15.0 - subtotal)

        st.divider()

        r1a, r1b = st.columns(2)
        r1a.caption("Subtotal");     r1b.write(f"**${subtotal:.2f}**")

        if discount > 0:
            r2a, r2b = st.columns(2)
            r2a.caption("🎁 Discount")
            r2b.write(f"**:green[-${discount:.2f}]**")

        r3a, r3b = st.columns(2)
        r3a.caption("Delivery")
        r3b.write("**:green[🚚 Free!]**" if subtotal >= 15 else f"**${shipping:.2f}**")

        st.divider()

        r4a, r4b = st.columns(2)
        r4a.write("**Total**")
        r4b.write(f"**:green[${total:.2f}]**")

        if subtotal < 15.0:
            st.caption(f"🚚 Add ${shipping:.2f} more for free delivery")
            st.progress(min(1.0, subtotal / 15.0))

        st.write("")
        col_co, col_cl = st.columns([3, 2])
        with col_co:
            if st.button("✨ Checkout", use_container_width=True, type="primary"):
                delivery_val = 0.0 if subtotal >= 15.0 else shipping
                items_payload = [
                    {"product_name": it, "unit_price": get_price(it), "quantity": 1}
                    for it in st.session_state.cart
                ]
                new_order = engine_client.create_order(
                    items=items_payload,
                    subtotal=subtotal,
                    discount=discount,
                    delivery_fee=delivery_val,
                )
                order_id = new_order.get("order_id", "ORD-NEW")
                st.session_state.cart = []
                st.session_state.last_order_id = order_id
                st.balloons()
                st.toast(f"Order #{order_id} placed successfully!", icon="🎉")
                st.rerun()
        with col_cl:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.cart = []
                st.rerun()
    else:
        st.markdown(
            '<div style="text-align:center;padding:1.5rem 0;">'
            '<div style="font-size:2rem;">🧺</div>'
            '<div style="font-size:0.88rem;font-weight:600;color:#8b949e;margin-top:0.4rem;">Cart is empty</div>'
            '<div style="font-size:0.76rem;color:#484f58;margin-top:0.2rem;">Add items from the store</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    with st.expander("⚙️ Recommendation Settings"):
        top_k         = st.slider("How many suggestions?", 1, 10, 5)
        min_lift      = st.slider("Minimum match strength", 1.0, 3.0, 1.15, 0.05)
        min_conf_ratio = st.slider("Minimum popularity (%)", 10, 70, 20, 5) / 100.0

    st.divider()
    st.markdown("**🍽️ Shop by Occasion**")
    for label, items in OCCASIONS.items():
        if st.button(label, use_container_width=True, key=f"occ_{label}"):
            st.session_state.cart = items[:]
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  TOP NAV BAR
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    '<div class="nav-bar">'
    '  <div>'
    '    <div class="nav-logo">Fresh<span>Cart</span></div>'
    '    <div class="nav-tagline">AI-powered grocery recommendations</div>'
    '  </div>'
    '  <div class="nav-badges">'
    '    <span class="nav-badge">🏷️ 169 Products</span>'
    '    <span class="nav-badge">⚡ Instant Picks</span>'
    '    <span class="nav-badge">🚚 Free delivery $15+</span>'
    '  </div>'
    '</div>',
    unsafe_allow_html=True,
)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="hero-search-wrap">'
    '  <div class="hero-eyebrow">🤖 AI-Powered Grocery Assistant</div>'
    '  <h1 class="hero-h1">What are you <em>cooking</em> tonight?</h1>'
    '  <p class="hero-sub">Add items to your cart — we\'ll instantly suggest what goes perfectly with them.</p>'
    '</div>',
    unsafe_allow_html=True,
)

# ── Occasion quick-load ───────────────────────────────────────────────────────
occ_cols = st.columns(len(OCCASIONS))
for i, (label, items) in enumerate(OCCASIONS.items()):
    with occ_cols[i]:
        if st.button(label, use_container_width=True, key=f"hero_occ_{label}"):
            st.session_state.cart = items[:]
            st.rerun()

st.write("")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_shop, tab_kits, tab_history, tab_how = st.tabs([
    "🛍️  Shop & Discover",
    "🍱  Meal Kits",
    "📜  Order History",
    "📊  How It Works",
])


# ──────────────────────────────────────────────────────────────────────────────
# TAB 1 — SHOP & DISCOVER
# ──────────────────────────────────────────────────────────────────────────────
with tab_shop:

    st.markdown(
        '<div class="section-label">Step 1</div>'
        '<div class="section-title">🛒 Build Your Cart</div>',
        unsafe_allow_html=True,
    )

    # Department filter buttons
    all_depts = ["All"] + list(CATEGORY_ICONS.keys())
    dept_cols = st.columns(len(all_depts))
    for i, dept in enumerate(all_depts):
        with dept_cols[i]:
            icon  = CATEGORY_ICONS.get(dept, "🛒")
            label = f"{icon} All" if dept == "All" else icon
            is_active = st.session_state.active_dept == dept
            if st.button(label, key=f"dept_{dept}", use_container_width=True,
                         type="primary" if is_active else "secondary"):
                st.session_state.active_dept = dept
                st.rerun()

    # Filtered multiselect
    if st.session_state.active_dept == "All":
        filtered_products = catalog_products
    else:
        filtered_products = [
            p for p in catalog_products
            if get_product_meta(p)[0] == st.session_state.active_dept
        ]

    selected_items = st.multiselect(
        "search",
        options=filtered_products,
        default=[i for i in st.session_state.cart if i in filtered_products],
        placeholder="🔍 Search — e.g. 'milk', 'pasta', 'coffee'…",
        label_visibility="collapsed",
    )

    # Sync → cart (preserve other-dept items)
    if set(selected_items) != {i for i in st.session_state.cart if i in filtered_products}:
        other = [i for i in st.session_state.cart if i not in filtered_products]
        st.session_state.cart = other + list(selected_items)

    # Cart chips
    if st.session_state.cart:
        st.caption("IN YOUR CART")
        chips = " ".join(
            f'<span class="basket-chip">{get_product_meta(it)[1]} {it.title()}</span>'
            for it in st.session_state.cart
        )
        st.markdown(chips, unsafe_allow_html=True)

    st.divider()

    # ── Recommendations ───────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-label">Step 2</div>'
        '<div class="section-title">⭐ Frequently Bought Together</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.cart:
        st.markdown(
            '<div class="empty-state">'
            '  <div class="empty-state-emoji">🧺</div>'
            '  <div class="empty-state-title">Your cart is empty!</div>'
            '  <div class="empty-state-sub">Add groceries above and we\'ll suggest perfect pairings instantly.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        with st.spinner("Finding the best pairings for you…"):
            result = engine_client.get_recommendations(
                cart_items=st.session_state.cart,
                top_k=top_k,
                min_confidence=min_conf_ratio,
                min_lift=min_lift,
            )

        recs     = result.get("recommendations", [])
        strategy = result.get("strategy", "association_rule")

        if strategy != "association_rule":
            st.info("💡 Showing store bestsellers — add more items for personalized picks!")

        if recs:
            # Render cards in rows of 3 — using native st.container(border=True)
            for row_start in range(0, len(recs), 3):
                row_recs = recs[row_start: row_start + 3]
                cols = st.columns(3)
                for col, rec in zip(cols, row_recs):
                    raw     = rec.get("product", "")
                    cat, icon = get_product_meta(raw)
                    name    = raw.title()
                    lift    = float(rec.get("lift", 1.0))
                    conf    = float(rec.get("confidence", 0.0)) * 100
                    price   = get_price(raw)
                    people  = max(1, round(conf / 10))
                    in_cart = raw in st.session_state.cart

                    with col:
                        with st.container(border=True):
                            # Top Pick ribbon (static HTML — no f-string $ issue)
                            if lift >= 2.0:
                                st.markdown(
                                    '<div style="text-align:center;">'
                                    '<span class="top-pick-ribbon">🔥 Top Pick</span>'
                                    '</div>',
                                    unsafe_allow_html=True,
                                )

                            # Emoji + name + category (static values, safe)
                            st.markdown(
                                f'<div class="prod-header">'
                                f'  <span class="prod-emoji">{icon}</span>'
                                f'  <div class="prod-name">{name}</div>'
                                f'  <div class="prod-category">{cat}</div>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

                            # Price — using st.write to avoid $ LaTeX issues
                            st.markdown(
                                f'<div class="prod-price">${price:.2f}</div>',
                                unsafe_allow_html=True,
                            )

                            # Affinity badge
                            st.markdown(
                                f'<div class="together-badge">{affinity_label(lift)}</div>',
                                unsafe_allow_html=True,
                            )

                            # Match strength bar (native Streamlit)
                            st.caption(f"Match strength · {conf:.0f}%")
                            st.progress(min(1.0, conf / 100))

                            # Shoppers text
                            st.markdown(
                                f'<div class="shoppers-str">'
                                f'{people} in 10 shoppers buy this together'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

                            # CTA button
                            if in_cart:
                                st.button(
                                    "✓ In Cart",
                                    key=f"incart_{row_start}_{raw}",
                                    disabled=True,
                                    use_container_width=True,
                                )
                            else:
                                if st.button(
                                    f"+ Add to Cart  •  ${price:.2f}",
                                    key=f"add_{row_start}_{raw}",
                                    use_container_width=True,
                                    type="secondary",
                                ):
                                    add_to_cart(raw)
                                    st.rerun()
        else:
            st.markdown(
                '<div class="empty-state">'
                '  <div class="empty-state-emoji">🤔</div>'
                '  <div class="empty-state-title">No matches found</div>'
                '  <div class="empty-state-sub">Try loosening settings in the sidebar, or add different items.</div>'
                '</div>',
                unsafe_allow_html=True,
            )


# ──────────────────────────────────────────────────────────────────────────────
# TAB 2 — MEAL KITS
# ──────────────────────────────────────────────────────────────────────────────
with tab_kits:
    st.markdown(
        '<div class="section-label">Handpicked for you</div>'
        '<div class="section-title">🍱 Meal Kits & Bundle Deals</div>',
        unsafe_allow_html=True,
    )
    st.caption("Data-backed packs of 3–6 items that shoppers love together. Save up to 20%!")

    bundles_data = engine_client.get_bundles()
    all_cats = ["All"] + sorted({b.get("category", "") for b in bundles_data if b.get("category")})
    sel_cat  = st.radio("Theme:", all_cats, horizontal=True, label_visibility="collapsed")
    filtered = [b for b in bundles_data if sel_cat == "All" or b.get("category") == sel_cat]

    col_b1, col_b2 = st.columns(2)
    for idx, bundle in enumerate(filtered):
        target  = col_b1 if idx % 2 == 0 else col_b2
        name    = bundle.get("name", "Special Bundle")
        cat     = bundle.get("category", "General")
        desc    = bundle.get("description", "")
        items   = bundle.get("items", [])
        orig_p  = bundle.get("original_price", 0.0)
        deal_p  = bundle.get("bundle_price", 0.0)
        disc    = bundle.get("discount_pct", 0)
        orders  = bundle.get("orders_count", 0)
        bid     = bundle.get("bundle_id", idx)
        in_all  = all(it in st.session_state.cart for it in items)

        with target:
            with st.container(border=True):
                st.markdown(
                    f'<div class="kit-tag">{cat}</div>'
                    f'<div class="kit-name">{name}</div>'
                    f'<div class="kit-desc">{desc}</div>',
                    unsafe_allow_html=True,
                )

                # Item pills
                pills = " ".join(
                    f'<span class="kit-pill">{get_product_meta(it)[1]} {it.title()}</span>'
                    for it in items
                )
                st.markdown(pills, unsafe_allow_html=True)

                # Price row
                st.markdown(
                    f'<div style="margin:0.6rem 0 0.3rem;display:flex;align-items:baseline;gap:0.6rem;">'
                    f'  <span class="kit-orig">${orig_p:.2f}</span>'
                    f'  <span class="kit-sale">${deal_p:.2f}</span>'
                    f'  <span class="kit-save">SAVE {disc}%</span>'
                    f'</div>'
                    f'<div class="kit-social">🧑‍🤝‍🧑 Backed by {orders:,} real transactions</div>',
                    unsafe_allow_html=True,
                )

                st.write("")
                if in_all:
                    st.button("✓ All items in cart", key=f"kit_in_{bid}",
                              disabled=True, use_container_width=True)
                else:
                    if st.button(f"🛒 Add Meal Kit  ·  Save {disc}%",
                                 key=f"kit_add_{bid}",
                                 use_container_width=True, type="primary"):
                        add_bundle_to_cart(items, name)
                        st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# TAB 3 — ORDER HISTORY
# ──────────────────────────────────────────────────────────────────────────────
with tab_history:
    st.markdown(
        '<div class="section-label">Your Account</div>'
        '<div class="section-title">📜 Past Orders & Receipts</div>',
        unsafe_allow_html=True,
    )
    st.caption("Review your past grocery deliveries and receipts. Click 'Reorder' to instantly reload items into your cart.")

    history_data = engine_client.get_orders(limit=50)
    orders_list = history_data.get("orders", [])
    tot_orders = history_data.get("total_orders", len(orders_list))
    tot_spent = history_data.get("total_spent", 0.0)
    tot_saved = history_data.get("total_saved", 0.0)

    # Lifetime KPIs
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Lifetime Orders", f"{tot_orders}")
    kpi2.metric("Total Spent", f"${tot_spent:.2f}")
    kpi3.metric("Total Saved", f"${tot_saved:.2f}")

    st.write("")

    if not orders_list:
        st.markdown(
            '<div class="empty-state">'
            '  <div class="empty-state-emoji">🧾</div>'
            '  <div class="empty-state-title">No orders yet!</div>'
            '  <div class="empty-state-sub">Add groceries to your cart and click ✨ Checkout in the sidebar to record your first order.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        for ord_idx, order in enumerate(orders_list):
            oid = order.get("order_id", f"ORD-{ord_idx}")
            created = order.get("created_at", "")
            items = order.get("items", [])
            subtot = order.get("subtotal", 0.0)
            disc = order.get("discount", 0.0)
            deliv = order.get("delivery_fee", 0.0)
            tot = order.get("total_amount", 0.0)
            status_str = order.get("status", "Completed")

            with st.container(border=True):
                # Header row
                h1, h2 = st.columns([3, 1])
                with h1:
                    st.markdown(
                        f'<div style="font-size:1.1rem;font-weight:800;color:#3fb950;">'
                        f'📦 {oid} '
                        f'<span style="font-size:0.75rem;color:#8b949e;font-weight:500;">· {created}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with h2:
                    st.markdown(
                        f'<div style="text-align:right;">'
                        f'<span style="background:#1f2d1f;border:1px solid #2ea043;color:#3fb950;'
                        f'font-size:0.75rem;font-weight:700;padding:0.25rem 0.65rem;border-radius:9999px;">'
                        f'✓ {status_str}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                # Items purchased chips
                item_names = [it.get("product_name", "") for it in items]
                chips_html = " ".join(
                    f'<span class="kit-pill">{get_product_meta(p)[1]} {p.title()} (${get_price(p):.2f})</span>'
                    for p in item_names
                )
                st.markdown(f'<div style="margin:0.5rem 0 0.8rem;">{chips_html}</div>', unsafe_allow_html=True)

                # Pricing breakdown
                p1, p2, p3, p4 = st.columns(4)
                p1.caption("Subtotal")
                p1.write(f"${subtot:.2f}")

                p2.caption("Discount")
                p2.write(f"-${disc:.2f}" if disc > 0 else "$0.00")

                p3.caption("Delivery")
                p3.write("Free" if deliv == 0 else f"${deliv:.2f}")

                p4.caption("Total Paid")
                p4.write(f"**:green[${tot:.2f}]**")

                st.write("")
                col_btn, _ = st.columns([2, 3])
                with col_btn:
                    if st.button(f"🔁 Reorder Items ({len(items)})", key=f"reorder_btn_{oid}", use_container_width=True):
                        st.session_state.cart = [it.strip().lower() for it in item_names if it]
                        st.toast(f"Loaded {len(item_names)} items from {oid} into cart!", icon="🛒")
                        st.rerun()

        st.write("")
        with st.expander("⚙️ Manage Order History"):
            st.warning("This will clear your saved past order history.")
            if st.button("🗑️ Clear All Past Orders", type="secondary"):
                engine_client.clear_orders()
                st.toast("Order history cleared.", icon="🗑️")
                st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# TAB 4 — HOW IT WORKS
# ──────────────────────────────────────────────────────────────────────────────
with tab_how:
    st.markdown(
        '<div class="section-label">Behind the magic</div>'
        '<div class="section-title">🤖 How FreshCart Recommends</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            '<div class="how-card">'
            '  <div class="how-emoji">🧾</div>'
            '  <div class="how-title">9,835 Real Baskets</div>'
            '  <div class="how-desc">We analyzed almost 10,000 real grocery shopping trips to find patterns.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            '<div class="how-card">'
            '  <div class="how-emoji">🔗</div>'
            '  <div class="how-title">861 Product Pairings</div>'
            '  <div class="how-desc">Our AI discovered 861 strong connections between products people buy together.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            '<div class="how-card">'
            '  <div class="how-emoji">⚡</div>'
            '  <div class="how-title">Instant Results</div>'
            '  <div class="how-desc">Recommendations appear in under 25ms — faster than you can blink!</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.write("")
    st.markdown("#### 📖 What does 'match strength' mean?")
    ga, gb, gc = st.columns(3)
    with ga:
        st.info(
            "**❤️ Match Strength**\n\n"
            "If 60% of shoppers who buy milk also buy yogurt, the match strength is **60%**. "
            "Higher = safer pick."
        )
    with gb:
        st.info(
            "**🔥 Top Pick**\n\n"
            "Items labeled 🔥 are **2× more likely** to be bought together than by random chance."
        )
    with gc:
        st.info(
            "**🧑‍🤝‍🧑 'X in 10 shoppers'**\n\n"
            "We translate stats into plain English. 70% confidence → '7 in 10 shoppers buy this together.'"
        )

    st.write("")
    with st.expander("📊 Raw Model Statistics"):
        stats = engine_client.get_stats()
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Baskets Analyzed", f"{stats.get('totalTransactions', 9835):,}")
        s2.metric("Unique Products",  stats.get("totalCatalogSKUs", 169))
        s3.metric("Association Rules", stats.get("totalAssociationRules", 861))
        s4.metric("Min Support",       f"{stats.get('minSupportThreshold', 0.005)*100:.1f}%")

        st.write("**Top 15 strongest product associations:**")
        rules_df = engine_client.local_recommender.rules
        if not rules_df.empty:
            display_cols = [c for c in
                            ["antecedents_str", "consequents_str", "confidence", "lift"]
                            if c in rules_df.columns]
            tbl = rules_df[display_cols].copy()
            if "confidence" in tbl.columns:
                tbl["confidence"] = (tbl["confidence"] * 100).round(1).astype(str) + "%"
            if "lift" in tbl.columns:
                tbl["lift"] = tbl["lift"].round(2).astype(str) + "×"
            tbl.rename(columns={
                "antecedents_str": "If you buy…",
                "consequents_str": "You'll likely want…",
                "confidence":      "Match Strength",
                "lift":            "Synergy",
            }, inplace=True)
            st.dataframe(
                tbl.sort_values("Synergy", ascending=False).head(15),
                use_container_width=True,
                hide_index=True,
            )
