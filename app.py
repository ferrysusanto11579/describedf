import streamlit as st
import datetime as dt
import pandas as pd
import numpy as np
import scipy.stats as stats
import io

buffer = io.BytesIO()


##################################################################### CONFIG

config = {}



##################################################################### FUNCTIONS

def describe_df(df):
    ## default pd.DataFrame.describe()
    df_desc = df.describe(include='all').T
    cols_int = ['count']
    cols_float = ['mean','std','min','25%','50%','75%','max']
    df_desc[cols_int] = df_desc[cols_int].astype(int)
    df_desc[cols_float] = df_desc[cols_float].astype(float)

    ## Null in percentage
    df_desc['null%'] = np.round((df.shape[0]-df_desc['count']) / df.shape[0] * 100, 2)

    ## Data type
    df_dtypes = df.dtypes.to_frame()
    df_dtypes.columns = ['dtype']
    df_desc = pd.merge(df_desc, df_dtypes, left_index=True, right_index=True)

    ## Number of unique values & value stats/distributions
    def get_unique_stats(df, colname, n=10):
        gb = df.groupby(colname).size().reset_index()
        gb = gb.sort_values([0, colname], ascending=False)

        if gb.shape[0] > n*2:
            gb_top, gb_botm = gb.iloc[:n], gb.iloc[-n:]
        else:
            topn = int(np.ceil(1.*gb.shape[0]/2))
            bottomn = gb.shape[0] - topn
            gb_top, gb_botm = gb.iloc[:topn], gb.iloc[-bottomn:]

        valsstring_all = '  \n'.join([ ''+str(int(b))+': '+str(a) for a,b in gb.values])
        valsstring_top = '  \n'.join([ ''+str(int(b))+': '+str(a) for a,b in gb_top.values])
        valsstring_botm = '  \n'.join([ ''+str(int(b))+': '+str(a) for a,b in gb_botm.values])
        return len(gb), valsstring_all, valsstring_top, valsstring_botm
    df_desc[['nunique','uniquecounts','topN','bottomN']] = df_desc.apply(
        lambda r: get_unique_stats(df, r.name, n=10), axis=1, result_type='expand')

    ## stats.normtest for numerical columns
    ## If the p-val is very small, it means it is unlikely that the data came from a normal distribution
    ## URL: https://stackoverflow.com/questions/12838993/scipy-normaltest-how-is-it-used
    def get_normtest(df, colname):
        if pd.api.types.is_numeric_dtype(df[colname]):
            try:
                k2, p = stats.normaltest(df[colname], nan_policy='omit')
                return p
            except Exception as errmsg:
                return '(error) '+ str(errmsg)
        return np.nan
    df_desc['normtest_pval'] = df_desc.apply(lambda r: get_normtest(df, r.name), axis=1)

    ## 'Remarks' column
    def get_remarks(row):
        messages = []
        if row['null%'] > 0:
            if row['null%'] >= 30:
                messages.append('High null% - Drop column?')
            elif row['null%'] >= 10:
                messages.append('Med null% - Imputation? Custom feature engineering?')
            else:
                messages.append('Low null% - Drop rows? Custom feature engineering?')
        if row['dtype'] == 'object':
            messages.append('Object data type. Consideration & recommendation:')
            messages.append('- Is this ordinal (ordered)? Try mapping to integer')
            messages.append('- Is this nominal (non-ordered)? Try one-hot encoding')
        return '\n'.join(messages)
    df_desc['Remarks'] = df_desc.apply(lambda r: get_remarks(r), axis=1)


    ## Create multi-level columns by Type
    coltype = {
        'count': 'Summary',
        'null%': 'Summary',
        'nunique': 'Summary',
        'dtype': 'Summary',

        'mean': 'Numerical',
        'std': 'Numerical',
        'min': 'Numerical',
        '25%': 'Numerical',
        '50%': 'Numerical',
        '75%': 'Numerical',
        'max': 'Numerical',
        'normtest_pval': 'Numerical',

        #'uniquecounts': 'Analytics',
        'topN': 'Freq. of Values',
        'bottomN': 'Freq. of Values',

        'Remarks': 'Other',

        'top': '(to delete)', ## Categorical
        'freq': '(to delete)', ## Categorical
        'unique': '(to delete)',
    }
    coltypeorder = ['Summary', 'Numerical', 'Freq. of Values', 'Other']
    colsbytype = {t:[] for t in coltypeorder}
    colsorder = []
    for cname,ctype in coltype.items():
        if colsbytype.get(ctype) is not None:
            colsbytype[ctype].append(cname)
            colsorder.append(cname)
    df_desc = df_desc[colsorder]
    tups = [(coltype[col], col) for col in colsorder]
    df_desc.columns = pd.MultiIndex.from_tuples(tups)
    
    return df_desc

