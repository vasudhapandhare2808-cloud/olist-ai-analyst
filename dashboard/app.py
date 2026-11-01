
from pathlib import Path
import sys

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.queries import (
    get_kpis,
    get_monthly_sales,
    get_order_status,
    get_top_categories,
    get_customer_locations,
    get_delivery_performance,
    get_payment_types,
    get_review_distribution,
)

from src.analyst_agent import ask_analyst


st.set_page_config(
    page_title="Olist Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# DESIGN SYSTEM
# ============================================================

st.markdown(
    """
    <style>
    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
    );

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background-color: #F5F7FB;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    .block-container {
        max-width: 1500px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Sidebar */

    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E8ECF3;
    }

    [data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }

    [data-testid="stSidebar"] h1 {
        color: #172B4D;
        font-weight: 800;
        letter-spacing: -1px;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #748198;
        font-size: 13px;
    }

    /* Main headings */

    .page-title {
        font-size: 30px;
        font-weight: 800;
        color: #172B4D;
        letter-spacing: -1.2px;
        margin-bottom: 4px;
    }

    .page-subtitle {
        color: #8792A5;
        font-size: 14px;
        margin-bottom: 26px;
    }

    .section-title {
        color: #263650;
        font-size: 17px;
        font-weight: 700;
        margin-top: 10px;
        margin-bottom: 12px;
    }

    /* KPI cards */

    [data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E8EDF5;
        border-radius: 13px;
        padding: 19px 20px;
        box-shadow: 0 2px 8px rgba(25, 45, 80, 0.025);
        min-height: 112px;
    }

    [data-testid="stMetricLabel"] {
        color: #8190A6 !important;
        font-size: 12px !important;
        font-weight: 600 !important;
    }

    [data-testid="stMetricValue"] {
        color: #172B4D !important;
        font-size: 25px !important;
        font-weight: 750 !important;
    }

    /* Charts */

    [data-testid="stPlotlyChart"] {
        background: #FFFFFF;
        border: 1px solid #E8EDF5;
        border-radius: 13px;
        padding: 10px;
        box-shadow: 0 2px 8px rgba(25, 45, 80, 0.025);
    }

    /* Dataframes */

    [data-testid="stDataFrame"] {
        border: 1px solid #E8EDF5;
        border-radius: 12px;
        overflow: hidden;
    }

    /* Chat */

    [data-testid="stChatMessage"] {
        border: 1px solid #E8EDF5;
        border-radius: 12px;
        background: #FFFFFF;
        padding: 12px;
    }

    /* Buttons */

    .stButton > button {
        border-radius: 8px;
        border: 1px solid #DCE5F2;
        color: #2458C5;
        background: #FFFFFF;
        font-weight: 600;
    }

    .stButton > button:hover {
        border-color: #3675E8;
        color: #2458C5;
    }

    /* Dividers */

    hr {
        border-color: #E8EDF5;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# PLOTLY THEME
# ============================================================

CHART_LAYOUT = {
    "template": "plotly_white",
    "font": {
        "family": "Inter, sans-serif",
        "color": "#64748B",
        "size": 11,
    },
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "margin": dict(l=20, r=20, t=45, b=20),
    "hoverlabel": {
        "bgcolor": "#172B4D",
        "font_color": "#FFFFFF",
    },
}

BLUE = "#3675E8"
LIGHT_BLUE = "#9BBBF7"
NAVY = "#172B4D"
MUTED = "#8190A6"


def style_chart(fig, height=350):
    fig.update_layout(
        **CHART_LAYOUT,
        height=height,
    )
    return fig


# ============================================================
# CACHED DATA
# ============================================================

@st.cache_data(ttl=300)
def load_kpis():
    return get_kpis()


@st.cache_data(ttl=300)
def load_monthly_sales():
    return get_monthly_sales()


@st.cache_data(ttl=300)
def load_order_status():
    return get_order_status()


@st.cache_data(ttl=300)
def load_categories():
    return get_top_categories(10)


@st.cache_data(ttl=300)
def load_customers():
    return get_customer_locations(10)


@st.cache_data(ttl=300)
def load_delivery():
    return get_delivery_performance()


@st.cache_data(ttl=300)
def load_payments():
    return get_payment_types()


@st.cache_data(ttl=300)
def load_reviews():
    return get_review_distribution()


# ============================================================
# REUSABLE PAGE HEADER
# ============================================================

def page_header(title, subtitle):
    st.markdown(
        f"""
        <div class="page-title">{title}</div>
        <div class="page-subtitle">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

with st.sidebar:

    st.markdown("# olist<span style='color:#3675E8'>.</span>",
                unsafe_allow_html=True)

    st.caption("INTELLIGENCE PLATFORM")

    st.divider()

    st.markdown("**WORKSPACE**")

    pages = {
        "Overview": "Overview",
        "Sales Analytics": "Sales Analytics",
        "Product Analytics": "Product Analytics",
        "Customer Analytics": "Customer Analytics",
        "Delivery Analytics": "Delivery Analytics",
        "AI Analyst": "AI Analyst",
    }

    page = st.radio(
        "Navigation",
        list(pages.keys()),
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown("**DATA SOURCE**")
    st.caption("Olist Brazilian E-commerce")
    st.caption("DuckDB · Local Database")

    st.divider()

    st.caption("Built with Streamlit, Python & Ollama")


# ============================================================
# 1. EXECUTIVE OVERVIEW
# ============================================================

if page == "Overview":

    page_header(
        "Business Overview",
        "Monitor your e-commerce performance and key business metrics.",
    )

    kpis = load_kpis()

    # KPI ROW 1

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "TOTAL ORDERS",
        f"{int(kpis['total_orders']):,}",
    )

    col2.metric(
        "UNIQUE CUSTOMERS",
        f"{int(kpis['total_customers']):,}",
    )

    col3.metric(
        "PRODUCT SALES",
        f"R$ {kpis['product_sales'] / 1_000_000:.2f}M",
    )

    # KPI ROW 2

    col4, col5, col6 = st.columns(3)

    col4.metric(
        "AVERAGE REVIEW",
        f"{kpis['average_review_score']:.2f}/5",
    )

    col5.metric(
        "DELIVERY RATE",
        f"{kpis['delivery_rate']:.2f}%",
    )

    col6.metric(
        "AVERAGE PAYMENT",
        f"R$ {kpis['average_payment_value']:.2f}",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # SALES AND ORDER STATUS

    left, right = st.columns([1.6, 1])

    with left:

        st.markdown(
            '<div class="section-title">Monthly Sales Performance</div>',
            unsafe_allow_html=True,
        )

        sales = load_monthly_sales()

        fig = px.area(
            sales,
            x="month",
            y="product_sales",
        )

        fig.update_traces(
            line_color=BLUE,
            fillcolor="rgba(54,117,232,0.12)",
            line_width=2.5,
            hovertemplate="Sales: R$ %{y:,.2f}<extra></extra>",
        )

        fig.update_xaxes(title=None, showgrid=False)
        fig.update_yaxes(
            title="Product Sales (BRL)",
            gridcolor="#EDF1F7",
        )

        st.plotly_chart(
            style_chart(fig, 370),
            use_container_width=True,
        )

    with right:

        st.markdown(
            '<div class="section-title">Order Status</div>',
            unsafe_allow_html=True,
        )

        status = load_order_status()

        fig = px.pie(
            status,
            names="order_status",
            values="order_count",
            hole=0.65,
        )

        fig.update_traces(
            textposition="inside",
            textinfo="percent",
            marker=dict(line=dict(color="#FFFFFF", width=2)),
        )

        fig.update_layout(legend=dict(orientation="h", y=-0.12))

        st.plotly_chart(
            style_chart(fig, 370),
            use_container_width=True,
        )

    # CATEGORY AND DELIVERY

    left, right = st.columns(2)

    with left:

        st.markdown(
            '<div class="section-title">Top Product Categories</div>',
            unsafe_allow_html=True,
        )

        categories = load_categories().sort_values("items_sold")

        fig = px.bar(
            categories,
            x="items_sold",
            y="category",
            orientation="h",
        )

        fig.update_traces(
            marker_color=BLUE,
            hovertemplate="%{y}<br>Items sold: %{x:,}<extra></extra>",
        )

        fig.update_xaxes(title="Items Sold", gridcolor="#EDF1F7")
        fig.update_yaxes(title=None, showgrid=False)

        st.plotly_chart(
            style_chart(fig, 390),
            use_container_width=True,
        )

    with right:

        st.markdown(
            '<div class="section-title">Delivery Performance</div>',
            unsafe_allow_html=True,
        )

        delivery = load_delivery()

        delivery_data = {
            "Metric": ["On-time / eligible deliveries", "Late deliveries"],
            "Percentage": [
                max(0, 100 - delivery["late_delivery_percentage"]),
                delivery["late_delivery_percentage"],
            ],
        }

        fig = px.bar(
            delivery_data,
            x="Percentage",
            y="Metric",
            orientation="h",
            text="Percentage",
        )

        fig.update_traces(
            marker_color=[BLUE, "#F59E0B"],
            texttemplate="%{text:.2f}%",
            textposition="outside",
        )

        fig.update_xaxes(range=[0, 110], title="Percentage", gridcolor="#EDF1F7")
        fig.update_yaxes(title=None, showgrid=False)

        st.plotly_chart(
            style_chart(fig, 390),
            use_container_width=True,
        )


# ============================================================
# 2. SALES ANALYTICS
# ============================================================

elif page == "Sales Analytics":

    page_header(
        "Sales Analytics",
        "Explore monthly sales trends and order volume.",
    )

    sales = load_monthly_sales()

    total_sales = sales["product_sales"].sum()
    total_orders = sales["total_orders"].sum()

    col1, col2 = st.columns(2)

    col1.metric("Delivered Product Sales", f"R$ {total_sales:,.2f}")
    col2.metric("Delivered Orders in Trend", f"{int(total_orders):,}")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">Monthly Revenue Trend</div>',
        unsafe_allow_html=True,
    )

    fig = px.line(
        sales,
        x="month",
        y="product_sales",
        markers=True,
    )

    fig.update_traces(
        line_color=BLUE,
        line_width=3,
        marker_size=6,
    )

    fig.update_xaxes(title=None, showgrid=False)
    fig.update_yaxes(title="Product Sales (BRL)", gridcolor="#EDF1F7")

    st.plotly_chart(style_chart(fig, 420), use_container_width=True)

    st.markdown(
        '<div class="section-title">Monthly Order Volume</div>',
        unsafe_allow_html=True,
    )

    fig = px.bar(
        sales,
        x="month",
        y="total_orders",
    )

    fig.update_traces(marker_color=LIGHT_BLUE)
    fig.update_xaxes(title=None, showgrid=False)
    fig.update_yaxes(title="Orders", gridcolor="#EDF1F7")

    st.plotly_chart(style_chart(fig, 360), use_container_width=True)

    with st.expander("View monthly sales data"):
        st.dataframe(sales, use_container_width=True, hide_index=True)


# ============================================================
# 3. PRODUCT ANALYTICS
# ============================================================

elif page == "Product Analytics":

    page_header(
        "Product Analytics",
        "Understand product demand and category performance.",
    )

    categories = load_categories()

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            '<div class="section-title">Top Categories by Items Sold</div>',
            unsafe_allow_html=True,
        )

        fig = px.bar(
            categories.sort_values("items_sold"),
            x="items_sold",
            y="category",
            orientation="h",
        )

        fig.update_traces(marker_color=BLUE)
        fig.update_xaxes(title="Items Sold", gridcolor="#EDF1F7")
        fig.update_yaxes(title=None, showgrid=False)

        st.plotly_chart(style_chart(fig, 430), use_container_width=True)

    with col2:

        st.markdown(
            '<div class="section-title">Category Sales Contribution</div>',
            unsafe_allow_html=True,
        )

        fig = px.pie(
            categories,
            names="category",
            values="product_sales",
            hole=0.55,
        )

        fig.update_traces(
            textposition="inside",
            textinfo="percent",
        )

        st.plotly_chart(style_chart(fig, 430), use_container_width=True)

    st.markdown(
        '<div class="section-title">Category Performance Table</div>',
        unsafe_allow_html=True,
    )

    st.dataframe(
        categories,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# 4. CUSTOMER ANALYTICS
# ============================================================

elif page == "Customer Analytics":

    page_header(
        "Customer Analytics",
        "Explore customer distribution across Brazilian cities and states.",
    )

    customers = load_customers()

    total_top_customers = customers["customer_count"].sum()

    col1, col2 = st.columns(2)

    col1.metric("Cities in Top 10", len(customers))
    col2.metric("Customers in Top 10 Cities", f"{total_top_customers:,}")

    st.markdown(
        '<div class="section-title">Top Customer Cities</div>',
        unsafe_allow_html=True,
    )

    fig = px.bar(
        customers.sort_values("customer_count"),
        x="customer_count",
        y="customer_city",
        color="customer_state",
        orientation="h",
        color_discrete_sequence=[BLUE, LIGHT_BLUE, "#7D9FEA"],
    )

    fig.update_xaxes(title="Customer Records", gridcolor="#EDF1F7")
    fig.update_yaxes(title=None, showgrid=False)

    st.plotly_chart(style_chart(fig, 450), use_container_width=True)

    st.markdown(
        '<div class="section-title">Customer Location Data</div>',
        unsafe_allow_html=True,
    )

    st.dataframe(
        customers,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# 5. DELIVERY ANALYTICS
# ============================================================

elif page == "Delivery Analytics":

    page_header(
        "Delivery Analytics",
        "Track delivery times, late shipments, and customer satisfaction.",
    )

    delivery = load_delivery()
    reviews = load_reviews()

    col1, col2 = st.columns(2)

    col1.metric(
        "AVERAGE DELIVERY TIME",
        f"{delivery['average_delivery_days']:.2f} days",
    )

    col2.metric(
        "LATE DELIVERY RATE",
        f"{delivery['late_delivery_percentage']:.2f}%",
    )

    st.markdown(
        '<div class="section-title">Review Score Distribution</div>',
        unsafe_allow_html=True,
    )

    fig = px.bar(
        reviews,
        x="review_score",
        y="review_count",
        text="review_count",
    )

    fig.update_traces(
        marker_color=BLUE,
        textposition="outside",
    )

    fig.update_xaxes(
        title="Review Score",
        dtick=1,
        showgrid=False,
    )

    fig.update_yaxes(
        title="Number of Reviews",
        gridcolor="#EDF1F7",
    )

    st.plotly_chart(style_chart(fig, 400), use_container_width=True)

    st.markdown(
        '<div class="section-title">Payment Method Analysis</div>',
        unsafe_allow_html=True,
    )

    payments = load_payments()

    fig = px.bar(
        payments,
        x="payment_type",
        y="total_payment",
        text="total_payment",
    )

    fig.update_traces(
        marker_color=LIGHT_BLUE,
        texttemplate="R$ %{text:,.0f}",
        textposition="outside",
    )

    fig.update_xaxes(title="Payment Type", showgrid=False)
    fig.update_yaxes(title="Payment Value (BRL)", gridcolor="#EDF1F7")

    st.plotly_chart(style_chart(fig, 380), use_container_width=True)


# ============================================================
# 6. AI ANALYST
# ============================================================

elif page == "AI Analyst":

    page_header(
        "AI Business Analyst",
        "Ask questions about Olist data using natural language.",
    )

    st.markdown(
        """
        <div style="
            background:#FFFFFF;
            border:1px solid #E8EDF5;
            border-radius:12px;
            padding:18px;
            margin-bottom:20px;
        ">
            <div style="font-size:17px;font-weight:700;color:#172B4D;">
                Ask your data anything.
            </div>
            <div style="font-size:13px;color:#8190A6;margin-top:5px;">
                Powered by Qwen, Llama, SQLGlot and DuckDB.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    examples = [
        "What are the top five product categories by items sold?",
        "What percentage of delivered orders arrived late?",
        "Which five customer cities have the most customers?",
        "What is the average review score?",
    ]

    with st.expander("Try an example question"):

        for example in examples:

            if st.button(example, key=f"example_{example}"):
                st.session_state.ai_question = example

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for message in st.session_state.chat_history:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input(
        "Ask about sales, customers, products or deliveries..."
    )

    if "ai_question" in st.session_state:
        question = st.session_state.pop("ai_question")

    if question:

        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": question,
            }
        )

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):

            with st.spinner("Analyzing your business question..."):

                try:
                    answer = ask_analyst(question)

                except Exception as exc:
                    answer = f"Unable to complete the analysis: {exc}"

                st.markdown(answer)

        st.session_state.chat_history.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()

st.markdown(
    """
    <div style="
        text-align:center;
        color:#94A3B8;
        font-size:11px;
        padding:8px;
    ">
        OLIST INTELLIGENCE · AI-POWERED BUSINESS ANALYTICS
        <br>
        Built with Python, DuckDB, Streamlit and Ollama
    </div>
    """,
    unsafe_allow_html=True,
)
