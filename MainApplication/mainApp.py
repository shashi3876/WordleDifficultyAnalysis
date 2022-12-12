# Import libraries


# Import Libraries
import twint
import nest_asyncio




import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, render_template
from datetime import date,timedelta,datetime
import re


app = Flask(__name__)
nest_asyncio.apply()
# Load the data
file_path = 'Tweets_Wordle_Data.csv'
tweets = pd.read_csv(file_path)
tweets['Date']= pd.to_datetime(tweets['Date']).dt.date
#tweets['Date']= tweets.Date.to_pydatetime()
tweets=tweets.drop(columns="Unnamed: 0")
tweets = tweets.set_index('Date')
wordleRegex = re.compile(r'Wordle \d\d\d [\dX]/6')

@app.route('/')
def home_endpoint():
    return render_template("index.html")

@app.route('/api',methods=['POST'])
def predict():
    # Get the data from the POST request.
    date = request.form.get("date")
    date=datetime.strptime(date,"%Y-%m-%d").date()
    
    print(date)
    print(type(date))
    #most_recent_date = tweets['Date'].max()
    #print(type(most_recent_date))
    #print(tweets['Date'])
    vals=getDataForDate(date)
    if type(vals)!=str:
        ans=f"<h1>Showing Wordle difficulty for {str(date)}</h1>"
        ans+=f"<table><tr><td>The success rate</td><td>{vals['Success']*100:.2f}%</td></tr>"
        ans+=f"<tr><td>The average number of attempts</td><td>{vals['Average']:.2f}</td></tr>"
        ans+=f"<tr><td>The difficulty percentile</td><td>{vals['Percentile Rank']:.2f}%</td></tr></table><br/>"
        ans+=getDifficultyLevel(vals['Percentile Rank'])
        ans+="Attempt distribution is as follows <br>"
        ans+=genTable(vals)
    else:
        ans=vals;
    return ans    
        
def genTable(vals):
    result="<table><tr><th>Attempts</th><th>Percentage</th></tr>"
    fields=['1','2','3','4','5','6','X']
    for i in fields:
        result+=f"<tr><td>{i}</td><td>{vals[i]:.1f}</td></tr>"
    result+="</table>"
    return result

def getDataForDate(date):
    if date>date.today():
        return 'Sorry. No data for future dates available.'
    elif (date in tweets.index):
        return tweets.loc[date]
    else:
        scrapeData()
        return 'Sorry. Data for this day is not available. Please try again in few minutes. We are scraping these data'

def getDifficultyLevel(percentile):
    if percentile>80:
        return '<p style="color:red;">This was a very hard word.</p>'
    elif percentile>60:
        return '<p style="color:pink;">This was a hard word.</p>'
    elif percentile>40:
        return '<p style="color:orange;">This was a medium word.</p>'
    elif percentile>80:
        return '<p style="color:blue;">This was an easy word.</p>'
    else:
        return '<p style="color:green;">This was a very easy word.</p>'
        
        
def scrapeData():
    file_path = 'Tweets_Wordle_Data.csv'
    tweets = pd.read_csv(file_path)
    tweets['Date']= pd.to_datetime(tweets['Date'])
    tweets=tweets.drop(columns="Unnamed: 0")
    most_recent_date = tweets['Date'].max()
    date_to_scrape=most_recent_date+ timedelta(days=1) 
    while(date_to_scrape<=date.today()):
        temp={}
        startDay = date_to_scrape.strftime("%Y-%m-%d")+' 00:00:00'
        endDay = date_to_scrape.strftime("%Y-%m-%d")+' 23:59:00'
        print(f'Start date={startDay} end date={endDay}')
        tweets_df=scrapePerDay(startDay,endDay)
        tweets_df=processTweets(tweets_df)
        temp['Date']=startDay
        ans=tweets_df.attempts.value_counts().sort_values()
        fields=['1','2','3','4','5','6','X']
        for key in fields:
            if key in ans.index:
                temp[key]=ans.loc[key]
            else:
                temp[key]=0
        temp['Num tweets']=len(tweets_df)

        temp['Success']=(temp['Num tweets']-temp['X'])/temp['Num tweets']
        temp['Average']=(temp['1']*1+temp['2']*2+temp['3']*3+temp['4']*4+temp['5']*5+temp['6']*6)/(temp['Num tweets']-temp['X'])
        temp['Percentile Rank'] = 0
        for i in fields:
            temp[i]=temp[i]*100/temp['Num tweets']
        tweets=tweets.append(temp,ignore_index=True)
        date_to_scrape=date_to_scrape+ timedelta(days=1) 
    tweets['Percentile Rank'] = tweets.Average.rank(pct = True)*100
    with open(file_path, 'w') as f:
        tweets.to_csv(f)
    tweets = tweets.set_index('Date')

def scrapePerDay(startDay,endDay):
    c = twint.Config()   
    c.Since = startDay
    c.Until = endDay
    c.Pandas = True
    c.Search = "Wordle"  # key words to look for.
    twint.run.Search(c)
    tweets_df = twint.storage.panda.Tweets_df
    return tweets_df

def processTweets(tweets_df):
    tweets=tweets_df[['tweet']]
    tweets['Wordle']=tweets.tweet.apply(findWordleReg)
    tweets=tweets[tweets['Wordle']!='None']
    tweets['version']=tweets.Wordle.str[7:10]
    tweets['attempts']=tweets.Wordle.str[-3]
    return tweets


def findWordleReg(tweet_ans):
    mo=wordleRegex.search(tweet_ans)
    if mo!=None:
        return mo.group()
    else:
        return 'None'
    
if __name__ == '__main__':
    app.run(port=5000, debug=True)