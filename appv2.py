### For getting data
import yfinance as yf
import streamlit as st
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px 
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
from io import BytesIO


### For seaching ticker by company name
from googlesearch import search

### For rss
import json
import requests
import xmltojson
import numpy as np
from textblob import TextBlob
import datetime

### For python code
import urllib

#################CONFIG##########################
theme = "simple_white"
################################################

st.set_page_config(
     page_title="Market Monitoring",
    #  page_icon="🧊",
    #  layout="wide",
     initial_sidebar_state="expanded")

################################################

def name_convert(name):
    searchval = 'yahoo finance '+name
    link = []
    #limits to the first link
    for url in search(searchval, tld='es', lang='es', stop=1):
        link.append(url)
    print(link)
    link = str(link[0])
    link=link.split("/")
    if link[-1]=='':
        ticker=link[-2]
    else:
        x=link[-1].split('=')
        ticker=x[-1]

    return(ticker)

st.write("""
# Market Monitoring
""")

st.sidebar.header('Filter')

today = datetime.date.today()

def page_input():
    page = st.sidebar.radio("Page",("Home Page","Stock Monitoring"))
    return page 

page = page_input()


def user_input_features():
    ticker_company_name = st.sidebar.text_input("Ticker or Keywords", 'Alibaba Hong Kong')
    start_date = st.sidebar.text_input("Start Date", f'{today-datetime.timedelta(90)}')
    end_date = st.sidebar.text_input("End Date", f'{today+datetime.timedelta(1)}')
    ticker = st.sidebar.text_input("Or search by ticker for quicker runtime.", '')
    return ticker, ticker_company_name, start_date, end_date

symbol, comp_name, start, end = user_input_features()



if comp_name == None or comp_name == "":
    pass
else:
    symbol = name_convert(comp_name)

valid_date = True
try:
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)
except ValueError:
    st.error('Please enter a valid Date with format yyyy-mm-dd')
    valid_date = False


tickerData = yf.Ticker(symbol)
# st.error('Please enter a valid ticker')
valid_ticker = True
try:
    tickerInfo = tickerData.info
except:
    st.error('Please enter a valid ticker')
    valid_ticker = False

##### Run the app only when the ticker input is valid (Plus have information(?))
def page1():
    # @st.cache
    def tickerDataFrame(start,end):
        tickerDf = tickerData.history(start=start, end=end)
        return tickerDf
    tickerDf = tickerDataFrame(start,end)



    # st.write("""
    # # Simple Stock Price App
    # Shown are the stock **closing price** and ***volume*** of ***{}***
    # """.format(tickerInfo['longName']))

    try:
        Name = tickerInfo['longName']
    except KeyError:
        Name = tickerInfo['shortName']
    st.write(f"""
    # {Name}
    Last price at ***{round(tickerDf["Close"][-1],2)} {tickerInfo['currency']}***
    """)

    ################################################################################################################################
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
        title_text="<b>Stock Price and Trading Volume of {} ".format(Name),
        title_x=0.5,
        title_font_family="Helvetica",
        title_font_color="Black",
        title_font_size=18
    )

    fig.update_layout(
        yaxis=dict(range=[min(Y2),max(Y2*3.5)]),
        template=f"{theme}"
    )

    # Set x-axis title
    fig.update_xaxes(title_text="Date")

    # Set y-axes titles
    fig.update_yaxes(title_text="<b>Volume</b>",side = "right", secondary_y=False)
    fig.update_yaxes(title_text="<b>Pirce</b>",side = "left", secondary_y=True)
    st.plotly_chart(fig)

    def to_excel(df):
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Sheet1')
        writer.save()
        processed_data = output.getvalue()
        return processed_data

    def get_table_download_link(df):
        """Generates a link allowing the data in a given panda dataframe to be downloaded
        in:  dataframe
        out: href string
        """
        val = to_excel(df)
        b64 = base64.b64encode(val)  # val looks like b'...'
        return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="extract.xlsx">Download data as csv</a>' # decode b'abc' => abc


    with st.beta_expander('Data Table'):
        # st.line_chart(tickerDf.Close)
        st.dataframe(tickerDf)
        df = tickerDf # your dataframe
        st.markdown(get_table_download_link(df), unsafe_allow_html=True)

    with st.beta_expander('Stock Info'):
        st.json(tickerInfo)
    ########################################################################################################################################

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

    newsDf = get_news(Name,days=3)
    newsDf["Date"] = newsDf["Date"].dt.strftime("%d/%m %H:%M")
    newsDf = newsDf.set_index("Date")
    with st.beta_expander('Google News'):
        st.dataframe(newsDf)

    def get_file_content_as_string(path):
        url = 'https://raw.githubusercontent.com/alanwong626/market-monitoring/main/app.py'
        response = urllib.request.urlopen(url)
        return response.read().decode("utf-8")

    with st.beta_expander("This app's Python code"):
        st.code(get_file_content_as_string("streamlit_app.py"))
        st.markdown("[View on GitHub](https://github.com/alanwong626/market-monitoring)",unsafe_allow_html=True)

    with st.beta_expander("To do list"):
        toDo = dict(
            One = "Add option to compare multiple stocks",
            Two = "Create dashboard to get best/worst performing stocks of majot indexes (WIP)",
            Three = "Allow users to search a stock with company name",
            Four = "Add other sources to obtain data for other assets",
            Five = "Fix the news tap, allow user to click on hyperlink to news",
            Six = "Add main page to view most important information (to be defined)",
            Seven = "Add other ML features, inclduing sentiment scores(?)"
        )
        st.json(toDo)


if valid_ticker == True and valid_date == True:
    if page == "Homr Page":
        home_page()
    elif page == "Stock Monitoring":
        page1()