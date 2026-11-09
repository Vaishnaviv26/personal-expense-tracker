
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

# ---------- DATABASE ----------
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

conn.execute("""
CREATE TABLE IF NOT EXISTS settings (
    setting_key TEXT PRIMARY KEY,
    setting_value REAL
)
""")

conn.execute("""
INSERT OR IGNORE INTO settings (setting_key, setting_value)
VALUES ('monthly_budget', 10000)
""")
conn.commit()

CATEGORIES = [
    "Food", "Travel", "Shopping",
    "Education", "Bills", "Health", "Other"
]

# ---------- PROFESSIONAL DESIGN ----------
st.markdown("""

<style>
.stApp {
    background-color: #f5f7fb;
    color: #1e293b;
    font-family: 'Segoe UI', sans-serif;
}

section[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e2e8f0;
}

h1 {
    color: #17365d !important;
    font-weight: 750 !important;
}

h2, h3 {
    color: #243b53 !important;
    font-weight: 650 !important;
}

div[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0 3px 12px rgba(0,0,0,0.04);
}

div[data-testid="stMetricLabel"] {
    color: #64748b !important;
    font-weight: 600;
}

div[data-testid="stMetricValue"] {
    color: #17365d !important;
    font-weight: 750;
}

.stButton > button {
    background-color: #2457a6;
    color: white;
    border: none;
    border-radius: 9px;
    padding: 9px 18px;
    font-weight: 600;
    transition: 0.2s;
}

.stButton > button:hover {
    background-color: #17365d;
    color: white;
    border: none;
}

div[data-testid="stForm"] {
    background: white;
    padding: 18px;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
}

div[data-testid="stDataFrame"] {
    border: 1px solid #e2e8f0;
    border-radius: 12px;
}

hr {
    border-color: #e2e8f0;
}
</style>
""", unsafe_allow_html=True)

st.title("💰 Personal Expense Tracker")
st.write(
    "Manage your money, track spending and understand "
    "your financial habits."
)

# ---------- MONTHLY BUDGET ----------
budget_row = conn.execute("""
SELECT setting_value FROM settings
WHERE setting_key = 'monthly_budget'
""").fetchone()

monthly_budget = float(budget_row[0]) if budget_row else 10000.0

with st.sidebar.expander("💰 Monthly Budget", expanded=True):
    with st.form("budget_form"):
        new_budget = st.number_input(
            "Set monthly budget (₹)",
            min_value=0.0,
            value=monthly_budget,
            step=500.0
        )
        save_budget = st.form_submit_button("Save Budget")

        if save_budget:
            conn.execute("""
                UPDATE settings
                SET setting_value = ?
                WHERE setting_key = 'monthly_budget'
            """, (new_budget,))
            conn.commit()
            st.success("Budget saved!")
            st.rerun()

# ---------- ADD EXPENSE ----------
st.sidebar.header("➕ Add New Expense")

with st.sidebar.form("expense_form", clear_on_submit=True):
    expense_date = st.date_input("Expense Date", value=date.today())
    category = st.selectbox("Category", CATEGORIES)
    amount = st.number_input(
        "Amount (₹)", min_value=0.01, value=100.0, step=10.0
    )
    description = st.text_input("Description")
    submitted = st.form_submit_button("Add Expense")

    if submitted:
        conn.execute("""
            INSERT INTO expenses
            (expense_date, category, amount, description)
            VALUES (?, ?, ?, ?)
        """, (str(expense_date), category, amount, description))
        conn.commit()
        st.success("Expense added successfully!")
        st.rerun()

# ---------- LOAD DATA ----------
df = pd.read_sql_query(
    "SELECT * FROM expenses ORDER BY expense_date DESC, id DESC",
    conn
)

if df.empty:
    st.info("No expenses added yet. Use the sidebar to add your first expense!")
    st.caption("Your dashboard will appear here after you add an expense.")

