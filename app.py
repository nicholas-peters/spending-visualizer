import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

category_file = "categories.json"


st.set_page_config(page_title = "Chime Statement Visualizer", layout="wide")

# keep categories stored
if "categories" not in st.session_state:
  st.session_state.categories = {
    "Uncategorized": []
  }

if os.path.exists(category_file):
  if os.path.getsize(category_file) > 0:
    try:
      with open(category_file, "r") as f:
        st.session_state.categories = json.load(f)
    except json.JSONDecodeError:
      st.session_state.categories = {"Uncategorized": []}

def save_categories():
  with open(category_file, "w") as f:
    json.dump(st.session_state.categories, f)

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
            
            tab1, tab2, tab3 = st.tabs(["Purchases", "Deposits", "Other"])
            
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
            
            with tab2: # deposits tab
                st.write(deposits)
            
            with tab3: # 
                st.write(other)

main()