def to_xlsx(df, original_df=None, outputdir='.\\', prefix=None, dfname=None, include_date=True, include_time=True, include_nrow=True, include_ncol=True):
    ## Output to xlsx
    nrow, ncol = None, None
    if original_df is not None:
        nrow, ncol = original_df.shape
    tmpprefix = '' if prefix is None else prefix
    tmpname = '' if dfname is None else dfname
    tmptime = ''
    if include_date or include_time:
        tmptime = '%Y%m%d' if include_date else ''
        if include_time:
            tmptime = tmptime+'-%H%M%S' if tmptime!='' else '%H%M%S'
        tmptime = dt.datetime.now().strftime(tmptime)
    tmpnrow = 'ninstances%d'%(nrow) if original_df is not None and include_nrow else ''
    tmpncol = 'ncolumns%d'%(ncol) if original_df is not None and include_ncol else ''
    tmpcomponents = [tmpprefix, tmpname, tmptime, tmpnrow, tmpncol]
    tmpcomponents = [c for c in tmpcomponents if c!='']
    outputpath = outputdir + '%s.xlsx' % ('-'.join(tmpcomponents))
    
    colsorder = [c2 for c1,c2 in df.columns]

    sheetname = 'Sheet1'
    fmt_start_rown = 4
    fmt_end_rown = fmt_start_rown + df.shape[0]-1
    colchars = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    fmt_start_coln = 1
    fmt_end_coln = fmt_start_coln + df.shape[1]-1
    fmt_start_col, fmt_end_coln = colchars[fmt_start_coln], colchars[fmt_end_coln]
    with pd.ExcelWriter(buffer) as writer:
        ## Data
        df.to_excel(writer, sheet_name=sheetname)

        ## Reference URL: https://pythoninoffice.com/python-xlsxwriter-conditional-formatting/

        ## Prep for sheet formatting
        workbook, worksheet = writer.book, writer.sheets[sheetname]
        workbook.formats[0].set_text_wrap()

        ## Apply formatting: blanks
        fmt_blanks = workbook.add_format({'bg_color':'#F2F2F2'})
        worksheet.conditional_format('%s%d:%s%d'%(fmt_start_col,fmt_start_rown, fmt_end_coln,fmt_end_rown)
                                     , {'type':'blanks', 'format':fmt_blanks})

        ## Apply formatting: System error message
        fmt_errmsg = workbook.add_format({'color':'#C00000'})
        worksheet.conditional_format('%s%d:%s%d'%(fmt_start_col,fmt_start_rown ,fmt_end_coln,fmt_end_rown)
                                     , {'type':'text', 'criteria':'begins with','value':'(error)', 
                                        'format':fmt_errmsg})

        ## Apply formatting: dtype==object
        colindex = list(colsorder).index('dtype') + 1
        colchar = colchars[colindex]
        fmt_dtypeobject = workbook.add_format({'bg_color':'#D9D9D9'})
        worksheet.conditional_format('%s%d:%s%d'%(colchar,fmt_start_rown ,colchar,fmt_end_rown)
                                     , {'type':'text', 'criteria':'containing',
                                        'value':'object', 'format':fmt_dtypeobject})

        ## Apply formatting: null% > 30%
        colindex = list(colsorder).index('null%') + 1
        colchar = colchars[colindex]
        fmt_warning = workbook.add_format({'bg_color':'#FDE9D9'})
        fmt_warning1 = workbook.add_format({'bg_color':'#FCD5B4'})
        fmt_warning2 = workbook.add_format({'bg_color':'#FABF8F'})
        worksheet.conditional_format('%s%d:%s%d'%(colchar,fmt_start_rown, colchar,fmt_end_rown)
                                     , {'type':'cell', 'criteria':'>','value': 30, 'format':fmt_warning2})
        worksheet.conditional_format('%s%d:%s%d'%(colchar,fmt_start_rown, colchar,fmt_end_rown)
                                     , {'type':'cell', 'criteria':'>','value': 10, 'format':fmt_warning1})
        worksheet.conditional_format('%s%d:%s%d'%(colchar,fmt_start_rown, colchar,fmt_end_rown)
                                     , {'type':'cell', 'criteria':'>','value': 0, 'format':fmt_warning})

        ## Apply formatting: Feature name
        worksheet.set_column(0, 0, 20) 

        ## Apply formatting: Freq. of Values (topN, bottomN)
        colindex = list(colsorder).index('topN') + 1
        worksheet.set_column(colindex, colindex+1, 25) 

        ## Apply formatting: Remarks
        colindex = list(colsorder).index('Remarks') + 1
        worksheet.set_column(colindex, colindex, 50)
	
	# Close the Pandas Excel writer and output the Excel file to the buffer
        writer.save()
        
        download_button = st.download_button(
            label="Download output (.xlsx)",
            data=buffer,
            file_name=outputpath,
            mime="application/vnd.ms-excel")
    return outputpath