else:
    df["expense_date"] = pd.to_datetime(df["expense_date"])
    today = pd.Timestamp(date.today())

    # Current month data
    month_df = df[
        (df["expense_date"].dt.month == today.month)
        & (df["expense_date"].dt.year == today.year)
    ]

    total_spending = float(df["amount"].sum())
    monthly_spending = float(month_df["amount"].sum())
    remaining_budget = monthly_budget - monthly_spending
    # Previous Month Spending
previous_month = today - pd.DateOffset(months=1)

previous_month_df = df[
    (df["expense_date"].dt.month == previous_month.month) &
    (df["expense_date"].dt.year == previous_month.year)
]

previous_month_spending = float(previous_month_df["amount"].sum())

# Monthly Spending Difference
spending_difference = monthly_spending - previous_month_spending
    # ---------- SUMMARY CARDS ----------
    st.subheader("📊 Financial Overview")

    col1, col2 , col3,col4 = st.columns(4)

    col1.metric("💸 Total Spending", f"₹{total_spending:,.2f}")
    col2.metric("📅 This Month", f"₹{monthly_spending:,.2f}")
    col3.metric("💰 Monthly Budget", f"₹{monthly_budget:,.2f}")
    col4.metric("🏦 Budget Remaining", f"₹{remaining_budget:,.2f}")

    if monthly_budget > 0:
        used_percent = monthly_spending / monthly_budget
        st.write("**Monthly Budget Usage**")
        st.progress(min(used_percent, 1.0))
        st.caption(f"{used_percent * 100:.1f}% of your budget used")

        if used_percent > 1:
            st.error("Your monthly spending has exceeded the budget!")
        elif used_percent >= 0.8:
            st.warning("You have used at least 80% of your monthly budget.")
        else:
            st.success("Your spending is within your monthly budget.")
    # Monthly Spending Comparison
st.subheader("📈 Monthly Spending Comparison")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Previous Month Spending",
        f"₹{previous_month_spending:,.2f}"
    )

