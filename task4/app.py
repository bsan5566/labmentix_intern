
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Local Food Wastage Management", page_icon="🥗", layout="wide")

# ---------- DB helpers ----------
@st.cache_resource
def get_conn():
    conn = sqlite3.connect("food_waste.db", check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def run_query(query, params=()):
    with closing(get_conn().cursor()) as cur:
        cur.execute(query, params)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
    return pd.DataFrame(rows, columns=cols)

def run_exec(query, params=()):
    with closing(get_conn().cursor()) as cur:
        cur.execute(query, params)
        get_conn().commit()

# ---------- UI helpers ----------
def multiselect_or_all(label, options):
    sel = st.multiselect(label, options)
    return options if not sel else sel


st.title("Local Food Wastage Management System")
st.caption("Filter, analyze and manage providers, receivers, listings and claims")

tab_overview, tab_dashboard, tab_explore, tab_queries, tab_crud, tab_insights, tab_alerts, tab_map, tab_reports = st.tabs(
    ["Overview", "Dashboard 📈", "Explore 📊", "Queries (15+)", "CRUD ✍️", "Insights 🧠", "Alerts 🚨", "Geo Map 🌍", "Reports 📑"]
)




# ---------- Overview ----------
with tab_overview:
    c1, c2, c3, c4 = st.columns(4)
    total_prov = run_query("SELECT COUNT(*) AS n FROM providers")
    total_recv = run_query("SELECT COUNT(*) AS n FROM receivers")
    total_food = run_query("SELECT COUNT(*) AS n FROM food_listings")
    total_claims = run_query("SELECT COUNT(*) AS n FROM claims")
    c1.metric("Providers", int(total_prov['n'].iloc[0]) if not total_prov.empty else 0)
    c2.metric("Receivers", int(total_recv['n'].iloc[0]) if not total_recv.empty else 0)
    c3.metric("Food Listings", int(total_food['n'].iloc[0]) if not total_food.empty else 0)
    c4.metric("Claims", int(total_claims['n'].iloc[0]) if not total_claims.empty else 0)

    st.subheader("Recent Listings")
    st.dataframe(run_query("SELECT food_id, food_name, quantity, expiry_date, location, food_type, meal_type FROM food_listings ORDER BY food_id DESC LIMIT 20"))
    
   # ---------- Dashboard ----------
with tab_dashboard:
    st.subheader("📊 Interactive Dashboard")

    # --- Providers per city ---
    st.write("### Providers per City")
    df_city = run_query("""
        SELECT city, COUNT(*) AS provider_count
        FROM providers
        GROUP BY city
        ORDER BY provider_count DESC;
    """)
    if not df_city.empty:
        import plotly.express as px
        fig = px.bar(df_city, x="city", y="provider_count",
                     text="provider_count", title="Providers by City")
        fig.update_traces(textposition="outside", marker_color="#1F77B4")
        st.plotly_chart(fig, use_container_width=True)

    # --- Food type distribution ---
    st.write("### Food Type Distribution")
    df_food_type = run_query("""
        SELECT food_type, COUNT(*) AS cnt
        FROM food_listings
        GROUP BY food_type
        ORDER BY cnt DESC;
    """)
    if not df_food_type.empty:
        fig = px.pie(df_food_type, names="food_type", values="cnt",
                     title="Food Types Share")
        st.plotly_chart(fig, use_container_width=True)

    # --- Claims status distribution ---
    st.write("### Claims Status Distribution")
    df_claims = run_query("""
        SELECT LOWER(status) AS status, COUNT(*) AS cnt
        FROM claims
        GROUP BY LOWER(status);
    """)
    if not df_claims.empty:
        fig = px.bar(df_claims, x="status", y="cnt",
                     text="cnt", title="Claims Status")
        fig.update_traces(marker_color="#2CA02C", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    # --- Top providers by total donations ---
    st.write("### Top Providers by Total Donations")
    df_top_providers = run_query("""
        SELECT p.name, SUM(fl.quantity) AS total_donated
        FROM food_listings fl
        JOIN providers p ON fl.provider_id = p.provider_id
        GROUP BY p.name
        ORDER BY total_donated DESC
        LIMIT 10;
    """)
    if not df_top_providers.empty:
        fig = px.bar(df_top_providers, x="name", y="total_donated",
                     text="total_donated", title="Top 10 Providers")
        fig.update_traces(marker_color="#FF7F0E", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    # --- Donations trend over time ---
    st.write("### Donations Trend Over Time")
    df_trend = run_query("""
        SELECT substr(expiry_date,1,7) AS month, SUM(quantity) AS total_quantity
        FROM food_listings
        GROUP BY substr(expiry_date,1,7)
        ORDER BY month;
    """)
    if not df_trend.empty:
        fig = px.line(df_trend, x="month", y="total_quantity",
                      markers=True, title="Monthly Donations Trend")
        fig.update_traces(line_color="#9467BD")
        st.plotly_chart(fig, use_container_width=True)

    # --- Top food items ---
    st.write("### Top 5 Donated Food Items")
    df_food_items = run_query("""
        SELECT food_name, SUM(quantity) AS total_quantity
        FROM food_listings
        GROUP BY food_name
        ORDER BY total_quantity DESC
        LIMIT 5;
    """)
    if not df_food_items.empty:
        fig = px.bar(df_food_items, x="food_name", y="total_quantity",
                     text="total_quantity", title="Top 5 Food Items")
        fig.update_traces(marker_color="#D62728", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    # --- Top receivers by claims ---
    st.write("### Top 5 Receivers by Claims")
    df_top_receivers = run_query("""
        SELECT r.name, COUNT(c.claim_id) AS total_claims
        FROM claims c
        JOIN receivers r ON c.receiver_id = r.receiver_id
        GROUP BY r.name
        ORDER BY total_claims DESC
        LIMIT 5;
    """)
    if not df_top_receivers.empty:
        fig = px.bar(df_top_receivers, x="name", y="total_claims",
                     text="total_claims", title="Top 5 Receivers")
        fig.update_traces(marker_color="#8C564B", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)



# ---------- Explore ----------
with tab_explore:
    st.subheader("Filter Listings")
    cities = run_query("SELECT DISTINCT location FROM food_listings")["location"].dropna().tolist()
    provider_types = run_query("SELECT DISTINCT provider_type FROM food_listings")["provider_type"].dropna().tolist()
    food_types = run_query("SELECT DISTINCT food_type FROM food_listings")["food_type"].dropna().tolist()
    meal_types = run_query("SELECT DISTINCT meal_type FROM food_listings")["meal_type"].dropna().tolist()

    col1, col2, col3, col4 = st.columns(4)
    sel_cities = col1.multiselect("City", cities)
    sel_provider_types = col2.multiselect("Provider Type", provider_types)
    sel_food_types = col3.multiselect("Food Type", food_types)
    sel_meal_types = col4.multiselect("Meal Type", meal_types)

    query = "SELECT * FROM food_listings WHERE 1=1"
    params = []

    if sel_cities:
        query += f" AND location IN ({','.join(['?']*len(sel_cities))})"
        params += sel_cities
    if sel_provider_types:
        query += f" AND provider_type IN ({','.join(['?']*len(sel_provider_types))})"
        params += sel_provider_types
    if sel_food_types:
        query += f" AND food_type IN ({','.join(['?']*len(sel_food_types))})"
        params += sel_food_types
    if sel_meal_types:
        query += f" AND meal_type IN ({','.join(['?']*len(sel_meal_types))})"
        params += sel_meal_types

    st.dataframe(run_query(query, tuple(params)))

# ---------- Queries (Extended) ----------
with tab_queries:
    st.subheader("Key Questions & Insights")

    queries = {
        # 🔹 Provider / Receiver Analytics
        "Providers per city": """
            SELECT city, COUNT(*) AS provider_count
            FROM providers
            GROUP BY city
            ORDER BY provider_count DESC;
        """,
        "Top 5 cities by number of providers": """
            SELECT city, COUNT(*) AS provider_count
            FROM providers
            GROUP BY city
            ORDER BY provider_count DESC
            LIMIT 5;
        """,
        "Receivers per city": """
            SELECT city, COUNT(*) AS receiver_count
            FROM receivers
            GROUP BY city
            ORDER BY receiver_count DESC;
        """,
        "Top 5 cities by number of receivers": """
            SELECT city, COUNT(*) AS receiver_count
            FROM receivers
            GROUP BY city
            ORDER BY receiver_count DESC
            LIMIT 5;
        """,
        "Average donations per provider": """
            SELECT p.name, AVG(fl.quantity) AS avg_quantity
            FROM food_listings fl
            JOIN providers p ON fl.provider_id = p.provider_id
            GROUP BY p.name
            ORDER BY avg_quantity DESC;
        """,
        "Average claims per receiver": """
            SELECT r.name, AVG(c.claim_id) AS avg_claims
            FROM claims c
            JOIN receivers r ON c.receiver_id = r.receiver_id
            GROUP BY r.name
            ORDER BY avg_claims DESC;
        """,

        # 🔹 Food Analytics
        "Provider type contribution (by total quantity)": """
            SELECT fl.provider_type, SUM(fl.quantity) AS total_quantity
            FROM food_listings fl
            GROUP BY fl.provider_type
            ORDER BY total_quantity DESC;
        """,
        "Most donated food items": """
            SELECT food_name, SUM(quantity) AS total_quantity
            FROM food_listings
            GROUP BY food_name
            ORDER BY total_quantity DESC
            LIMIT 10;
        """,
        "Expired food listings": """
            SELECT *
            FROM food_listings
            WHERE date(expiry_date) < date('now')
            ORDER BY expiry_date ASC;
        """,
        "Food listings expiring in next 7 days": """
            SELECT *
            FROM food_listings
            WHERE date(expiry_date) BETWEEN date('now') AND date('now', '+7 day')
            ORDER BY expiry_date ASC;
        """,

        # 🔹 Claims Analytics
        "Top receivers by number of claims": """
            SELECT r.name AS receiver_name, COUNT(c.claim_id) AS total_claims
            FROM claims c
            JOIN receivers r ON c.receiver_id = r.receiver_id
            GROUP BY r.name
            ORDER BY total_claims DESC;
        """,
        "Receivers with most completed claims": """
            SELECT r.name, COUNT(c.claim_id) AS completed_claims
            FROM claims c
            JOIN receivers r ON c.receiver_id = r.receiver_id
            WHERE LOWER(c.status) = 'completed'
            GROUP BY r.name
            ORDER BY completed_claims DESC;
        """,
        "Food items with most cancelled claims": """
            SELECT fl.food_name, COUNT(c.claim_id) AS cancelled_claims
            FROM claims c
            JOIN food_listings fl ON c.food_id = fl.food_id
            WHERE LOWER(c.status) = 'cancelled'
            GROUP BY fl.food_name
            ORDER BY cancelled_claims DESC;
        """,
        "Claims per food item": """
            SELECT fl.food_name, COUNT(c.claim_id) AS claims_count
            FROM food_listings fl
            LEFT JOIN claims c ON fl.food_id = c.food_id
            GROUP BY fl.food_name
            ORDER BY claims_count DESC;
        """,
        "Provider with highest completed claims": """
            SELECT p.name, COUNT(c.claim_id) AS completed_claims
            FROM claims c
            JOIN food_listings fl ON c.food_id = fl.food_id
            JOIN providers p ON fl.provider_id = p.provider_id
            WHERE LOWER(c.status) = 'completed'
            GROUP BY p.name
            ORDER BY completed_claims DESC;
        """,
        "Claims status distribution": """
            SELECT LOWER(status) AS status, COUNT(*) AS cnt
            FROM claims
            GROUP BY LOWER(status)
            ORDER BY cnt DESC;
        """,
        "Claim completion percentage": """
            SELECT status,
                   COUNT(*) * 100.0 / (SELECT COUNT(*) FROM claims) AS percentage
            FROM claims
            GROUP BY status;
        """,
        "Avg quantity per receiver (approx)": """
            SELECT r.name AS receiver_name,
                   AVG(fl.quantity) AS avg_quantity_of_items_they_claimed
            FROM claims c
            JOIN receivers r ON c.receiver_id = r.receiver_id
            JOIN food_listings fl ON c.food_id = fl.food_id
            GROUP BY r.name
            ORDER BY avg_quantity_of_items_they_claimed DESC;
        """,
        "Top 5 receivers by quantity claimed": """
            SELECT r.name, SUM(fl.quantity) AS total_claimed
            FROM claims c
            JOIN receivers r ON c.receiver_id = r.receiver_id
            JOIN food_listings fl ON c.food_id = fl.food_id
            GROUP BY r.name
            ORDER BY total_claimed DESC
            LIMIT 5;
        """,
        "Most-claimed meal type": """
            SELECT fl.meal_type, COUNT(c.claim_id) AS claims_count
            FROM claims c
            JOIN food_listings fl ON c.food_id = fl.food_id
            GROUP BY fl.meal_type
            ORDER BY claims_count DESC;
        """,
        "Average time between listing and claim": """
            SELECT fl.food_id, fl.food_name,
                   ROUND(julianday(c.timestamp) - julianday(fl.expiry_date), 2) AS days_difference
            FROM food_listings fl
            JOIN claims c ON fl.food_id = c.food_id
            ORDER BY days_difference ASC;
        """,

        # 🔹 Efficiency & Ratios
        "Claim to listing ratio by provider": """
            SELECT p.name,
                   COUNT(DISTINCT c.claim_id)*1.0 / COUNT(DISTINCT fl.food_id) AS claim_to_listing_ratio
            FROM providers p
            LEFT JOIN food_listings fl ON p.provider_id = fl.provider_id
            LEFT JOIN claims c ON fl.food_id = c.food_id
            GROUP BY p.name
            ORDER BY claim_to_listing_ratio DESC;
        """,
        "Total quantity donated by provider": """
            SELECT p.name, SUM(fl.quantity) AS total_donated
            FROM food_listings fl
            JOIN providers p ON fl.provider_id = p.provider_id
            GROUP BY p.name
            ORDER BY total_donated DESC;
        """
    }

    q_choice = st.selectbox("Choose a query", list(queries.keys()))

    if q_choice == "Provider contacts in selected city":
        city = st.text_input("City", value="")
        if city:
            st.dataframe(run_query(queries[q_choice], (city,)))
    elif q_choice == "Listings nearing expiry (<= N days)":
        days = st.number_input("Days from now", value=3, min_value=0, step=1)
        offset = f"+{int(days)} day"
        st.dataframe(run_query("SELECT * FROM food_listings WHERE date(expiry_date) <= date('now', ?)", (offset,)))
    else:
        # Directly run the query without button
        st.dataframe(run_query(queries[q_choice]))


# ---------- CRUD ----------
with tab_crud:
    st.subheader("Manage Records")

    crud_tabs = st.tabs(["Providers", "Receivers", "Food Listings", "Claims"])

    # Providers
    with crud_tabs[0]:
        st.write("### Providers")
        st.dataframe(run_query("SELECT * FROM providers ORDER BY provider_id"))
        with st.form("add_provider"):
            st.write("**Add / Update Provider**")
            pid = st.number_input("Provider ID (blank for new)", value=0, min_value=0, step=1)
            name = st.text_input("Name")
            ptype = st.text_input("Type")
            address = st.text_input("Address")
            city = st.text_input("City")
            contact = st.text_input("Contact")
            submitted = st.form_submit_button("Save")
            if submitted:
                if pid and pid > 0:
                    run_exec("UPDATE providers SET name=?, type=?, address=?, city=?, contact=? WHERE provider_id=?",
                             (name, ptype, address, city, contact, pid))
                    st.success("Provider updated")
                else:
                    run_exec("INSERT INTO providers(name,type,address,city,contact) VALUES(?,?,?,?,?)",
                             (name, ptype, address, city, contact))
                    st.success("Provider added")
        del_id = st.number_input("Delete Provider ID", value=0, min_value=0, step=1)
        if st.button("Delete Provider"):
            run_exec("DELETE FROM providers WHERE provider_id=?", (int(del_id),))
            st.warning("Provider deleted (if existed)")

    # Receivers
    with crud_tabs[1]:
        st.write("### Receivers")
        st.dataframe(run_query("SELECT * FROM receivers ORDER BY receiver_id"))
        with st.form("add_receiver"):
            st.write("**Add / Update Receiver**")
            rid = st.number_input("Receiver ID (blank for new)", value=0, min_value=0, step=1)
            name = st.text_input("Name", key="r_name")
            rtype = st.text_input("Type", key="r_type")
            city = st.text_input("City", key="r_city")
            contact = st.text_input("Contact", key="r_contact")
            submitted = st.form_submit_button("Save", use_container_width=True)
            if submitted:
                if rid and rid > 0:
                    run_exec("UPDATE receivers SET name=?, type=?, city=?, contact=? WHERE receiver_id=?",
                             (name, rtype, city, contact, rid))
                    st.success("Receiver updated")
                else:
                    run_exec("INSERT INTO receivers(name,type,city,contact) VALUES(?,?,?,?)",
                             (name, rtype, city, contact))
                    st.success("Receiver added")
        del_id = st.number_input("Delete Receiver ID", value=0, min_value=0, step=1, key="del_r")
        if st.button("Delete Receiver"):
            run_exec("DELETE FROM receivers WHERE receiver_id=?", (int(del_id),))
            st.warning("Receiver deleted (if existed)")

    # Food Listings
    with crud_tabs[2]:
        st.write("### Food Listings")
        st.dataframe(run_query("SELECT * FROM food_listings ORDER BY food_id DESC LIMIT 200"))
        with st.form("add_food"):
            st.write("**Add / Update Food**")
            fid = st.number_input("Food ID (blank for new)", value=0, min_value=0, step=1)
            fname = st.text_input("Food Name")
            qty = st.number_input("Quantity", value=1, min_value=0, step=1)
            expiry = st.text_input("Expiry Date (YYYY-MM-DD)")
            pid = st.number_input("Provider ID", value=0, min_value=0, step=1, key="f_pid")
            ptype = st.text_input("Provider Type")
            location = st.text_input("Location (City)")
            ftype = st.text_input("Food Type")
            mtype = st.text_input("Meal Type")
            submitted = st.form_submit_button("Save")
            if submitted:
                if fid and fid > 0:
                    run_exec("""UPDATE food_listings
                                SET food_name=?, quantity=?, expiry_date=?, provider_id=?, provider_type=?,
                                    location=?, food_type=?, meal_type=?
                                WHERE food_id=?""",
                             (fname, qty, expiry, pid, ptype, location, ftype, mtype, fid))
                    st.success("Food updated")
                else:
                    run_exec("""INSERT INTO food_listings
                                (food_name, quantity, expiry_date, provider_id, provider_type, location, food_type, meal_type)
                                VALUES (?,?,?,?,?,?,?,?)""",
                             (fname, qty, expiry, pid, ptype, location, ftype, mtype))
                    st.success("Food added")
        del_id = st.number_input("Delete Food ID", value=0, min_value=0, step=1, key="del_f")
        if st.button("Delete Food"):
            run_exec("DELETE FROM food_listings WHERE food_id=?", (int(del_id),))
            st.warning("Food deleted (if existed)")

    # Claims
    with crud_tabs[3]:
        st.write("### Claims")
        st.dataframe(run_query("SELECT * FROM claims ORDER BY claim_id DESC LIMIT 200"))
        with st.form("add_claim"):
            st.write("**Add / Update Claim**")
            cid = st.number_input("Claim ID (blank for new)", value=0, min_value=0, step=1)
            fid = st.number_input("Food ID", value=0, min_value=0, step=1, key="c_fid")
            rid = st.number_input("Receiver ID", value=0, min_value=0, step=1, key="c_rid")
            status = st.selectbox("Status", ["Pending", "Completed", "Cancelled"])
            ts = st.text_input("Timestamp (YYYY-MM-DD HH:MM:SS)", value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            submitted = st.form_submit_button("Save")
            if submitted:
                if cid and cid > 0:
                    run_exec("UPDATE claims SET food_id=?, receiver_id=?, status=?, timestamp=? WHERE claim_id=?",
                             (fid, rid, status, ts, cid))
                    st.success("Claim updated")
                else:
                    run_exec("INSERT INTO claims(food_id, receiver_id, status, timestamp) VALUES(?,?,?,?)",
                             (fid, rid, status, ts))
                    st.success("Claim added")
        del_id = st.number_input("Delete Claim ID", value=0, min_value=0, step=1, key="del_c")
        if st.button("Delete Claim"):
            run_exec("DELETE FROM claims WHERE claim_id=?", (int(del_id),))
            st.warning("Claim deleted (if existed)")
            
# ---------- Alerts ----------


with tab_alerts:
    st.subheader("🚨 Alerts & Notifications")

    # 1. Expiring food in next 3 days
    expiring_food = run_query("""
        SELECT food_name, quantity, expiry_date, location 
        FROM food_listings 
        WHERE date(expiry_date) <= date('now', '+3 day')
        ORDER BY expiry_date ASC
    """)
    if not expiring_food.empty:
        st.error("⚠️ Some food items are expiring soon (within 3 days)!")
        st.dataframe(expiring_food)
    else:
        st.success("✅ No food is nearing expiry in the next 3 days.")

    # 2. Low stock (quantity <= 5)
    low_stock = run_query("""
        SELECT food_name, quantity, location, expiry_date
        FROM food_listings
        WHERE quantity <= 5
        ORDER BY quantity ASC
    """)
    if not low_stock.empty:
        st.warning("⚠️ Low stock items detected!")
        st.dataframe(low_stock)
    else:
        st.info("✅ No low stock alerts.")

    # 3. Pending claims
    pending_claims = run_query("""
        SELECT c.claim_id, r.name AS receiver, f.food_name, c.status, c.timestamp
        FROM claims c
        JOIN receivers r ON c.receiver_id = r.receiver_id
        JOIN food_listings f ON c.food_id = f.food_id
        WHERE LOWER(c.status) = 'pending'
        ORDER BY c.timestamp ASC
    """)
    if not pending_claims.empty:
        st.error("🚨 Pending claims need attention!")
        st.dataframe(pending_claims)
    else:
        st.success("✅ No pending claims.")


# ---------- Insights ----------
with tab_insights:
    st.subheader("🧠 Smart Insights Dashboard")

    # KPI Cards
    c1, c2, c3 = st.columns(3)
    top_city = run_query("SELECT location, COUNT(*) AS listings FROM food_listings GROUP BY location ORDER BY listings DESC LIMIT 1")
    top_food = run_query("SELECT food_type, COUNT(*) AS cnt FROM food_listings GROUP BY food_type ORDER BY cnt DESC LIMIT 1")
    top_receiver = run_query("""
        SELECT r.name, COUNT(c.claim_id) AS claims 
        FROM claims c 
        JOIN receivers r ON c.receiver_id = r.receiver_id
        GROUP BY r.name ORDER BY claims DESC LIMIT 1
    """)

    c1.metric("🏙️ Top City (Listings)", 
              top_city['location'].iloc[0] if not top_city.empty else "N/A", 
              int(top_city['listings'].iloc[0]) if not top_city.empty else 0)

    c2.metric("🍱 Most Common Food", 
              top_food['food_type'].iloc[0] if not top_food.empty else "N/A", 
              int(top_food['cnt'].iloc[0]) if not top_food.empty else 0)

    c3.metric("🤝 Top Receiver (Claims)", 
              top_receiver['name'].iloc[0] if not top_receiver.empty else "N/A", 
              int(top_receiver['claims'].iloc[0]) if not top_receiver.empty else 0)

    st.markdown("---")

    # Charts side by side
    col1, col2 = st.columns(2)

with col1:
    st.write("### 📊 Claims Status Trend")
    df_claims_trend = run_query("""
        SELECT SUBSTR(timestamp, 1, 7) AS month, status, COUNT(*) AS cnt
        FROM claims
        GROUP BY month, status
        ORDER BY month;
    """)
    if not df_claims_trend.empty:
        pivot = df_claims_trend.pivot(index="month", columns="status", values="cnt").fillna(0)
        st.line_chart(pivot)
    else:
        st.info("No claims data available to display trend.")


    with col2:
        st.write("### 🍽️ Meal Type Popularity")
        df_meals = run_query("SELECT meal_type, COUNT(*) AS cnt FROM food_listings GROUP BY meal_type")
        if not df_meals.empty:
            st.bar_chart(df_meals.set_index("meal_type"))

    st.markdown("---")

    # Deep dive analysis
    st.write("### 🔍 Expiry Risk Analysis")
    expiry = run_query("""
        SELECT location, COUNT(*) AS near_expiry 
        FROM food_listings
        WHERE date(expiry_date) <= date('now', '+5 day')
        GROUP BY location ORDER BY near_expiry DESC
    """)
    if not expiry.empty:
        st.bar_chart(expiry.set_index("location"))
    else:
        st.info("No items are nearing expiry in the next 5 days ✅")

# ---------- Reports ----------
with tab_reports:
    st.subheader("📑 Reports & Data Export")

    report_choice = st.selectbox("Choose a report to export", [
        "Providers List",
        "Receivers List",
        "Food Listings",
        "Claims",
        "Expiring Soon Food"
    ])

    if report_choice == "Providers List":
        df = run_query("SELECT * FROM providers ORDER BY provider_id")
    elif report_choice == "Receivers List":
        df = run_query("SELECT * FROM receivers ORDER BY receiver_id")
    elif report_choice == "Food Listings":
        df = run_query("SELECT * FROM food_listings ORDER BY expiry_date")
    elif report_choice == "Claims":
        df = run_query("SELECT * FROM claims ORDER BY timestamp DESC")
    elif report_choice == "Expiring Soon Food":
        df = run_query("SELECT * FROM food_listings WHERE date(expiry_date) <= date('now', '+3 day') ORDER BY expiry_date")

    if not df.empty:
        st.dataframe(df)

        # Download as CSV
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV",
            csv,
            f"{report_choice.replace(' ','_').lower()}.csv",
            "text/csv",
            key="download-csv"
        )

# ---------- Geo Map ----------
with tab_map:
    st.subheader("🌍 Geographic View of Food Network")

    # Separate providers and receivers
    df_providers = run_query("SELECT name, city FROM providers")
    df_receivers = run_query("SELECT name, city FROM receivers")

    col1, col2 = st.columns(2)

    with col1:
        st.write("### 🏢 Providers")
        if not df_providers.empty:
            st.dataframe(df_providers)
        else:
            st.info("No providers found")

    with col2:
        st.write("### 🏥 Receivers")
        if not df_receivers.empty:
            st.dataframe(df_receivers)
        else:
            st.info("No receivers found")

