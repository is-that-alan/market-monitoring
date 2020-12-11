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

import investpy
###################################################################### HELPER EXPLAIN ######################################################################
# name_convert(keyword)                    --OUPUT--->    ticker (string);                               Convert keyword to ticker by doing a Google search
# index_performance(index_name)            --OUPUT--->    gainer (df), laggard (df);                     Get gainer and laggard of an index from MarketWatch (Google search to find link)
# get_table_download_link(df)              --OUPUT--->    download_link (html href);                     Convert dataframe to a downloadable csv and output download link as html
# get_news (keyword, days (optional))      --OUPUT--->    news (df);                                     Get news from Google's RSS and compute sentiment score, default to one day
# get_file_content_as_string()             --OUPUT--->    python_code (string);                          Get code of this project, we can then use st.code to display the code
# get_pct_changes(ticker_list)             --OUPUT--->    %changes (df), dates (dict), prices (df);      Calculate the % change -> daily, wtd, mtd, ytd (beta, need to figure out what to do with trading holiday, and may add quarterly)
##########################################################################################################################################################


##### Additional functions (To be added to helperFunctions #####
def pct_change_from_date(df):
    close = df.Close
    start = close[0]
    end = close[-1]
    change = round(((end/start)-1)*100,2)
    return f"{change}%"

def get_attribute_investing(df, security, attribute):
    country = df.loc[df.index[df["name"]== security].to_list()[0]][attribute]
    return country

def get_asset_data(asset_list,from_date,to_date,asset_type, asset_df):
    # commodity, bond, currency
    # etfs and funds need country
    if asset_type == "Bonds":
        func = lambda a,s,e : investpy.get_bond_historical_data(a,s,e)
    elif asset_type == "Currencies":
        func = lambda a,s,e : investpy.get_currency_cross_historical_data(a,s,e)
    elif asset_type == "ETFs":
        func = lambda a,s,e,c : investpy.get_etf_historical_data(a,c,s,e)
    elif asset_type == "Funds":
        func = lambda a,s,e, c : investpy.get_fund_historical_data(a, c,s,e)
    elif asset_type == "Commodities":
        func = lambda a,s,e : investpy.get_commodity_historical_data(a,s,e)
    elif asset_type == "Indices":
        func = lambda a,s,e, c : investpy.get_index_historical_data(a,c,s,e)
    elif asset_type == "Crypto":
        func = lambda a,s,e : investpy.get_crypto_historical_data(a,s,e)    
    df_list = []
    for asset in asset_list:
        if asset_type != "ETFs" and asset_type != "Funds" and asset_type != "Indices":
            df = func(asset,from_date,to_date)
            df_list.append(df)
        else:
            country = get_attribute_investing(asset_df, asset, 'country')
            df = func(asset,from_date,to_date, country)
            df_list.append(df)
    close_list = [df.Close for df in df_list]
    print(close_list)
    close_df = pd.concat(close_list,axis=1)
    close_df.columns = asset_list
    return df_list, close_df

