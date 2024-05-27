import streamlit as st
import pandas as pd
import numpy as np

# Title of the app
st.title('Simple Streamlit App')

# Create a DataFrame
data = pd.DataFrame(
    np.random.randn(100, 3),
    columns=['a', 'b', 'c']
)

# Display the DataFrame
st.write(data)

# Line chart
st.line_chart(data)