##################################################################### SIDEBAR

with st.sidebar:
	st.write('# Input data')
	uploaded_file = st.file_uploader("Upload CSV", type=".csv")
	use_example_file = st.checkbox("Use example file", False, help="Adult Data Set from UCI")
		
	st.write('# Output settings')
	outputfile_prefix = st.text_input('Filename Prefix', value='describedf', placeholder='(optional)')
	outputfile_dfname = st.text_input('Dataframe name', value='AdultDataFromUCI', placeholder='(optional)')
	outputfile_include_date = st.checkbox("Include date", True)
	outputfile_include_time = st.checkbox("Include time", True)
	outputfile_include_nrow = st.checkbox("Include number of instances", True)
	outputfile_include_ncol = st.checkbox("Include number of columns", True)
	
	
	
##################################################################### MAIN PAGE
st.write('# Describe data frame')

st.write('## Introduction')

if st.checkbox('Summary'):
	st.write('''
			* Data source: [Adult Data Set @ UCI](https://archive.ics.uci.edu/ml/datasets/Adult)
		''')

if st.checkbox('How to use this app'):
	st.write('''
			1. On the sidebar:
				* Upload data (in csv format) or tick the box to load the sample dataset
				* Configure the output file name
			2. Preview the data
			3. Investigate data statistics, including: count, null%, number of unique values, min, max, etc
			4. Download the _described data frame_ to your local to: easier investigation and note-taking, etc
		''')


if use_example_file:
	uploaded_file = "adult.csv"

if uploaded_file:
	df = pd.read_csv(uploaded_file)
	described_df = describe_df(df)
	
	st.write("## Data Preview")
	st.write('shape: %s'%(str(df.shape)))
	st.dataframe(df, height=300)

	st.write("## Describe Data")
	tmpdf = described_df.copy()
	for c in tmpdf.columns:
		if tmpdf[c].dtype == 'object':
			tmpdf[c] = tmpdf[c].replace('\n',', ')
	st.dataframe(tmpdf.astype(str))
	
	outputpath = to_xlsx( described_df
			    , original_df=df
			    , outputdir='.\\'
			    , prefix=outputfile_prefix
			    , dfname=outputfile_dfname
			    , include_date=outputfile_include_date
			    , include_time=outputfile_include_time
			    , include_nrow=outputfile_include_nrow
			    , include_ncol=outputfile_include_ncol)
