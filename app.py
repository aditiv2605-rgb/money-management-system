import streamlit as st
import sqlite3
import pandas as pd
import calendar

from datetime import date
from pathlib import Path

# ==========================================
# 1. APPLICATION CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="My Finance | Money Manager",
    page_icon="💰",
    layout="wide"
)

# ==========================================
# 2. LIGHT THEME DESIGN
# ==========================================

st.markdown("""
<style>

.stApp {
    background-color: #F5F7FB;
    color: #263238;
}

[data-testid="stSidebar"] {
    background-color: #EAF0FA;
}

[data-testid="stMetric"] {
    background-color: white;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #E2E8F0;
}

h1, h2, h3 {
    color: #243B53;
}

.stButton button {
    border-radius: 8px;
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# 3. DATABASE CONNECTION
# ==========================================

DB_PATH = Path(__file__).parent / "money_management.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def create_table():

    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS money_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            transaction_date TEXT NOT NULL,
            note TEXT
        )
    """)

    conn.commit()
    conn.close()


create_table()


# ==========================================
# 4. CATEGORIES
# ==========================================

INCOME_CATEGORIES = [
    "Salary",
    "Pocket Money",
    "Freelancing",
    "Business",
    "Investment",
    "Other Income"
]

EXPENSE_CATEGORIES = [
    "Food",
    "Shopping",
    "Travel",
    "Education",
    "Bills",
    "Entertainment",
    "Healthcare",
    "Other Expenses"
]


# ==========================================
# 5. DATABASE FUNCTIONS
# ==========================================

def add_transaction(txn_type, category, amount,
                    txn_date, note):

    conn = get_connection()

    conn.execute("""
        INSERT INTO money_transactions
        (transaction_type, category, amount,
         transaction_date, note)
        VALUES (?, ?, ?, ?, ?)
    """, (
        txn_type,
        category,
        amount,
        txn_date.isoformat(),
        note
    ))

    conn.commit()
    conn.close()


def get_transactions():

    conn = get_connection()

    df = pd.read_sql_query("""
        SELECT *
        FROM money_transactions
        ORDER BY transaction_date DESC, id DESC
    """, conn)

    conn.close()

    return df


def delete_transaction(transaction_id):

    conn = get_connection()

    conn.execute(
        "DELETE FROM money_transactions WHERE id = ?",
        (transaction_id,)
    )

    conn.commit()
    conn.close()


# ==========================================
# 6. SIDEBAR NAVIGATION
# ==========================================

st.sidebar.title("💰 My Finance")

st.sidebar.caption(
    "PERSONAL FINANCE MANAGEMENT"
)

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "NAVIGATION",
    [
        "Dashboard",
        "Add Transaction",
        "Transaction History"
    ]
)

st.sidebar.markdown("---")

st.sidebar.write("Money Management System")

st.sidebar.caption(
    "Manage your money wisely."
)


# ==========================================
# 7. LOAD TRANSACTIONS
# ==========================================

df = get_transactions()

if not df.empty:

    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"],
        errors="coerce"
    )


# ==========================================
# 8. MONTHLY FINANCIAL DASHBOARD
# ==========================================

