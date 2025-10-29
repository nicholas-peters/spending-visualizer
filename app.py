import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

category_json = "categories.json"


st.set_page_config(page_title = "Chime Statement Visualizer", layout="wide")

# css to make it look cool
st.markdown("""
<style>
  .stApp {
    background: #135057;
background: linear-gradient(0deg,rgba(19, 80, 87, 1) 0%, rgba(1, 17, 69, 1) 100%);
  }
  header[data-testid="stHeader"] {
    display: none;
  }
            
.stTabs [data-baseweb="tab"] {
    color: white;
    background-color: transparent;
}

.stTabs [data-baseweb="tab"]:hover {
    color: #eee;
}

.stTabs [aria-selected="true"] {
    color: #1dd0e0 !important; /* active tab text color */
}



</style>
""", unsafe_allow_html=True)

# keep categories stored
if "categories" not in st.session_state:
  st.session_state.categories = {
    "Uncategorized": []
  }

if os.path.exists(category_json):
  if os.path.getsize(category_json) > 0:
    try:
      with open(category_json, "r") as f:
        st.session_state.categories = json.load(f)
    except json.JSONDecodeError:
      st.session_state.categories = {"Uncategorized": []}



def categorize_transactions(df):
  df["CATEGORY"] = "Uncategorized"

  for category, keywords in st.session_state.categories.items():
    if category == "Uncategorized" or not keywords:
      continue

    lowered_keywords = [keyword.lower().strip() for keyword in keywords]
    for idx, row in df.iterrows():
      details = row["DESCRIPTION"].lower()
      if details in lowered_keywords:
        df.at[idx, "CATEGORY"] = category

  return df

def save_categories():
  with open(category_json, "w") as f:
    json.dump(st.session_state.categories, f)

def load_file(file):
  try:
    df = pd.read_csv(file)
    df.columns = [col.strip() for col in df.columns] # strip whitespace

    # Format the amount removing commas and $
    df["AMOUNT"] = df["AMOUNT"].str.replace(",", "")
    df["AMOUNT"] = df["AMOUNT"].str.replace("$", "", regex=False).astype(float)
    df["AMOUNT"] = df["AMOUNT"].abs()


    return categorize_transactions(df)
  except Exception as e:
    st.error(f"Error loading file: {str(e)}")
    return None

def add_keyword_to_category(category, keyword):
  keyword = keyword.strip()
  if keyword and keyword not in st.session_state.categories[category]:
    st.session_state.categories[category].append(keyword)
    save_categories()
    return True
  return False


def main():
    st.title("Statement Visualizer")
    input_file = st.file_uploader("Upload Chime CSV File", type=["csv"])
    
    if input_file is not None:
        df = load_file(input_file)
        if df is not None:
            purchases = df[df["TYPE"] == "Purchase"].copy().reset_index(drop=True)
            deposits = df[df["TYPE"] == "Deposit"].copy()
            other = df[~df["TYPE"].isin(["Purchase", "Deposit"])].copy()
            
            st.session_state.purchases = purchases.copy()
            
            tab1, tab2, tab3, tab4 = st.tabs(["Purchases", "Deposits", "Other", "Analyze"])
            
            with tab1: # purchases tab
                new_category = st.text_input("New Category Name")
                add_button = st.button("Add Category")
                if add_button and new_category:
                    if new_category not in st.session_state.categories:
                        st.session_state.categories[new_category] = []
                        save_categories()
                        st.rerun()
                
                st.subheader("Your Expenses")
                edited_df = st.data_editor(
                    st.session_state.purchases[["TRANSACTION DATE", "DESCRIPTION", "AMOUNT", "CATEGORY"]],
                    column_config={
                        "CATEGORY": st.column_config.SelectboxColumn(
                            "CATEGORY",
                            options = list(st.session_state.categories.keys())
                        )
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="category_editor"
                )
                
                save_button = st.button("Apply Changes", type="primary")
                if save_button:
                    for idx, row in edited_df.iterrows():
                        new_category = row["CATEGORY"]
                        original_category = st.session_state.purchases.iloc[idx]["CATEGORY"]
                        if new_category != original_category:
                            details = st.session_state.purchases.iloc[idx]["DESCRIPTION"]
                            add_keyword_to_category(new_category, details)
                    st.rerun()
            
            with tab2: # deposits tab
                st.write(deposits)
            
            with tab3: # others tab
                st.write(other)

            with tab4: # analyze tab
                st.subheader("Spending Visualizer")
                category_totals = st.session_state.purchases.groupby("CATEGORY")["AMOUNT"].sum().reset_index()
                category_totals = category_totals.sort_values("AMOUNT", ascending=False)
                st.dataframe(category_totals,
                             column_config={
                                "AMOUNT": st.column_config.NumberColumn("AMOUNT", format="%.2f")
                             },
                             use_container_width=True,
                             hide_index=True    
                )
                fig = px.pie(
                   category_totals,
                   values="AMOUNT",
                   names="CATEGORY",
                   title="Categorized Purchases"
                )
                st.plotly_chart(fig, use_container_width=True)

                # display spending changes by day graph
                st.subheader("Spending Changes")
                
                col1, col2 = st.columns(2)
                min_date = pd.to_datetime(st.session_state.purchases["TRANSACTION DATE"].min()).date()
                max_date = pd.to_datetime(st.session_state.purchases["TRANSACTION DATE"].max()).date()
                
                with col1:
                    start_date = st.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
                with col2:
                    end_date = st.date_input("End Date", max_date, min_value=min_date, max_value=max_date)
                
                purchases_copy = st.session_state.purchases.copy()
                purchases_copy["TRANSACTION DATE"] = pd.to_datetime(purchases_copy["TRANSACTION DATE"])
                mask = (purchases_copy["TRANSACTION DATE"].dt.date >= start_date) & \
                       (purchases_copy["TRANSACTION DATE"].dt.date <= end_date)
                filtered_purchases = purchases_copy[mask].copy()
                
                daily_data = filtered_purchases.copy()
                daily_data["Date"] = daily_data["TRANSACTION DATE"].dt.date
                daily_spending = daily_data.groupby("Date")["AMOUNT"].sum().reset_index()
                daily_spending.columns = ["Date", "Amount"]
                
                fig_daily = px.line(daily_spending, x="Date", y="Amount", 
                                   title="Spending by Day",
                                   markers=True)
                fig_daily.update_layout(xaxis_title="Day", yaxis_title="Money spent")
                st.plotly_chart(fig_daily, use_container_width=True)
                

main()
