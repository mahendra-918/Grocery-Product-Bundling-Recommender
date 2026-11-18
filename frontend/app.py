"""
FreshCart — Consumer Grocery Shopping UI (Dark Theme).
Powered by FP-Growth Market Basket Analysis.
All recommendation cards use native Streamlit components — zero raw-HTML rendering bugs.
"""

import sys
from collections import Counter
from html import escape
from pathlib import Path
from typing import List, Dict

import streamlit as st

# ── Project root on path ──────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from frontend.components.api_client import AccountRequestError, engine_client
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


CATALOG_PAGE_SIZE = 8
EVERYDAY_GROCERIES = (
    "whole milk", "white bread", "domestic eggs", "yogurt",
    "citrus fruit", "root vegetables", "pasta", "coffee",
)


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
    st.session_state.cart = {}
elif isinstance(st.session_state.cart, list):
    st.session_state.cart = dict(Counter(st.session_state.cart))
if "cart_kits" not in st.session_state:
    st.session_state.cart_kits = {}
if "catalog_page" not in st.session_state:
    st.session_state.catalog_page = 0


# ── Helper functions ──────────────────────────────────────────────────────────
def add_to_cart(item: str, *, show_toast: bool = True):
    cart = st.session_state.cart
    cart[item] = cart.get(item, 0) + 1
    if show_toast:
        _, icon = get_product_meta(item)
        st.toast(f"{icon} **{item.title()}** added!", icon="🛒")


def remove_one_from_cart(item: str):
    cart = st.session_state.cart
    if cart[item] == 1:
        del cart[item]
    else:
        cart[item] -= 1


def replace_cart(items: Dict[str, int]):
    st.session_state.cart = items
    st.session_state.cart_kits = {}


def apply_meal_kit(bundle_id: str, items: List[str], name: str, savings_cents: int):
    for item in items:
        st.session_state.cart.setdefault(item, 1)
    st.session_state.cart_kits[bundle_id] = (set(items), name, savings_cents)
    st.toast(f"{name} deal applied", icon="🎉")


def reset_catalog_page():
    st.session_state.catalog_page = 0


def clear_catalog_filters():
    st.session_state.grocery_query = ""
    st.session_state.grocery_department = "All groceries"
    reset_catalog_page()