if page == "Dashboard":

    st.title("💰 Financial Dashboard")

    st.write(
        "Welcome to your personal finance dashboard."
    )

    st.markdown("---")

    # MONTH AND YEAR SELECTION

    st.subheader("📅 Monthly Financial Analysis")

    col1, col2 = st.columns(2)

    month_names = list(calendar.month_name)[1:]

    with col1:

        selected_month_name = st.selectbox(
            "Select Month",
            month_names,
            index=date.today().month - 1
        )

    with col2:

        available_years = []

        if not df.empty:

            available_years = (
                df["transaction_date"]
                .dropna()
                .dt.year
                .unique()
                .tolist()
            )

        current_year = date.today().year

        if current_year not in available_years:
            available_years.append(current_year)

        available_years = sorted(
            available_years,
            reverse=True
        )

        selected_year = st.selectbox(
            "Select Year",
            available_years
        )

    selected_month = (
        month_names.index(selected_month_name) + 1
    )

    # FILTER MONTHLY DATA

    if not df.empty:

        monthly_df = df[
            (df["transaction_date"].dt.month == selected_month)
            &
            (df["transaction_date"].dt.year == selected_year)
        ].copy()

    else:

        monthly_df = pd.DataFrame()

    st.markdown("---")

    # MONTHLY TOTALS

    monthly_income = 0

    monthly_expenses = 0

    if not monthly_df.empty:

        monthly_income = monthly_df.loc[
            monthly_df["transaction_type"] == "Income",
            "amount"
        ].sum()

        monthly_expenses = monthly_df.loc[
            monthly_df["transaction_type"] == "Expense",
            "amount"
        ].sum()

    monthly_savings = (
        monthly_income - monthly_expenses
    )

    # SAVINGS RATE

    if monthly_income > 0:

        savings_rate = (
            monthly_savings / monthly_income
        ) * 100

    else:

        savings_rate = 0

    # FINANCIAL OVERVIEW

    st.subheader(
        f"Financial Overview - {selected_month_name} {selected_year}"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Monthly Income",
        f"₹{monthly_income:,.2f}"
    )

    col2.metric(
        "Monthly Expenses",
        f"₹{monthly_expenses:,.2f}"
    )

    col3.metric(
        "Monthly Savings",
        f"₹{monthly_savings:,.2f}"
    )

    col4.metric(
        "Savings Rate",
        f"{savings_rate:.1f}%"
    )

    st.markdown("---")

    # EXPENSE AND INCOME BREAKDOWN

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("📉 Expense Breakdown")

        expenses = monthly_df[
            monthly_df["transaction_type"] == "Expense"
        ] if not monthly_df.empty else pd.DataFrame()

        if not expenses.empty:

            expense_summary = expenses.groupby(
                "category"
            )["amount"].sum()

            st.bar_chart(expense_summary)

        else:

            st.info(
                "No expenses recorded for this month."
            )

    with col2:

        st.subheader("📈 Income Breakdown")

        incomes = monthly_df[
            monthly_df["transaction_type"] == "Income"
        ] if not monthly_df.empty else pd.DataFrame()

        if not incomes.empty:

            income_summary = incomes.groupby(
                "category"
            )["amount"].sum()

            st.bar_chart(income_summary)

        else:

            st.info(
                "No income recorded for this month."
            )

    st.markdown("---")

    # DAILY EXPENSE ANALYSIS

    st.subheader("📊 Daily Spending Analysis")

    if not expenses.empty:

        daily_expenses = expenses.copy()

        daily_expenses["Day"] = (
            daily_expenses["transaction_date"].dt.day
        )

        daily_summary = daily_expenses.groupby(
            "Day"
        )["amount"].sum()

        st.bar_chart(daily_summary)

    else:

        st.info(
            "Daily spending information will appear here."
        )

    st.markdown("---")

    # RECENT MONTHLY TRANSACTIONS

    st.subheader("🧾 Monthly Transactions")

    if not monthly_df.empty:

        st.dataframe(
            monthly_df,
            width="stretch",
            hide_index=True
        )

    else:

        st.info(
            "No transactions available for the selected month."
        )


# ==========================================
# 9. ADD TRANSACTION
# ==========================================

elif page == "Add Transaction":

    st.title("➕ Add New Transaction")

    st.caption(
        "Record your income and expenses."
    )

    txn_type = st.selectbox(
        "Transaction Type",
        ["Income", "Expense"]
    )

    if txn_type == "Income":

        categories = INCOME_CATEGORIES

    else:

        categories = EXPENSE_CATEGORIES

    with st.form("transaction_form"):

        category = st.selectbox(
            "Category",
            categories
        )

        amount = st.number_input(
            "Amount (₹)",
            min_value=0.01,
            value=100.0,
            step=100.0
        )

        txn_date = st.date_input(
            "Transaction Date",
            value=date.today()
        )

        note = st.text_input(
            "Description / Note",
            placeholder="Enter transaction details"
        )

        submitted = st.form_submit_button(
            "Save Transaction",
            width="stretch"
        )

        if submitted:

            add_transaction(
                txn_type,
                category,
                amount,
                txn_date,
                note
            )

            st.success(
                "Transaction saved successfully!"
            )

            st.rerun()


# ==========================================
# 10. TRANSACTION HISTORY
# ==========================================

elif page == "Transaction History":

    st.title("📋 Transaction History")

    st.caption(
        "View and manage all your transactions."
    )

    if not df.empty:

        filter_type = st.selectbox(
            "Filter Transactions",
            [
                "All",
                "Income",
                "Expense"
            ]
        )

        if filter_type == "All":

            filtered_df = df.copy()

        else:

            filtered_df = df[
                df["transaction_type"] == filter_type
            ].copy()

        st.subheader("All Transactions")

        st.dataframe(
            filtered_df,
            width="stretch",
            hide_index=True
        )

        # DOWNLOAD CSV

        csv_data = df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "⬇️ Download Transactions as CSV",
            data=csv_data,
            file_name="money_transactions.csv",
            mime="text/csv",
            width="stretch"
        )

        st.markdown("---")

        # DELETE TRANSACTION

        st.subheader("🗑️ Delete Transaction")

        transaction_options = {
            f"ID {row.id} | {row.transaction_type} | {row.category} | ₹{row.amount:,.2f} | {row.transaction_date}":
            row.id
            for row in df.itertuples()
        }

        selected_transaction = st.selectbox(
            "Select transaction to delete",
            list(transaction_options.keys())
        )

        if st.button(
            "Delete Selected Transaction",
            type="primary"
        ):

            transaction_id = transaction_options[
                selected_transaction
            ]

            delete_transaction(transaction_id)

            st.success(
                "Transaction deleted successfully!"
            )

            st.rerun()

    else:

        st.info(
            "No transactions available yet. Add your first transaction!"
        )

# ==========================================
# 11. END OF APPLICATION
# ==========================================