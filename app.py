import streamlit as st
import pandas as pd
import plotly.express as px
import json

st.set_page_config(
    page_title="Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# ---------------- DATA UPLOAD ----------------

def load_data(file):
    ext = file.name.split(".")[-1].lower()

    if ext == "csv":
        return pd.read_csv(file)

    elif ext == "xlsx":
        return pd.read_excel(file)

    elif ext == "json":
        try:
            return pd.read_json(file)
        except ValueError:
            file.seek(0)
            return pd.json_normalize(json.load(file))

    else:
        raise ValueError("Unsupported file format")


# ---------------- VALIDATION ----------------

def validate_data(df):

    required = [
        "Order ID", "Order Date",
        "Sales", "Quantity", "Profit"
    ]

    missing = [c for c in required if c not in df.columns]

    if missing:
        return False, missing

    return True, []


# ---------------- PREPROCESSING ----------------

def preprocess_data(df):

    df = df.copy()

    df.columns = df.columns.str.strip()

    duplicates = df.duplicated().sum()

    df = df.drop_duplicates()

    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].apply(
            lambda x: x.strip() if isinstance(x, str) else x
        )

    for col in ["Order Date", "Ship Date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col], errors="coerce"
            )

    numeric = ["Sales", "Quantity", "Discount", "Profit"]

    for col in numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("$", "", regex=False),
                errors="coerce"
            )

            df[col] = df[col].fillna(df[col].median())

    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].fillna("Unknown")

    return df, duplicates


# ---------------- STATISTICAL SUMMARY ----------------

def statistical_summary(df):

    return df.describe(include="all").T


# ---------------- MAIN APPLICATION ----------------

st.title("📊 Sales Analytics Dashboard")

st.sidebar.title("Dashboard Controls")

uploaded_file = st.sidebar.file_uploader(
    "Upload Dataset",
    type=["csv", "xlsx", "json"]
)

if uploaded_file:

    try:

        df = load_data(uploaded_file)

        valid, errors = validate_data(df)

        if not valid:

            st.error("Missing required columns: " + ", ".join(errors))

        else:

            st.success("Dataset uploaded successfully!")

            st.subheader("1. Dataset Information")

            col1, col2, col3 = st.columns(3)

            col1.metric("Rows", df.shape[0])
            col2.metric("Columns", df.shape[1])
            col3.metric("Duplicates", df.duplicated().sum())

            st.write("Column Names:")
            st.write(df.columns.tolist())

            st.write("Data Types:")
            st.dataframe(
                df.dtypes.astype(str).rename("Data Type")
            )

            st.write("Missing Values:")
            st.dataframe(
                df.isnull().sum().rename("Missing Values")
            )

            st.write("Duplicate Records:", df.duplicated().sum())

            # PREPROCESSING

            st.subheader("2. Data Preprocessing")

            df, duplicates = preprocess_data(df)

            st.success("Data preprocessing completed!")

            st.write("Duplicates Removed:", duplicates)

            st.write("Statistical Summary:")
            st.dataframe(statistical_summary(df))

            # FILTERS

            st.sidebar.subheader("Interactive Filters")

            if "Region" in df.columns:

                regions = df["Region"].unique().tolist()

                selected_region = st.sidebar.multiselect(
                    "Select Region",
                    regions,
                    default=regions
                )

                df = df[df["Region"].isin(selected_region)]

            if "Category" in df.columns:

                categories = df["Category"].unique().tolist()

                selected_category = st.sidebar.multiselect(
                    "Select Category",
                    categories,
                    default=categories
                )

                df = df[df["Category"].isin(selected_category)]

            if "Segment" in df.columns:

                segments = df["Segment"].unique().tolist()

                selected_segment = st.sidebar.multiselect(
                    "Select Segment",
                    segments,
                    default=segments
                )

                df = df[df["Segment"].isin(selected_segment)]

            # KPIs

            st.subheader("3. Key Performance Indicators")

            sales = df["Sales"].sum()
            profit = df["Profit"].sum()
            orders = df["Order ID"].nunique()
            quantity = df["Quantity"].sum()

            margin = (
                profit / sales * 100
                if sales != 0 else 0
            )

            c1, c2, c3, c4, c5 = st.columns(5)

            c1.metric("Total Sales", f"${sales:,.2f}")
            c2.metric("Total Profit", f"${profit:,.2f}")
            c3.metric("Total Orders", orders)
            c4.metric("Quantity Sold", f"{quantity:,.0f}")
            c5.metric("Profit Margin", f"{margin:.2f}%")

            # CHART 1

            st.subheader("4. Sales by Category")

            if "Category" in df.columns:

                fig1 = px.bar(
                    df.groupby("Category", as_index=False)["Sales"].sum(),
                    x="Category",
                    y="Sales",
                    color="Category"
                )

                st.plotly_chart(fig1, use_container_width=True)

            # CHART 2

            st.subheader("5. Profit by Region")

            if "Region" in df.columns:

                fig2 = px.pie(
                    df,
                    names="Region",
                    values="Profit",
                    title="Regional Profit Distribution"
                )

                st.plotly_chart(fig2, use_container_width=True)

            # CHART 3

            st.subheader("6. Sales Trend")

            if "Order Date" in df.columns:

                trend = (
                    df.groupby("Order Date", as_index=False)["Sales"]
                    .sum()
                )

                fig3 = px.line(
                    trend,
                    x="Order Date",
                    y="Sales",
                    markers=True
                )

                st.plotly_chart(fig3, use_container_width=True)

            # CHART 4

            st.subheader("7. Quantity by Category")

            if "Category" in df.columns:

                fig4 = px.bar(
                    df.groupby("Category", as_index=False)["Quantity"].sum(),
                    x="Category",
                    y="Quantity",
                    color="Category"
                )

                st.plotly_chart(fig4, use_container_width=True)

            # FINAL DATA

            st.subheader("8. Processed Dataset")

            st.dataframe(df, use_container_width=True)

            st.download_button(
                "Download Cleaned CSV",
                df.to_csv(index=False),
                "cleaned_sales_data.csv",
                "text/csv"
            )

    except Exception as e:

        st.error(f"Error: {e}")

else:

    st.info("Upload your sales dataset to start.")