"""
Data Page
"""
import streamlit as st
from app.ui.base_page import BasePage

class DataPage(BasePage):
    def render(self):
        st.header('Data & Tables')
        st.write('Inspect uploaded data and prepared metrics. You can download the merged metrics as CSV for offline use.')

        st.subheader('Prepared metrics')
        st.dataframe(self.state.metrics_df)

        if self.state.metrics_df is not None and not self.state.metrics_df.empty:
            csv = self.state.metrics_df.to_csv(index=False)
            st.download_button('Download metrics CSV', data=csv, file_name='metrics.csv', mime='text/csv')
