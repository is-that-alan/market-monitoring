import yfinance as yf
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px 
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
from helperFunctions import * # name_convert, index_performance, get_table_download_link, get_news, get_file_content_as_string, get_pct_changes

import pandas as pd
import datetime
from pandas_datareader import data,wb
###################################################################### HELPER EXPLAIN ######################################################################
# name_convert(keyword)                    --OUPUT--->    ticker (string);                  Convert keyword to ticker by doing a Google search
# index_performance(index_name)            --OUPUT--->    gainer (df), laggard (df);        Get gainer and laggard of an index from MarketWatch (Google search to find link)
# get_table_download_link(df)              --OUPUT--->    download_link (html href);        Convert dataframe to a downloadable csv and output download link as html
# get_news (keyword, days (optional))      --OUPUT--->    news (df);                        Get news from Google's RSS and compute sentiment score, default to one day
# get_file_content_as_string()             --OUPUT--->    python_code (string);             Get code of this project, we can then use st.code to display the code
# get_pct_changes(ticker_list)             --OUPUT--->    %changes (df), dates (dict);      Calculate the % change -> daily, wtd, mtd, ytd (beta, need to figure out what to do with trading holiday, and may add quarterly)
##########################################################################################################################################################


##### Additional functions (To be added to helperFunctions #####
def pct_change_from_date(df):
    close = df.Close
    start = close[0]
    end = close[-1]
    change = round(((end/start)-1)*100,2)
    return f"{change}%"


#################CONFIG##########################
template = "simple_white"

format_date = ("%Y-%m-%d")

today = datetime.date.today()

st.set_page_config(
     page_title="Market Monitoring",
    #  page_icon="🧊",
    #  layout="wide",
     initial_sidebar_state="expanded")

today = datetime.datetime.today()

#################CONFIG END#######################
   
##### MAIN #####
def main():
    """
    Select app mode
    1. Dashboard: Market Overview, predefined indexes, news and etc...
    2. Index: Search index performance, include data on gainers and laggards
    3. Stock: Get data of a single stock, also works for indexes
    4. Multi-Stocks: Compare and plot multiple stocks (in beta)
    5. View Source Code: Return source code of this project
    """
    st.sidebar.title("Market Monitoring")
    app_mode = st.sidebar.radio("Choose  app mode",("Dashboard","Index","Stock","Multi-Stocks","View Source Code"))
    if app_mode == "Dashboard":
        dashboard()
    elif app_mode == "Index":
        index()
    elif app_mode == "Stock":
        stock()
    elif app_mode == "Multi-Stocks":
        multi_stocks()
    elif app_mode == "View Source Code":
        source_code()
    else:
        raise RuntimeError

################################################## Dashboard ##################################################
def dashboard():
    st.title("Market Dashboard")
    st.markdown(" {}, {}".format(today.strftime("%A"),today.strftime("%d-%b-%y, %H:%M")))
    return None