def turn_catalog_page(direction: int):
    st.session_state.catalog_page += direction


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

    account = st.session_state.get("account")
    if account:
        st.caption(f"Signed in as **{account['username']}**")
        if st.button("Sign out", use_container_width=True):
            try:
                engine_client.account_request("POST", "/auth/logout", token=account["token"])
            except AccountRequestError as exc:
                st.error(str(exc))
            else:
                del st.session_state.account
                st.session_state.pop("last_order_id", None)
                replace_cart({})
                st.rerun()
    else:
        with st.expander("Sign in or create an account"):
            mode = st.radio("Account action", ["Sign in", "Create account"], horizontal=True)
            with st.form("account_form", clear_on_submit=True):
                username = st.text_input("Username", max_chars=32)
                password = st.text_input("Password", type="password", max_chars=128)
                st.caption("Use at least 8 characters for your password.")
                submitted = st.form_submit_button(mode, use_container_width=True)
            if submitted:
                route = "/auth/login" if mode == "Sign in" else "/auth/register"
                try:
                    st.session_state.account = engine_client.account_request(
                        "POST", route, json={"username": username.strip(), "password": password},
                    )
                except AccountRequestError as exc:
                    st.error(str(exc))
                else:
                    st.rerun()

    st.divider()

    cart_items = set(st.session_state.cart)
    st.session_state.cart_kits = {
        kit_id: kit for kit_id, kit in st.session_state.cart_kits.items()
        if kit[0] <= cart_items
    }
    cart_count = sum(st.session_state.cart.values())
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
        for item, quantity in st.session_state.cart.items():
            _, icon = get_product_meta(item)
            line_total = get_price(item) * quantity
            name_col, less_col, quantity_col, more_col = st.columns([4, 1, 1, 1], gap="small")
            name_col.write(f"{icon} **{item.title()}**")
            name_col.caption(f"${line_total:.2f}")
            less_col.button(
                "−", key=f"rm_{item}", help=f"Remove one {item}",
                on_click=remove_one_from_cart, args=(item,),
            )
            quantity_col.write(f"**{quantity}**")
            more_col.button(
                "+", key=f"plus_{item}", help=f"Add one {item}",
                on_click=add_to_cart, args=(item,), kwargs={"show_toast": False},
            )

        subtotal_cents = sum(
            round(get_price(item) * 100) * quantity
            for item, quantity in st.session_state.cart.items()
        )
        savings_cents = sum(kit[2] for kit in st.session_state.cart_kits.values())
        delivery_cents = max(0, 1500 - subtotal_cents)
        subtotal = subtotal_cents / 100
        discount = savings_cents / 100
        delivery = delivery_cents / 100
        total = (subtotal_cents - savings_cents + delivery_cents) / 100

        st.divider()
        r1a, r1b = st.columns(2)
        r1a.caption("Subtotal")
        r1b.write(f"**${subtotal:.2f}**")

        r2a, r2b = st.columns(2)
        r2a.caption("Savings")
        r2b.write(f"-${discount:.2f}" if discount else "$0.00")
        for _, name, savings in st.session_state.cart_kits.values():
            st.caption(f"{name} · Save ${savings / 100:.2f}")

        r3a, r3b = st.columns(2)
        r3a.caption("Delivery")
        r3b.write(f"**${delivery:.2f}**" if delivery else "**Free**")

        st.divider()
        r4a, r4b = st.columns(2)
        r4a.write("**Total**")
        r4b.write(f"**${total:.2f}**")

        if delivery_cents:
            st.caption(f"Add ${delivery:.2f} more for free delivery")
            st.progress(subtotal_cents / 1500)

        st.write("")
        col_co, col_cl = st.columns([3, 2])
        with col_co:
            if st.button("✨ Checkout", use_container_width=True, type="primary", disabled=not account):
                items_payload = [
                    {"product_name": item, "unit_price": get_price(item), "quantity": quantity}
                    for item, quantity in st.session_state.cart.items()
                ]
                try:
                    new_order = engine_client.account_request(
                        "POST", "/orders", token=account["token"],
                        json={
                            "items": items_payload,
                            "subtotal": subtotal,
                            "discount": discount,
                            "delivery_fee": delivery,
                        },
                    )
                except AccountRequestError as exc:
                    st.error(str(exc))
                else:
                    order_id = new_order["order_id"]
                    replace_cart({})
                    st.session_state.last_order_id = order_id
                    st.balloons()
                    st.toast(f"Order #{order_id} placed successfully!", icon="🎉")
                    st.rerun()
        with col_cl:
            if st.button("🗑️ Clear", use_container_width=True):
                replace_cart({})
                st.rerun()
        if not account:
            st.caption("Sign in to check out.")
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

    st.markdown("**🍽️ Shop by Occasion**")
    for label, items in OCCASIONS.items():
        if st.button(label, use_container_width=True, key=f"occ_{label}"):
            replace_cart(dict.fromkeys(items, 1))
            st.rerun()


with st.sidebar:
    st.divider()
    developer_mode = st.checkbox("Developer mode", key="developer_mode")
    recommendation_options = {}
    if developer_mode:
        with st.expander("Recommendation tuning", expanded=True):
            recommendation_options = {
                "top_k": st.slider("Maximum suggestions", 1, 10, 5),
                "min_confidence": st.slider("Minimum confidence (%)", 0, 100, 20) / 100,
                "min_lift": st.slider("Minimum lift", 1.0, 5.0, 1.15, 0.05),
            }


# ══════════════════════════════════════════════════════════════════════════════
#  TOP NAV BAR
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    '<div class="nav-bar">'
    '  <div>'
    '    <div class="nav-logo">Fresh<span>Cart</span></div>'
    '  </div>'
    '  <div class="nav-badges">'
    '    <span class="nav-badge">🚚 Free delivery $15+</span>'
    '  </div>'
    '</div>',
    unsafe_allow_html=True,
)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="hero-search-wrap">'
    '  <h1 class="hero-h1">What are you <em>cooking</em> tonight?</h1>'
    '  <p class="hero-sub">Add groceries to your cart to see what shoppers buy with them.</p>'
    '</div>',
    unsafe_allow_html=True,
)

# ── Occasion quick-load ───────────────────────────────────────────────────────
occ_cols = st.columns(len(OCCASIONS))
for i, (label, items) in enumerate(OCCASIONS.items()):
    with occ_cols[i]:
        if st.button(label, use_container_width=True, key=f"hero_occ_{label}"):
            replace_cart(dict.fromkeys(items, 1))
            st.rerun()