with col2:
    st.metric(
        "Spending Change",
        f"₹{spending_difference:,.2f}",
        delta_color="inverse"
    )
    # ---------- FILTERS ----------
    st.subheader("🔎 Filter Expenses")

    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        start_date = st.date_input(
            "From date",
            value=df["expense_date"].min().date(),
            key="filter_start"
        )

    with filter_col2:
        end_date = st.date_input(
            "To date",
            value=date.today(),
            key="filter_end"
        )

    with filter_col3:
        selected_category = st.selectbox(
            "Category",
            ["All Categories"] + CATEGORIES
        )

    if start_date > end_date:
        st.error("The start date must be before the end date.")
        filtered_df = df.iloc[0:0].copy()
    else:
        filtered_df = df[
            (df["expense_date"].dt.date >= start_date)
            & (df["expense_date"].dt.date <= end_date)
        ].copy()

        if selected_category != "All Categories":
            filtered_df = filtered_df[
                filtered_df["category"] == selected_category
            ]

    st.caption(
        f"{len(filtered_df)} transactions found | "
        f"Filtered total: ₹{filtered_df['amount'].sum():,.2f}"
    )

    # ---------- CHARTS ----------
    st.subheader("📈 Spending Analytics")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.write("**Spending by Category**")

        category_data = filtered_df.groupby("category")["amount"].sum()

        if not category_data.empty:
            fig, ax = plt.subplots(figsize=(7, 4))
            category_data.sort_values().plot(
                kind="barh", ax=ax
            )
            ax.set_xlabel("Amount (₹)")
            ax.set_ylabel("Category")
            ax.set_title("Category-wise Expenses")
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
        else:
            st.info("No data available for this filter.")

    with chart_col2:
        st.write("**Monthly Spending Trend**")

        monthly_data = (
            df.set_index("expense_date")
            .resample("MS")["amount"]
            .sum()
        )

        if not monthly_data.empty:
            fig, ax = plt.subplots(figsize=(7, 4))
            monthly_data.plot(kind="line", marker="o", ax=ax)
            ax.set_xlabel("Month")
            ax.set_ylabel("Amount (₹)")
            ax.set_title("Month-wise Expenses")
            fig.autofmt_xdate()
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
        else:
            st.info("Not enough data to display a trend.")

    # ---------- DATA INSIGHTS ----------
    st.subheader("🤖 Spending Insights")

    highest_category = df.groupby("category")["amount"].sum()
    # Average daily spending
    df["expense_date"] = pd.to_datetime(df["expense_date"])

    daily_spending = df.groupby(
        df["expense_date"].dt.date
    )["amount"].sum()

    average_daily_spending = daily_spending.mean()
    insight_col1, insight_col2 = st.columns(2)

    with insight_col1:
            st.write("**Highest Spending Category**")
            if not highest_category.empty:
                top_category = highest_category.idxmax()
                top_amount = highest_category.max()
                st.info(f"{top_category}: ₹{top_amount:,.2f}")

    with insight_col2:
            st.write("**Average Expense per Transaction**")
            average_expense = df["amount"].mean()
            st.info(f"₹{average_expense:,.2f}")

    if monthly_spending > 0:
        st.write(
            f"You have spent ₹{monthly_spending:,.2f} "
            "during the current month."
        )

    # ---------- EXPENSE HISTORY ----------
    st.subheader("📋 Expense History")

    display_df = filtered_df.copy()
    display_df["expense_date"] = (
        display_df["expense_date"].dt.strftime("%Y-%m-%d")
    )
    display_df = display_df.rename(columns={
        "id": "ID",
        "expense_date": "Date",
        "category": "Category",
        "amount": "Amount (₹)",
        "description": "Description"
    })

    st.dataframe(display_df,width="stretch", hide_index=True)

    csv_data = filtered_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "📥 Download Filtered Expenses (CSV)",
        data=csv_data,
        file_name="my_expenses.csv",
        mime="text/csv"
    )

    # ---------- EDIT EXPENSE ----------
    st.subheader("✏️ Edit an Expense")

    with st.expander("Open expense editor"):
        edit_ids = df["id"].tolist()
        edit_id = st.selectbox(
            "Choose expense ID to edit",
            edit_ids,
            key="edit_id"
        )

        selected_row = df[df["id"] == edit_id].iloc[0]

        with st.form("edit_form"):
            edit_date = st.date_input(
                "New date",
                value=selected_row["expense_date"].date()
            )

            current_category = selected_row["category"]
            category_options = CATEGORIES.copy()

            if current_category not in category_options:
                category_options.append(current_category)

            edit_category = st.selectbox(
                "New category",
                category_options,
                index=category_options.index(current_category)
            )

            edit_amount = st.number_input(
                "New amount (₹)",
                min_value=0.01,
                value=float(selected_row["amount"]),
                step=10.0
            )

            old_description = selected_row["description"]
            edit_description = st.text_input(
                "New description",
                value="" if pd.isna(old_description) else str(old_description)
            )

            update_expense = st.form_submit_button("Update Expense")

            if update_expense:
                conn.execute("""
                    UPDATE expenses
                    SET expense_date = ?, category = ?,
                        amount = ?, description = ?
                    WHERE id = ?
                """, (
                    str(edit_date), edit_category, edit_amount,
                    edit_description, edit_id
                ))
                conn.commit()
                st.success("Expense updated!")
                st.rerun()

    # ---------- DELETE EXPENSE ----------
    st.subheader("🗑️ Delete an Expense")

    delete_id = st.selectbox(
        "Select expense ID to delete",
        df["id"].tolist(),
        key="delete_id"
    )

    confirm_delete = st.checkbox(
        "I confirm that I want to delete this expense."
    )

    if st.button("Delete Selected Expense"):
        if confirm_delete:
            conn.execute(
                "DELETE FROM expenses WHERE id = ?",
                (delete_id,)
            )
            conn.commit()
            st.success("Expense deleted!")
            st.rerun()
        else:
            st.warning("Please confirm before deleting.")

st.divider()
st.caption(
    "Personal Expense Tracker | Python • Streamlit • Pandas "
    "• Matplotlib • SQLite"
)

conn.close()