################################################## Index ##################################################
def index():
    index_name = st.sidebar.text_input("Index", "")
    if index_name != "":
        index_symbol = name_convert(index_name)
        indexData = yf.Ticker(index_symbol)
        name = indexData.info["shortName"]
        indexDf = indexData.history(period="max")
        index_fig = px.line(indexDf["Close"],template="simple_white", title='Historical Performance of {}'.format(name))
        index_fig.update_xaxes(
            rangeslider_visible=False,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1 Month", step="month", stepmode="backward"),
                    dict(count=6, label="6 Month", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1 Year", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            )
        )
        st.plotly_chart(index_fig,template=template)

        gainers, laggards = index_performance(index_name)
        with st.beta_expander('Gainers'):
            st.dataframe(gainers)
        with st.beta_expander('Laggards'):
            st.dataframe(laggards)
        
        # with st.beta_expander('Percentage Change'):
        #     st.markdown(f"{index_symbol.replace(r'%5E',r'^')}")
        #     index_pct, index_dates = get_pct_changes(index_symbol.replace(r"%E5",r"^"))
        #     st.dateframe(index_pct)
        # with st.beta_expander("Dates"):
        #     try:
        #         for d in index_dates:
        #             st.write(f"""{d}: {index_dates[d].strftime('%d/%m/%Y')}""")
        #         st.write("""The dates might be a bit off if there is a holiday, dates might be shifted.""")
        #         st.write("""These dates are from the dataframe of the last asset in your search list.""")
        #     except:
        #         pass

    return None

################################################## Stock ##################################################
def stock():

    stock_mode = st.sidebar.selectbox("Ticker mode or Keyword mode", ("Keyword", "Ticker"))
    stock_ticker_input = st.sidebar.text_input("Ticker or Keywords", 'Alibaba Hong Kong')
    start = st.sidebar.text_input("Start Date", f'{(today-datetime.timedelta(90)).strftime(format_date)}')
    end = st.sidebar.text_input("End Date", f'{(today+datetime.timedelta(1)).strftime(format_date)}')
    
    if stock_ticker_input != "":
        if stock_mode == "Keyword":
            stock_ticker = name_convert(stock_ticker_input)
        elif stock_mode == "Ticker":
            stock_ticker = stock_ticker_input
        start = pd.to_datetime(start)
        end = pd.to_datetime(end)
        tickerData = yf.Ticker(stock_ticker)
        tickerInfo = tickerData.info
        def tickerDataFrame(start,end):
            tickerDf = tickerData.history(start=start, end=end)
            return tickerDf
        tickerDf = tickerDataFrame(start,end)
        try:
            name = tickerInfo['longName']
        except KeyError:
            name = tickerInfo['shortName']
        st.write(f"""
        # {name}
        Last price at ***{round(tickerDf["Close"][-1],2)} {tickerInfo['currency']}***
        """)
        st.write(f"""
        Percentage Change: {pct_change_from_date(tickerDf)}
        """)
        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add traces
        fig.add_trace(
            go.Bar(x=tickerDf.index,y = tickerDf.Volume, name="Volume",marker_color="#F6D55C"),
            secondary_y=False,
        )

        Y2 = tickerDf.Volume.values

        fig.add_trace(
            go.Line(x=tickerDf.index,y = tickerDf.Close, name="Close",line=dict(width=3,color="#173F5F")),
            secondary_y=True,
        )

        # Add figure title
        fig.update_layout(
            title_text="<b>Stock Price and Trading Volume of {} ".format(name),
            title_x=0.5,
            title_font_family="Helvetica",
            title_font_color="Black",
            title_font_size=18
        )

        fig.update_layout(
            yaxis=dict(range=[min(Y2),max(Y2*3.5)]),
            template=f"{template}"
        )

        # Set x-axis title
        fig.update_xaxes(title_text="Date")

        # Set y-axes titles
        fig.update_yaxes(title_text="<b>Volume</b>",side = "right", secondary_y=False)
        fig.update_yaxes(title_text="<b>Pirce</b>",side = "left", secondary_y=True)
        st.plotly_chart(fig)

        with st.beta_expander('Data Table'):
            # st.line_chart(tickerDf.Close)
            st.dataframe(tickerDf)
            df = tickerDf # your dataframe
            st.markdown(get_table_download_link(df), unsafe_allow_html=True)

        with st.beta_expander('Stock Info'):
            st.json(tickerInfo)

    return None

################################################## Multi-Stocks ##################################################
# @st.cache(suppress_st_warning=True)
def multi_stocks():
    # tickers = ["9988.HK","3311.HK","0005.HK"]
    ticker_mode = st.sidebar.selectbox("Ticker mode or Keyword mode", ("Keyword", "Ticker"))
    tickers_input = st.sidebar.text_input("Enter the stock tickers, separated by a ' , ' or ' ; ' ")
    tickers = tickers_input.replace(';',',').split(",")
    if tickers !=  [""]:
        if ticker_mode == "Ticker":
            pctDf, dates = get_pct_changes(tickers)
            st.dataframe(pctDf)
            st.markdown(get_table_download_link(pctDf), unsafe_allow_html=True)
        elif ticker_mode == "Keyword":
            kw_list = []
            for kw in tickers:
                kw_list.append(name_convert(kw))
            print(kw_list)
            pctDf, dates = get_pct_changes(kw_list)
            st.dataframe(pctDf)
            st.markdown(get_table_download_link(pctDf), unsafe_allow_html=True)

    with st.beta_expander("Dates"):
        try:
            for d in dates:
                st.write(f"""{d}: {dates[d].strftime('%d/%m/%Y')}""")
            st.write("""The dates might be a bit off if there is a holiday, dates might be shifted.""")
            st.write("""These dates are from the dataframe of the last asset in your search list.""")
        except:
            pass
    with st.beta_expander("Delay Information"):
        delay = pd.read_html("https://help.yahoo.com/kb/exchanges-data-providers-yahoo-finance-sln2310.html")[0]
        st.dataframe(delay)
        link = st.markdown("[Yahoo Finance](https://help.yahoo.com/kb/exchanges-data-providers-yahoo-finance-sln2310.html)",unsafe_allow_html=True)

    with st.beta_expander("Percentage Change Calculation"):
        st.write("""To be implemented""")
        start_date_pct = st.text_input("Start Date", f'{(today-datetime.timedelta(90)).strftime(format_date)}')
        end_date_pct = st.text_input("End Date", f'{(today+datetime.timedelta(1)).strftime(format_date)}')
    return None
################################################## View Source Code ##################################################
def source_code():
    soruce_code = get_file_content_as_string()
    code_display = st.code(soruce_code)
    link = st.markdown("[View on GitHub](https://github.com/alanwong626/market-monitoring)",unsafe_allow_html=True)
    return code_display, link

if __name__ == '__main__':
    main()