from BotConfig import *
import pyupbit

# Account
ubt = pyupbit.Upbit(UB_ACCESS_KEY_NAJU, UB_SECRET_KEY_NAJU)

# Ticker
tks = pyupbit.get_tickers("KRW")
print(tks)

print(pyupbit.get_current_price(tks))

# # Generate Neck Dataframe
# def gen_neck_df(df):

#     df['close_prev'] = df['close'].shift()
#     df['ma05'] = df['close'].rolling(5).mean()
#     df['ma20'] = df['close'].rolling(20).mean()
#     df['ma60'] = df['close'].rolling(60).mean()
#     df['ma05_prev'] = df['ma05'].shift()
#     df['ma20_prev'] = df['ma20'].shift()
#     df['ma60_prev'] = df['ma60'].shift()
#     height_5_20_max = df['high'].rolling(20).max()
#     height_5_20_min = df['low'].rolling(20).min()
#     df['height_5_20'] = (((height_5_20_max / height_5_20_min) - 1) * 100).shift(5)

#     return df

# # Generate DataFrame
# def gen_upt_df(tk, tf, lm):
#     ohlcv = pyupbit.get_ohlcv(ticker=tk, interval=tf, count=lm)
#     if not (ohlcv is None) and len(ohlcv) >= lm:

#         return gen_neck_df(ohlcv)

# # Balance Code List    
# def get_balance_info(tks):
#     bal_cur = pyupbit.get_current_price(tks)
#     bal_lst = ubt.get_balances()
#     bal_krw = 0
#     prc = 0
#     obj = {}
#     lst = []
#     if len(bal_lst) > 0:
#         for bl in bal_lst:
#             avgp = float(bl['avg_buy_price'])
#             blnc = float(bl['balance'])
#             tikr = bl['unit_currency'] + '-' + bl['currency']
#             if tikr != 'KRW-KRW':
#                 obj[tikr] = {
#                     'a': avgp,
#                     'b': blnc
#                 }
#                 prc = prc + (bal_cur[tikr] * blnc)
#                 lst.append(tikr)
#             else:
#                 prc = prc + blnc
#                 bal_krw = blnc

#     return prc, bal_krw, obj, lst