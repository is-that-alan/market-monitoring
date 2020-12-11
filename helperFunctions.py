### For getting data
import yfinance as yf
import streamlit as st
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

### For changes
from pandas_datareader import data,wb

################HELPER##########################
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

def index_performance(index):
        tables = pd.read_html(list(search(("market watch" + index),tld='es', lang='es',stop=1,num=1))[0],encoding="UTF-8")
        gainers = tables[-2]
        laggards = tables[-1]
        return gainers, laggards

def get_table_download_link(df):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    def to_excel(df):
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Sheet1')
        writer.save()
        processed_data = output.getvalue()
        return processed_data
    val = to_excel(df)
    b64 = base64.b64encode(val)  # val looks like b'...'
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="extract.xlsx">Download data as csv</a>' # decode b'abc' => abc

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
    except KeyError as e:
        return e
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

def get_file_content_as_string():
    url = 'https://raw.githubusercontent.com/alanwong626/market-monitoring/main/app.py'
    response = requests.get(url).text
    return response

def get_pct_changes(tickers):
    df_list = []
    price_list = []
    for ticker in tickers:
        l_year = datetime.date.today() - pd.tseries.offsets.YearBegin() - datetime.timedelta(1)
        prices = yf.download(ticker, start=l_year)['Close']
        today = prices.index[-1]
        yest= prices.index[-2]
        start = prices.index[0]
        print(start)
        week = today - pd.tseries.offsets.Week(weekday=0) - datetime.timedelta(3)
        month = today - pd.tseries.offsets.BMonthBegin() - datetime.timedelta(1)

        dates = dict(
            today = today,
            yesterday = yest,
            endLastYear = start,
            endLastWeek = week,
            endLastMonth = month
        )

        # calculate percentage changes
        close = prices[today]
        daily =  (close - prices[yest]) / prices[yest] * 100
        wtd = (close - prices[week]) / prices[week] * 100
        mtd = (close - prices[month]) / prices[month] * 100
        ytd = (close - prices[start]) / prices[start]* 100

        # create temporary frame for current ticker
        df = pd.DataFrame(data=[[ticker, close, daily, wtd, mtd,  ytd]], 
                          columns=['Ticker', 'Close', 'Daily (%)', 'WTD (%)', 'MTD (%)', 'YTD (%)'])
        df_list.append(df)
        price_list.append(prices)
    try:
        changes = pd.concat(df_list)
        priceDf = pd.concat(price_list, axis=1)
        priceDf.columns = tickers

    except:
        changes = df_list[0]
        # priceDf = price_list[0]
    
    print(priceDf)
    return changes,dates, priceDf
################################################