def get_news(query,days=1):
        def google_news(query, days):
            link = "https://news.google.com/news/rss/headlines/section/topic/BUSINESS/search?q={}+when:{}d".format(query,days)
            return link
        link = google_news(query,days)
        r = requests.get(link)
        res = json.loads(xmltojson.parse(requests.get(link).text))
        headlines =[]
        try:
            for item in res['rss']["channel"]['item']:
                headline = {}
                headline['Date'] = item['pubDate']
                headline['Title'] = item['title']
                headline['Link'] = item["link"]
                headlines.append(headline)
        except KeyError:
            st.write("""
            Data unavailable 
            """)
        news = pd.DataFrame(headlines)
        polarity = lambda x: round(TextBlob(x).sentiment.polarity,2)
        subjectivity = lambda x: round(TextBlob(x).sentiment.subjectivity,2)
        news_polarity = np.zeros(len(news['Title']))
        news_subjectivity = np.zeros(len(news['Title']))
        for idx, headline in enumerate(news["Title"]):
        #     try:
            news_polarity[idx] = polarity(headline)
            news_subjectivity[idx] = subjectivity(headline)
        #     except:
        #         pass
        news["Polarity"]=news_polarity
        date = lambda x : datetime.datetime.strptime(x.split(",")[1][1:-4],'%d %b %Y %H:%M:%S')
        news['Date'] = news["Date"].apply(date)
        return news

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
    5. Bonds: a Dashboard on bonds (Limited infomation at the moment)
    6. Investing: Tool to search with investpy (data from investing.com)
    7. View Source Code: Return source code of this projec
    """
    st.sidebar.title("Market Monitoring")
    app_mode = st.sidebar.radio("Choose  app mode",("Dashboard","Index","Stock","Multi-Stocks", "Bonds", "Investing","View Source Code"))
    if app_mode == "Dashboard":
        dashboard()
    elif app_mode == "Index":
        index()
    elif app_mode == "Stock":
        stock()
    elif app_mode == "Multi-Stocks":
        multi_stocks()
    elif app_mode == "Bonds":
        bonds()
    elif app_mode == "Investing":
        investing()
    elif app_mode == "View Source Code":
        source_code()
    else:
        raise RuntimeError

################################################## Dashboard ##################################################
def dashboard():
    st.title("Market Dashboard")
    st.markdown(" {}, {}".format(today.strftime("%A"),today.strftime("%d-%b-%y, %H:%M")))

    st.title("Let's create a table!")
    for i in range(1, 10):
        cols = st.beta_columns(5)
        cols[0].write(f'{i}')
        cols[1].write(f'{i * i}')
        cols[2].write(f'{i * i * i}')
        cols[3].write('x' * i)
        cols[4].write('y' * (10-i))
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
        
        def make_clickable(link):
            # target _blank to open new window
            # extract clickable text to display for your link
            # st.write(f"""{link}""")
            # text = link.split('=')[0]
            text = "Link"
            # st.write(f"""{text}""")
            return f'<a target="_blank" href="{link}">{text}</a>'

        

        # link is the column with hyperlinks
               

        newsDf = get_news(stock_ticker,days=3)
        newsDf["Date"] = newsDf["Date"].dt.strftime("%d/%m %H:%M")
        # newsDf = newsDf.set_index("Date")

        newsDf['Link'] = newsDf['Link'].apply(make_clickable)
        # newsDf = newsDf.to_html(escape=False)
        # st.write(df, unsafe_allow_html=True) 

        
        with st.beta_expander('Google News'):
            # st.table(newsDf)
            st.write(newsDf.to_html(escape=False, index=False), unsafe_allow_html=True)
            average_sentiment = round((sum(newsDf.Polarity)/len(newsDf.Polarity)),2)
            st.write(f"""Average Sentiment: {average_sentiment}""")

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
            pctDf, dates, prices = get_pct_changes(tickers)
            st.dataframe(pctDf)
            st.markdown(get_table_download_link(pctDf), unsafe_allow_html=True)
        elif ticker_mode == "Keyword":
            kw_list = []
            for kw in tickers:
                kw_list.append(name_convert(kw))
            pctDf, dates, prices = get_pct_changes(kw_list)
            st.dataframe(pctDf)
            st.markdown(get_table_download_link(pctDf), unsafe_allow_html=True)
        with st.beta_expander("Data"):
            st.dataframe(prices)
            st.markdown(get_table_download_link(prices), unsafe_allow_html=True)
        with st.beta_expander("Plot"):
            st.write("""To be improved""")
            st.plotly_chart(px.line(prices), template = template)
        
        
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
### Location of the table
table_num = dict(
    Australia = 1,
    China = 11,
    France = 17,
    Germany = 18,
    Hong_Kong = 20,
    India = 23,
    Indonesia = 24,
    Italy = 27,
    Japan = 28,
    Malaysia = 31,
    New_Zealand = 38,
    Philippines = 43,
    Singapore = 50,
    South_Korea = 54,
    Spain = 55,
    Taiwan = 58,
    Tailand = 59,
    Turkey = 60,
    UK = 63,
    US = 64
)

num_other = dict(
    US_indexes = 66,
    Commodities = 67,
    Main_currencies = 70
)

def bonds():
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    r = requests.get("https://www.investing.com/rates-bonds/world-government-bonds", headers=headers)
    tables = pd.read_html(r.text)
    for keys in table_num:
        with st.beta_expander(f"{keys.replace('_',' ')}"):
            st.dataframe((tables[table_num[keys]]).drop(['Unnamed: 0','Unnamed: 9'],axis=1))
################################################## Investing ##################################################


def investing():
    investing_mode = st.sidebar.selectbox("Select asset class", ("Bonds", "Currencies", "ETFs", "Funds", "Commodities", "Indices", "Crypto"))
    bonds_df = investpy.bonds.bonds_as_df()
    currencies_df = investpy.currency_crosses.currency_crosses_as_df()
    commodities_df = investpy.commodities.commodities_as_df()
    etfs_df = investpy.etfs.etfs_as_df()
    funds_df = investpy.funds.funds_as_df()
    indices_df = investpy.indices.indices_as_df()
    crypto_df = investpy.crypto.cryptos_as_df()
    if investing_mode == "Bonds":
        asset_select = st.sidebar.multiselect("Select Assets", bonds_df["name"])
        asset_df = bonds_df
    elif investing_mode == "Currencies":
        asset_select = st.sidebar.multiselect("Select Assets", currencies_df["name"])
        asset_df = currencies_df
    elif investing_mode ==  "ETFs":
        asset_select = st.sidebar.multiselect("Select Assets", etfs_df["name"])
        asset_df = etfs_df
    elif investing_mode == "Funds":
        asset_select = st.sidebar.multiselect("Select Assets", funds_df["name"])
        asset_df = funds_df
    elif investing_mode == "Commodities":
        asset_select = st.sidebar.multiselect("Select Assets", commodities_df["name"])
        asset_df = commodities_df
    elif investing_mode ==  "Indices":
        asset_select = st.sidebar.multiselect("Select Assets", indices_df["name"])
        asset_df = indices_df
    elif investing_mode ==  "Crypto":
        asset_select = st.sidebar.multiselect("Select Assets", crypto_df["name"])
        asset_df = crypto_df

    from_date = st.sidebar.text_input("Start Date",(today-datetime.timedelta(30)).strftime(format_date))
    to_date = st.sidebar.text_input("End Date",today.strftime(format_date))
    from_date = datetime.datetime.strptime(from_date, format_date).strftime('%d/%m/%Y')
    to_date = datetime.datetime.strptime(to_date, format_date).strftime('%d/%m/%Y')
    # st.write(f"{type(asset_select)}: {asset_select}, {from_date}, {to_date}")
    if asset_select != []:
        df_list, close_df = get_asset_data(asset_select, from_date,to_date,investing_mode,asset_df)
        st.dataframe(close_df)
        st.markdown(get_table_download_link(close_df), unsafe_allow_html=True)



    return None

################################################## View Source Code ##################################################
def source_code():
    soruce_code = get_file_content_as_string()
    code_display = st.code(soruce_code)
    link = st.markdown("[View on GitHub](https://github.com/alanwong626/market-monitoring)",unsafe_allow_html=True)
    return code_display, link

if __name__ == '__main__':
    main()