st.write("")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_names = [
    "🛍️  Shop & Discover",
    "🍱  Meal Kits",
    "📜  Order History",
]
if developer_mode:
    tab_names.append("Model Inspector")
tab_shop, tab_kits, tab_history, *developer_tabs = st.tabs(tab_names)


# ──────────────────────────────────────────────────────────────────────────────
# TAB 1 — SHOP & DISCOVER
# ──────────────────────────────────────────────────────────────────────────────
with tab_shop:

    st.markdown(
        '<div class="section-title">🛒 Build Your Cart</div>',
        unsafe_allow_html=True,
    )

    search_col, department_col = st.columns([2, 1])
    with search_col:
        search = st.text_input(
            "Search groceries",
            key="grocery_query",
            placeholder="Try milk, bread, or coffee",
            on_change=reset_catalog_page,
        )
    with department_col:
        category = st.selectbox(
            "Department",
            ["All groceries", *CATEGORY_ICONS, "General Grocery"],
            key="grocery_department",
            on_change=reset_catalog_page,
        )

    query_words = search.casefold().split()
    ranked_catalog = sorted(
        catalog_products,
        key=lambda product: (
            EVERYDAY_GROCERIES.index(product) if product in EVERYDAY_GROCERIES
            else len(EVERYDAY_GROCERIES),
            product,
        ),
    )
    matches = [
        product for product in ranked_catalog
        if (category == "All groceries" or get_product_meta(product)[0] == category)
        and all(word in product.casefold() for word in query_words)
    ]

    if matches:
        last_page = (len(matches) - 1) // CATALOG_PAGE_SIZE
        page = min(st.session_state.catalog_page, last_page)
        start = page * CATALOG_PAGE_SIZE
        visible_products = matches[start : start + CATALOG_PAGE_SIZE]
        end = start + len(visible_products)
        if not query_words and category == "All groceries" and page == 0:
            st.markdown("#### Everyday groceries")
        if last_page:
            st.caption(f"Showing {start + 1}–{end} of {len(matches)} products")
        else:
            st.caption(f"{len(matches)} {'product' if len(matches) == 1 else 'products'}")

        with st.container(key="grocery_catalog"):
            for row_start in range(0, len(visible_products), 4):
                columns = st.columns(4)
                for column, product in zip(columns, visible_products[row_start : row_start + 4]):
                    department, icon = get_product_meta(product)
                    quantity = st.session_state.cart.get(product, 0)
                    with column, st.container(border=True):
                        st.markdown(
                            f'<div class="grocery-card">'
                            f'<div class="grocery-illustration" aria-hidden="true">{icon}</div>'
                            f'<div class="grocery-name">{escape(product.title())}</div>'
                            f'<div class="grocery-department">{escape(department)}</div>'
                            f'<div class="grocery-price">${get_price(product):.2f}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                        st.button(
                            f"+ Add · {quantity} in cart" if quantity else "+ Add",
                            key=f"catalog_add_{product}",
                            help=f"Add one {product.title()} to cart",
                            use_container_width=True,
                            on_click=add_to_cart,
                            args=(product,),
                        )

        if last_page:
            previous_col, next_col = st.columns(2)
            previous_col.button(
                "← Previous", disabled=page == 0, on_click=turn_catalog_page, args=(-1,),
            )
            next_col.button(
                "Next →", disabled=page == last_page, on_click=turn_catalog_page, args=(1,),
            )
    else:
        st.info("No groceries match. Try a different search or department.")
        st.button("Clear filters", on_click=clear_catalog_filters)

    st.divider()

    # ── Recommendations ───────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-title">⭐ Suggested for Your Cart</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.cart:
        st.markdown(
            '<div class="empty-state">'
            '  <div class="empty-state-emoji">🧺</div>'
            '  <div class="empty-state-title">Your cart is empty!</div>'
            '  <div class="empty-state-sub">Add groceries above to see suggestions.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        with st.spinner("Finding the best pairings for you…"):
            result = engine_client.get_recommendations(
                cart_items=list(st.session_state.cart),
                **recommendation_options,
            )

        recs     = result.get("recommendations", [])
        strategy = result.get("strategy", "association_rule")

        if developer_mode:
            st.caption(
                f"{result['mode']} · {result['latency_ms']:.2f} ms · {len(recs)} suggestions"
            )

        if recs and strategy == "fallback_staples":
            st.caption("Popular grocery staples")

        if recs:
            # Render cards in rows of 3 — using native st.container(border=True)
            for row_start in range(0, len(recs), 3):
                row_recs = recs[row_start: row_start + 3]
                cols = st.columns(3)
                for col, rec in zip(cols, row_recs):
                    raw     = rec.get("product", "")
                    cat, icon = get_product_meta(raw)
                    name    = raw.title()
                    price   = get_price(raw)
                    in_cart = raw in st.session_state.cart

                    with col:
                        with st.container(border=True):
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

                            if strategy == "association_rule" and rec.get("triggeredBy"):
                                paired_items = rec["triggeredBy"].replace(" + ", " and ").title()
                                st.caption(f"Often bought with {paired_items}")

                            if developer_mode and rec.get("strategy", strategy) == "association_rule":
                                st.markdown(
                                    f'<span class="developer-lift">{escape(rec["affinityStrength"])} '
                                    f'affinity · {rec["lift"]:.2f}× lift</span>',
                                    unsafe_allow_html=True,
                                )
                                st.progress(
                                    rec["confidence"],
                                    text=f"Confidence {rec['confidence']:.1%}",
                                )
                                st.caption(f"Support {rec['support']:.2%}")

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
                                    "+ Add to Cart",
                                    key=f"add_{row_start}_{raw}",
                                    use_container_width=True,
                                    type="secondary",
                                ):
                                    add_to_cart(raw)
                                    st.rerun()
        else:
            empty_hint = (
                "Lower the developer thresholds or add another grocery."
                if developer_mode else "Add another grocery to see more suggestions."
            )
            st.markdown(
                '<div class="empty-state">'
                '  <div class="empty-state-emoji">🤔</div>'
                '  <div class="empty-state-title">No matches found</div>'
                f'  <div class="empty-state-sub">{empty_hint}</div>'
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
    st.caption("Shop themed kits and see what you save compared with buying the items individually.")

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
        regular_cents = sum(round(get_price(item) * 100) for item in items)
        deal_cents = round(bundle["bundle_price"] * 100)
        if deal_cents >= regular_cents:
            deal_cents = regular_cents - round(regular_cents * bundle["discount_pct"] / 100)
        savings_cents = regular_cents - deal_cents
        orders = bundle.get("orders_count", 0)
        bid = bundle["bundle_id"]
        active_kits = st.session_state.cart_kits
        overlaps = any(kit[0].intersection(items) for kit in active_kits.values())

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
                    f'  <span class="kit-orig">${regular_cents / 100:.2f}</span>'
                    f'  <span class="kit-sale">${deal_cents / 100:.2f}</span>'
                    f'  <span class="kit-save">Save ${savings_cents / 100:.2f}</span>'
                    f'</div>'
                    f'<div class="kit-social">🧑‍🤝‍🧑 Backed by {orders:,} real transactions</div>',
                    unsafe_allow_html=True,
                )

                st.write("")
                if bid in active_kits:
                    if st.button("Remove Kit Deal", key=f"kit_remove_{bid}", use_container_width=True):
                        del active_kits[bid]
                        st.rerun()
                elif overlaps:
                    st.caption("Shares items with a kit deal already in your cart.")
                elif st.button("Add Meal Kit", key=f"kit_add_{bid}",
                               use_container_width=True, type="primary"):
                    apply_meal_kit(bid, items, name, savings_cents)
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

    if not account:
        st.info("Sign in from the sidebar to view your receipts and reorder.")
    else:
        try:
            history_data = engine_client.account_request("GET", "/orders", token=account["token"])
        except AccountRequestError as exc:
            st.error(str(exc))
        else:
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
                                f'✓ {escape(status_str)}</span>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

                        # Items purchased chips
                        item_names = [it.get("product_name", "") for it in items]
                        chips_html = " ".join(
                            f'<span class="kit-pill">{get_product_meta(p)[1]} {escape(p.title())} × {item["quantity"]} '
                            f'(${item["unit_price"]:.2f} each)</span>'
                            for p, item in zip(item_names, items)
                        )
                        st.markdown(f'<div style="margin:0.5rem 0 0.8rem;">{chips_html}</div>', unsafe_allow_html=True)

                        # Pricing breakdown
                        p1, p2, p3, p4 = st.columns(4)
                        p1.caption("Subtotal")
                        p1.write(f"${subtot:.2f}")

                        p2.caption("Savings")
                        p2.write(f"-${disc:.2f}" if disc > 0 else "$0.00")

                        p3.caption("Delivery")
                        p3.write("Free" if deliv == 0 else f"${deliv:.2f}")

                        p4.caption("Total Paid")
                        p4.write(f"**:green[${tot:.2f}]**")

                        st.write("")
                        col_btn, _ = st.columns([2, 3])
                        ordered_quantity = sum(item["quantity"] for item in items)
                        with col_btn:
                            if st.button(f"🔁 Reorder Items ({ordered_quantity})", key=f"reorder_btn_{oid}", use_container_width=True):
                                quantities = Counter()
                                for item in items:
                                    quantities[item["product_name"].strip().lower()] += item["quantity"]
                                replace_cart(dict(quantities))
                                st.toast(f"Loaded {ordered_quantity} items from {oid} into cart!", icon="🛒")
                                st.rerun()

                st.write("")
                with st.expander("⚙️ Manage Order History"):
                    st.warning("This will clear your saved past order history.")
                    if st.button("🗑️ Clear All Past Orders", type="secondary"):
                        try:
                            engine_client.account_request("DELETE", "/orders", token=account["token"])
                        except AccountRequestError as exc:
                            st.error(str(exc))
                        else:
                            st.toast("Order history cleared.", icon="🗑️")
                            st.rerun()


