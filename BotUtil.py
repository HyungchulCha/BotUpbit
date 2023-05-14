from BotConfig import *
import pandas as pd
import numpy as np
import os
import pickle
import requests
import math

def gen_neck_df(df, is_yf=False):

    if is_yf:
        df['high'] = df['High']
        df['low'] = df['Low']
        df['close'] = df['Adj Close']
        df['volume'] = df['Volume']

    if not (df is None):

        df['close_prev'] = df['close'].shift()
        df['ma05'] = df['close'].rolling(5).mean()
        df['ma20'] = df['close'].rolling(20).mean()
        df['ma60'] = df['close'].rolling(60).mean()
        df['ma05_prev'] = df['ma05'].shift()
        df['ma20_prev'] = df['ma20'].shift()
        df['ma60_prev'] = df['ma60'].shift()
        height_5_20_max = df['high'].rolling(20).max()
        height_5_20_min = df['low'].rolling(20).min()
        df['height_5_20'] = (((height_5_20_max / height_5_20_min) - 1) * 100).shift(5)

        return df
    
    
def RSI(df, period=14):
    if not (df is None):
        diff = df['close'] - df['close'].shift(1)
        df['rsi_up'] = np.where(diff>=0, diff, 0)
        df['rsi_dn'] = np.where(diff <0, diff.abs(), 0)
        au = df['rsi_up'].ewm(alpha=(1/period), min_periods=period).mean()
        ad = df['rsi_dn'].ewm(alpha=(1/period), min_periods=period).mean()
        df['rsi'] = au / (au + ad) * 100
        df.drop(['rsi_up', 'rsi_dn'], axis=1, inplace=True)
        return df
    

def MACD(df, s=12, l=26, sgn=9):
    if not (df is None):
        df['macd'] = df['close'].ewm(span=s, min_periods=s-1, adjust=False).mean()- df['close'].ewm(span=l, min_periods=l-1, adjust=False).mean()
        df['macd_signal'] = df['macd'].ewm(span=sgn, min_periods=sgn-1, adjust=False).mean()
        df['macd_osc'] = df['macd'] - df['macd_signal']
        df['macd_osc_diff'] = df['macd_osc'].diff()
        df.drop(['macd', 'macd_signal'], axis=1, inplace=True)
        return df
    

def VO(df, s=5, l=10):
    if not (df is None):
        vma05 = df['volume'].ewm(span=s, min_periods=s).mean()
        vma10 = df['volume'].ewm(span=l, min_periods=l).mean()
        df['volume_osc'] = ((vma05 - vma10) / vma10) * 100
        return df


def save_xlsx(url, df):
    df.to_excel(url)


def load_xlsx(url):
    return pd.read_excel(url)


def save_file(url, obj):
    with open(url, 'wb') as f:
        pickle.dump(obj, f)


def load_file(url):
    with open(url, 'rb') as f:
        return pickle.load(f)
    

def delete_file(url):
    if os.path.exists(url):
        for file in os.scandir(url):
            os.remove(file.path)


def get_qty(crnt_p, max_p):
    q = int(max_p / crnt_p)
    return 1 if q == 0 else q


def ror(pv, nv, pr=1, pf=0.0005, spf=0):
    cr = ((nv - (nv * pf) - (nv * spf)) / (pv + (pv * pf)))
    return pr * cr


def line_message(msg):
    print(msg)
    requests.post(LINE_URL, headers={'Authorization': 'Bearer ' + LINE_TOKEN}, data={'message': msg})