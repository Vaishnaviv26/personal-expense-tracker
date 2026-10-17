import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
from datetime import date

st.set_page_config(
    page_title="Personal Expense Tracker",
    page_icon="💰",
    layout="wide"
)

# Database connection
conn = sqlite3.connect("expenses.db", check_same_thread=False)

conn.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_date TEXT,
    category TEXT,
    amount REAL,
    description TEXT
)
""")
conn.commit()

st.title("💰 Personal Expense Tracker")
st.markdown("""
<style>
.stApp {
    background-color: #f4f7fb;
}

[data-testid="stSidebar"] {
    background-color: #e8eef8;
}

h1 {
    color: #17365d;
    font-weight: 800;
}

h2, h3 {
    color: #24476b;
}

[data-testid="stMetric"] {
    background-color: white;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #dce5f1;
    box-shadow: 0 3px 10px rgba(0,0,0,0.04);
}

.stButton > button {
    border-radius: 8px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)
st.write("Manage your daily expenses and understand your spending.")

# Sidebar
st.sidebar.header("➕ Add New Expense")

with st.sidebar.form("expense_form", clear_on_submit=True):
    expense_date = st.date_input("Expense Date", value=date.today())

    category = st.selectbox(
        "Category",
        ["Food", "Travel", "Shopping", "Education", "Bills", "Other"]
    )

    amount = st.number_input(
        "Amount (₹)",
        min_value=0.01,
        value=100.0,
        step=10.0
    )

    description = st.text_input("Description")

    submitted = st.form_submit_button("Add Expense")

    if submitted:
        conn.execute(
            """INSERT INTO expenses
            (expense_date, category, amount, description)
            VALUES (?, ?, ?, ?)""",
            (str(expense_date), category, amount, description)
        )
        conn.commit()
        st.success("Expense added successfully!")
        st.rerun()

# Load expenses
df = pd.read_sql_query(
    "SELECT * FROM expenses ORDER BY expense_date DESC",
    conn
)

if not df.empty:
    df["expense_date"] = pd.to_datetime(df["expense_date"])
    today = pd.Timestamp.today()

    current_month = df[
        (df["expense_date"].dt.month == today.month) &
        (df["expense_date"].dt.year == today.year)
    ]

    total_expenses = df["amount"].sum()
    monthly_expenses = current_month["amount"].sum()

    col1, col2, col3 = st.columns(3)

    col1.metric("💸 Total Expenses", f"₹{total_expenses:,.2f}")
    col2.metric("📅 This Month", f"₹{monthly_expenses:,.2f}")
    col3.metric("🧾 Total Transactions", len(df))

    st.subheader("📊 Spending by Category")

    category_data = df.groupby("category")["amount"].sum()

    fig, ax = plt.subplots()
    category_data.plot(kind="bar", ax=ax)
    ax.set_ylabel("Amount (₹)")
    ax.set_xlabel("Category")
    ax.set_title("Expense Analysis")
    plt.xticks(rotation=30)
    plt.tight_layout()

    st.pyplot(fig)
    plt.close(fig)

    st.subheader("📋 All Expenses")

    display_df = df.copy()
    display_df["expense_date"] = display_df["expense_date"].dt.strftime("%Y-%m-%d")
    display_df = display_df.rename(columns={
        "expense_date": "Date",
        "category": "Category",
        "amount": "Amount (₹)",
        "description": "Description",
        "id": "ID"
    })

    st.dataframe(display_df, use_container_width=True)

    csv_data = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "📥 Download Expenses as CSV",
        data=csv_data,
        file_name="my_expenses.csv",
        mime="text/csv"
    )

    st.subheader("🗑️ Delete an Expense")

    expense_ids = df["id"].tolist()

    selected_id = st.selectbox(
        "Select Expense ID",
        expense_ids
    )

    if st.button("Delete Selected Expense"):
        conn.execute("DELETE FROM expenses WHERE id = ?", (selected_id,))
        conn.commit()
        st.success("Expense deleted!")
        st.rerun()

else:
    st.info("No expenses added yet. Use the sidebar to add your first expense!")

st.divider()
st.caption("Personal Expense Tracker | Built using Python, Streamlit, Pandas, Matplotlib and SQLite")

conn.close()