if developer_tabs:
    with developer_tabs[0]:
        st.subheader("Model Inspector")
        stats = engine_client.get_stats()
        baskets, catalog, rules_count = st.columns(3)
        baskets.metric("Training baskets", f"{stats['totalTransactions']:,}")
        catalog.metric("Catalog products", stats["totalCatalogSKUs"])
        rules_count.metric("Association rules", stats["totalAssociationRules"])
        st.caption(
            f"Training floors · Support {stats['minSupportThreshold']:.2%} · "
            f"Confidence {stats['minConfidenceThreshold']:.0%} · Lift {stats['minLiftThreshold']:.2f}×"
        )

        st.markdown("#### Strongest rules in the local artifact")
        rules = engine_client.local_recommender.rules
        if rules.empty:
            st.info("No local association rules are loaded.")
        else:
            strongest = rules.nlargest(15, ["lift", "confidence"])[
                ["antecedents_str", "consequents_str", "support", "confidence", "lift"]
            ].copy()
            strongest[["support", "confidence"]] *= 100
            st.dataframe(
                strongest,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "antecedents_str": "Cart items",
                    "consequents_str": "Associated items",
                    "support": st.column_config.NumberColumn("Support", format="%.2f%%"),
                    "confidence": st.column_config.NumberColumn("Confidence", format="%.1f%%"),
                    "lift": st.column_config.NumberColumn("Lift", format="%.2f×"),
                },
            )


        st.markdown("#### Discovered bundles")
        st.caption(
            "Support is the share of baskets with every item. Joint lift compares that share "
            "with what we'd expect if the items were bought independently."
        )
        combinations = engine_client.local_recommender.get_discovered_bundles()
        if not combinations:
            st.info("No mined bundles are available. Run the training pipeline to generate them.")
        else:
            size_col, sort_col = st.columns(2)
            size = size_col.selectbox("Items per bundle", [2, 3])
            ranking = sort_col.selectbox("Rank by", ["Support", "Joint lift"])
            matching = [bundle for bundle in combinations if len(bundle["items"]) == size]
            if ranking == "Joint lift":
                matching.sort(key=lambda bundle: (-bundle["joint_lift"], -bundle["support"], bundle["items"]))
            if matching:
                st.caption(f"Top {min(15, len(matching))} of {len(matching)} combinations")
                st.dataframe(
                    [
                        {
                            "Bundle": " + ".join(item.title() for item in bundle["items"]),
                            "Baskets": bundle["orders_count"],
                            "Support": bundle["support"] * 100,
                            "Joint lift": bundle["joint_lift"],
                        }
                        for bundle in matching[:15]
                    ],
                    hide_index=True,
                    column_config={
                        "Support": st.column_config.NumberColumn("Support", format="%.2f%%"),
                        "Joint lift": st.column_config.NumberColumn("Joint lift", format="%.2f×"),
                    },
                )
            else:
                st.info(f"No {size}-item combinations reached the training support threshold.")
