# Spending Visualizer

## Description:

This app allows a user to submit a bank statement CSV file, specifically tailored to those who use the mobile banking company, Chime.

Once inputted, this app allows the user to set categories for each of their purchases, which is stored in a json file, allowing the
user to save time categorizing common expenses

The app uses Pandas to manipulate the CSV, Streamlit to display the information to the user in a clean and organized matter, and Plotly
to make charts and graphs to help visualize the data

## Installation:

- ### Clone the repository

git clone https://github.com/nicholas-peters/spending-visualizer.git

cd spending-visualizer.git

- ### Create a virtual environment
  
python3 -m venv venv

source ./venv/bin/activate

- ### Download dependencies
  
pip install streamlit pandas plotly

Now you can run the app using the command: streamlit run app.py

## How to Use:

- Download a bank statement from the Chime website
- Convert the PDF statement into a CSV file (Tabula works great)
- Upload your CSV file
- Create custom spending categories and organize your transactions
- View data about your spending with interactive charts and graphs

## Future improvements:

- Add month-by-month comparisons through separate bank statements
- Allow the user to set a personal budget goal, and see their progress





