import streamlit as st
import pandas as pd
import numpy as np



##################################################################### CONFIG

config = {}



##################################################################### SIDEBAR

with st.sidebar:
	st.write('## Input data')
	uploaded_file = st.file_uploader("Upload CSV", type=".csv")
	use_example_file = st.checkbox("Use example file", False, help="Adult Data Set from UCI")
	
	
	#st.write('## Output file name settings')
	#outputfile_prefix = st.text_input('Prefix', value='describedf', placeholder='(optional)')
	#outputfile_dfname = st.text_input('Dataframe name', placeholder='(optional)')
	#outputfile_include_date = st.checkbox("Include date", True)
	#outputfile_include_time = st.checkbox("Include time", True)
	#outputfile_include_nrow = st.checkbox("Include number of instances", True)
	#outputfile_include_ncol = st.checkbox("Include number of columns", True)
	


##################################################################### MAIN PAGE
st.write('# Describe data frame')

st.write('## Introduction')

if st.checkbox('Objective'):
	st.write('''
			* Perform exploratory data analysis using [Jupyter notebook](https://jupyter.org/)
			* Data cleaning, feature engineering, and modelling
			* Build an app using [Streamlit](https://docs.streamlit.io/en/stable/)
			* Allow user to do exploratory analysis of a pre-selected suburb
			* Using the pre-trained model, allow user to estimate/forecast Housing price
		''')

if st.checkbox('Technical overview'):
	st.write('''
			* Data source: [Melbourne Housing Market](https://www.kaggle.com/anthonypino/melbourne-housing-market)
			* Exploratory data analysis notebook: [link](https://github.com/ferrysusanto11579/melb-housing/blob/main/notebook/Melbourne%20Housing%20Market%20-%20EDA.ipynb)
			* Import raw data
			* Data cleaning, missing data imputations, feature engineering
			* ML modelling (xgboost)
			* Model analysis (feature importance, explain the model using [SHAP](https://shap.readthedocs.io/en/latest/))
			* Save the data & trained model (used as an input to this app)
			* Build interactive visualisations (using altair package) to allow exploratory data analysis for a particular Suburb
			* Predict the House Price using the ML model
			* Display output for analysis
		''')

	
if use_example_file:
	uploaded_file = "adult.csv"

if uploaded_file:
	df = pd.read_csv(uploaded_file)
	st.markdown("### Data preview")
	st.dataframe(df.head())
