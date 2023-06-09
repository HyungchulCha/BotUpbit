from BotConfig import *
from BotUtil import *
from dateutil.relativedelta import *
import datetime
import pyupbit
import time
import threading
import datetime
import os
import copy

class BotUpbit():


    def __init__(self):

        self.is_aws = True
        self.access_key = UB_ACCESS_KEY_AWS if self.is_aws else UB_ACCESS_KEY_NAJU
        self.secret_key = UB_SECRET_KEY_AWS if self.is_aws else UB_SECRET_KEY_NAJU
        self.ubt = pyupbit.Upbit(self.access_key, self.secret_key)
        
        self.q_l = []
        self.b_l = []
        self.o_l = {}
        self.p_l = {}

        self.time_order = None
        self.time_rebalance = None

        self.bool_start = False
        self.bool_balance = False
        self.bool_order = False
        
        self.prc_ttl = 0
        self.prc_lmt = 0

        self.const_up = 500000000
        self.const_dn = 5000

        self.prc_buy_min = 62500
        self.prc_buy_max = 5000000

    
    def init_per_day(self):

        if self.bool_balance == False:

            tn = datetime.datetime.now()
            tn_0 = tn.replace(hour=0, minute=0, second=0)
            tn_d = int(((tn - tn_0).seconds) % 300)
            print(tn_d)

            if tn_d <= 150:
                time.sleep(300 - tn_d - 150)
            else:
                time.sleep(300 - tn_d + 150)

            self.bool_balance = True

        # _tn = datetime.datetime.now()

        print('##################################################')

        self.ubt = pyupbit.Upbit(self.access_key, self.secret_key)

        self.q_l = pyupbit.get_tickers("KRW")
        prc_ttl, prc_lmt, _, bal_lst  = self.get_balance_info(self.q_l)
        self.b_l = list(set(self.q_l + bal_lst))
        self.prc_ttl = prc_ttl if prc_ttl < self.const_up else self.const_up
        self.prc_lmt = prc_lmt if prc_ttl < self.const_up else prc_lmt - self.const_up

        if os.path.isfile(FILE_URL_PRFT_3M):
            self.p_l = load_file(FILE_URL_PRFT_3M)
        else:
            self.p_l = {}
            save_file(FILE_URL_PRFT_3M, self.p_l)

        for mk in self.b_l:
            if not (mk in self.p_l):
                self.p_l[mk] = {'ttl_pft': 1, 'sum_pft': 0, 'fst_qty': 0}

        line_message(f'BotUpbit \nTotal Price : {self.prc_ttl} KRW \nSymbol List : {len(self.b_l)}')

        __tn = datetime.datetime.now()
        __tn_min = __tn.minute % 5
        __tn_sec = __tn.second

        self.time_rebalance = threading.Timer(300 - (60 * __tn_min) - __tn_sec + 150, self.init_per_day)
        self.time_rebalance.start()


    def stock_order(self):

        if self.bool_order == False:

            tn = datetime.datetime.now()
            tn_0 = tn.replace(hour=0, minute=0, second=0)
            tn_d = int(((tn - tn_0).seconds) % 300)
            time.sleep(300 - tn_d)
            self.bool_order = True

        _tn = datetime.datetime.now()

        # self.get_remain_cancel(self.b_l)

        _, _, bal_lst, _ = self.get_balance_info(self.q_l)
        sel_lst = []

        if os.path.isfile(FILE_URL_BLNC_3M):
            obj_lst = load_file(FILE_URL_BLNC_3M)
        else:
            obj_lst = {}
            save_file(FILE_URL_BLNC_3M, obj_lst)

        for symbol in self.b_l:

            is_notnul_obj = not (not obj_lst)
            is_symbol_bal = symbol in bal_lst
            is_symbol_obj = symbol in obj_lst

            df = self.gen_neck_df(self.gen_ubt_df(symbol, 'minute5', 80))

            if not (df is None):
                
                df_head = df.tail(2).head(1)
                cls_val = df_head['close'].iloc[-1]
                clp_val = df_head['close_prev'].iloc[-1]
                hgt_val = df_head['height_5_20'].iloc[-1]
                m05_val = df_head['ma05'].iloc[-1]
                m20_val = df_head['ma20'].iloc[-1]
                m60_val = df_head['ma60'].iloc[-1]

                cur_prc = float(cls_val)
                prc_buy = self.p_l[symbol]['ttl_pft'] * self.prc_buy_min
                prc_buy = self.prc_buy_max if (prc_buy > self.prc_buy_max) else self.prc_buy_min if (prc_buy < self.prc_buy_min) else prc_buy
                cur_bal = prc_buy / cur_prc
                is_posble_ord = self.prc_lmt > prc_buy

                if is_symbol_bal and (not is_symbol_obj):
                    obj_lst[symbol] = {'x': copy.deepcopy(bal_lst[symbol]['a']), 'a': copy.deepcopy(bal_lst[symbol]['a']), 's': 1, 'd': datetime.datetime.now().strftime('%Y%m%d')}
                    # print(f'{symbol} : Miss Match, Obj[X], Bal[O] !!!')
                
                if (not is_symbol_bal) and is_symbol_obj:
                    obj_lst.pop(symbol, None)
                    # print(f'{symbol} : Miss Match, Obj[O], Bal[X] !!!')

                if is_symbol_bal and ((self.p_l[symbol]['fst_qty'] == 0) or (cur_prc * bal_lst[symbol]['b'] <= self.const_dn)):
                    self.p_l[symbol]['fst_qty'] = copy.deepcopy(bal_lst[symbol]['b'])
                    self.p_l[symbol]['sum_pft'] = 0
                    # print(f'{symbol} : Insert Quantity, Pft[X], Bal[O] !!!')

                if is_posble_ord and ((not is_symbol_bal) or (is_symbol_bal and (cur_prc * bal_lst[symbol]['b'] <= self.const_dn))):

                    if \
                    (1.1 < hgt_val < 5) and \
                    (m60_val < m20_val < m05_val < cls_val < clp_val * 1.05) and \
                    (m20_val < cls_val < m20_val * 1.05) \
                    :
                        resp = self.ubt.buy_market_order(symbol, prc_buy)
                        # print(resp)
                        obj_lst[symbol] = {'a': cur_prc, 'x': cur_prc, 's': 1, 'd': datetime.datetime.now().strftime('%Y%m%d')}
                        self.p_l[symbol]['fst_qty'] = cur_bal
                        self.p_l[symbol]['sum_pft'] = 0
                        print(f'Buy - Symbol: {symbol}, Balance: {cur_bal}')
                        sel_lst.append({'c': '[B] ' + symbol, 'r': cur_bal})

                if is_symbol_bal and is_notnul_obj:
                    
                    t1 = 0.01
                    t2 = 0.015
                    t3 = 0.02
                    h1 = 1
                    h2 = 1
                    h3 = 1
                    ct = 0.975
                    hp = 1.05

                    if obj_lst[symbol]['x'] < cur_prc:

                        obj_lst[symbol]['x'] = cur_prc
                        
                        bal_fst = copy.deepcopy(bal_lst[symbol]['a'])
                        obj_max = copy.deepcopy(obj_lst[symbol]['x'])
                        sel_cnt = copy.deepcopy(obj_lst[symbol]['s'])
                        obj_pft = ror(bal_fst, obj_max)
                        bal_pft = ror(bal_fst, cur_prc)

                        ord_qty_00 = copy.deepcopy(bal_lst[symbol]['b'])
                        ord_qty_01 = ord_qty_00 * 0.3
                        ord_qty_02 = ord_qty_00 * 0.5
                        psb_ord_00 = cur_prc * ord_qty_00 > self.const_dn
                        psd_ord_01 = cur_prc * ord_qty_01 > self.const_dn
                        psb_ord_02 = cur_prc * ord_qty_02 > self.const_dn

                        # print(f'{symbol} : Current Price {cur_prc}, Current Profit {round(bal_pft, 4)}, Increase !!!')

                        if 1 < bal_pft < hp:

                            if (sel_cnt == 1) and (h1 <= bal_pft) and psb_ord_00:

                                bool_01_end = False
                                if psd_ord_01:
                                    qty = ord_qty_01
                                elif psb_ord_02:
                                    qty = ord_qty_02
                                else:
                                    qty = ord_qty_00
                                    bool_01_end = True

                                self.ubt.sell_market_order(symbol, qty)
                                _ror = ror(bal_fst * qty, cur_prc * qty)
                                print(f'Sell - Symbol: {symbol}, Profit: {round(_ror, 4)}')
                                sel_lst.append({'c': '[SH1] ' + symbol, 'r': round(_ror, 4)})
                                obj_lst[symbol]['d'] = datetime.datetime.now().strftime('%Y%m%d')
                                obj_lst[symbol]['s'] = sel_cnt + 1

                                if bool_01_end:
                                    obj_lst.pop(symbol, None)

                                self.set_profit_list(symbol, qty, _ror, bool_01_end)
                            
                            elif (sel_cnt == 2) and (h2 <= bal_pft) and psb_ord_00:

                                bool_02_end = False
                                if psb_ord_02:
                                    qty = ord_qty_02
                                else:
                                    qty = ord_qty_00
                                    bool_02_end = True

                                self.ubt.sell_market_order(symbol, qty)
                                _ror = ror(bal_fst * qty, cur_prc * qty)
                                print(f'Sell - Symbol: {symbol}, Profit: {round(_ror, 4)}')
                                sel_lst.append({'c': '[SH2] ' + symbol, 'r': round(_ror, 4)})
                                obj_lst[symbol]['d'] = datetime.datetime.now().strftime('%Y%m%d')
                                obj_lst[symbol]['s'] = sel_cnt + 1

                                if bool_02_end:
                                    obj_lst.pop(symbol, None)

                                self.set_profit_list(symbol, qty, _ror, bool_02_end)

                            elif (sel_cnt == 3) and (h3 <= bal_pft) and psb_ord_00:

                                self.ubt.sell_market_order(symbol, ord_qty_00)
                                _ror = ror(bal_fst * ord_qty_00, cur_prc * ord_qty_00)
                                print(f'Sell - Symbol: {symbol}, Profit: {round(_ror, 4)}')
                                sel_lst.append({'c': '[SH3] ' + symbol, 'r': round(_ror, 4)})
                                obj_lst[symbol]['d'] = datetime.datetime.now().strftime('%Y%m%d')
                                obj_lst[symbol]['s'] = sel_cnt + 1
                                obj_lst.pop(symbol, None)

                                self.set_profit_list(symbol, ord_qty_00, _ror, True)

                        elif (hp <= bal_pft) and psb_ord_00:

                            self.ubt.sell_market_order(symbol, ord_qty_00)
                            _ror = ror(bal_fst * ord_qty_00, cur_prc * ord_qty_00)
                            print(f'Sell - Symbol: {symbol}, Profit: {round(_ror, 4)}')
                            sel_lst.append({'c': '[S+] ' + symbol, 'r': round(_ror, 4)})
                            obj_lst.pop(symbol, None)

                            self.set_profit_list(symbol, ord_qty_00, _ror, True)

                    elif obj_lst[symbol]['x'] > cur_prc:
                        
                        bal_fst = copy.deepcopy(bal_lst[symbol]['a'])
                        obj_max = copy.deepcopy(obj_lst[symbol]['x'])
                        obj_pft = ror(bal_fst, obj_max)
                        bal_pft = ror(bal_fst, cur_prc)
                        los_dif = obj_pft - bal_pft
                        sel_cnt = copy.deepcopy(obj_lst[symbol]['s'])

                        ord_qty_00 = copy.deepcopy(bal_lst[symbol]['b'])
                        ord_qty_01 = ord_qty_00 * 0.3
                        ord_qty_02 = ord_qty_00 * 0.5
                        psb_ord_00 = cur_prc * ord_qty_00 > self.const_dn
                        psd_ord_01 = cur_prc * ord_qty_01 > self.const_dn
                        psb_ord_02 = cur_prc * ord_qty_02 > self.const_dn

                        # print(f'{symbol} : Max Price {obj_max}, Max Profit {round(obj_pft, 4)}, Current Price {cur_prc}, Current Profit {round(bal_pft, 4)}')

                        if 1 < bal_pft < hp:

                            if (sel_cnt == 1) and (t1 <= los_dif) and psb_ord_00:

                                bool_01_end = False
                                if psd_ord_01:
                                    qty = ord_qty_01
                                elif psb_ord_02:
                                    qty = ord_qty_02
                                else:
                                    qty = ord_qty_00
                                    bool_01_end = True

                                self.ubt.sell_market_order(symbol, qty)
                                _ror = ror(bal_fst * qty, cur_prc * qty)
                                print(f'Sell - Symbol: {symbol}, Profit: {round(_ror, 4)}')
                                sel_lst.append({'c': '[ST1] ' + symbol, 'r': round(_ror, 4)})
                                obj_lst[symbol]['d'] = datetime.datetime.now().strftime('%Y%m%d')
                                obj_lst[symbol]['s'] = sel_cnt + 1

                                if bool_01_end:
                                    obj_lst.pop(symbol, None)

                                self.set_profit_list(symbol, qty, _ror, bool_01_end)
                            
                            elif (sel_cnt == 2) and (t2 <= los_dif) and psb_ord_00:

                                bool_02_end = False
                                if psb_ord_02:
                                    qty = ord_qty_02
                                else:
                                    qty = ord_qty_00
                                    bool_02_end = True

                                self.ubt.sell_market_order(symbol, qty)
                                _ror = ror(bal_fst * qty, cur_prc * qty)
                                print(f'Sell - Symbol: {symbol}, Profit: {round(_ror, 4)}')
                                sel_lst.append({'c': '[ST2] ' + symbol, 'r': round(_ror, 4)})
                                obj_lst[symbol]['d'] = datetime.datetime.now().strftime('%Y%m%d')
                                obj_lst[symbol]['s'] = sel_cnt + 1

                                if bool_02_end:
                                    obj_lst.pop(symbol, None)

                                self.set_profit_list(symbol, qty, _ror, bool_02_end)

                            elif (sel_cnt == 3) and (t3 <= los_dif) and psb_ord_00:

                                self.ubt.sell_market_order(symbol, ord_qty_00)
                                _ror = ror(bal_fst * ord_qty_00, cur_prc * ord_qty_00)
                                print(f'Sell - Symbol: {symbol}, Profit: {round(_ror, 4)}')
                                sel_lst.append({'c': '[ST3] ' + symbol, 'r': round(_ror, 4)})
                                obj_lst[symbol]['d'] = datetime.datetime.now().strftime('%Y%m%d')
                                obj_lst[symbol]['s'] = sel_cnt + 1
                                obj_lst.pop(symbol, None)

                                self.set_profit_list(symbol, ord_qty_00, _ror, True)

                        elif (hp <= bal_pft) and psb_ord_00:

                            self.ubt.sell_market_order(symbol, ord_qty_00)
                            _ror = ror(bal_fst * ord_qty_00, cur_prc * ord_qty_00)
                            print(f'Sell - Symbol: {symbol}, Profit: {round(_ror, 4)}')
                            sel_lst.append({'c': '[S+] ' + symbol, 'r': round(_ror, 4)})
                            obj_lst.pop(symbol, None)

                            self.set_profit_list(symbol, ord_qty_00, _ror, True)

                        elif (bal_pft <= ct) and psb_ord_00:

                            self.ubt.sell_market_order(symbol, ord_qty_00)
                            _ror = ror(bal_fst * ord_qty_00, cur_prc * ord_qty_00)
                            print(f'Sell - Symbol: {symbol}, Profit: {round(_ror, 4)}')
                            sel_lst.append({'c': '[S-] ' + symbol, 'r': round(_ror, 4)})
                            obj_lst.pop(symbol, None)

                            self.set_profit_list(symbol, ord_qty_00, _ror, True)

        save_file(FILE_URL_BLNC_3M, obj_lst)
        save_file(FILE_URL_PRFT_3M, self.p_l)
        # print(self.p_l)

        sel_txt = ''
        for sl in sel_lst:
            sel_txt = sel_txt + '\n' + str(sl['c']) + ' : ' + str(sl['r'])

        __tn = datetime.datetime.now()
        __tn_min = __tn.minute % 5
        __tn_sec = __tn.second

        self.time_backtest = threading.Timer(300 - (60 * __tn_min) - __tn_sec, self.stock_order)
        self.time_backtest.start()

        line_message(f'BotUpbit \nStart : {_tn}, \nEnd : {__tn}, \nTotal Price : {float(self.prc_ttl)} KRW, {sel_txt}')


    # Generate Neck Dataframe
    def gen_neck_df(self, df):

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
    

    # Generate DataFrame
    def gen_ubt_df(self, tk, tf, lm):
        ohlcv = pyupbit.get_ohlcv(ticker=tk, interval=tf, count=lm)
        if not (ohlcv is None) and len(ohlcv) >= lm:

            return gen_neck_df(ohlcv)
        

    # Balance Code List    
    def get_balance_info(self, tks):
        bal_cur = pyupbit.get_current_price(tks)
        bal_lst = self.ubt.get_balances()
        bal_krw = 0
        prc = 0
        obj = {}
        lst = []
        if len(bal_lst) > 0:
            for bl in bal_lst:
                avgp = float(bl['avg_buy_price'])
                blnc = float(bl['balance'])
                tikr = bl['unit_currency'] + '-' + bl['currency']
                if tikr != 'KRW-KRW':
                    obj[tikr] = {
                        'a': avgp,
                        'b': blnc
                    }
                    prc = prc + (bal_cur[tikr] * blnc)
                    lst.append(tikr)
                else:
                    prc = prc + blnc
                    bal_krw = blnc

        return prc, bal_krw, obj, lst
    
        
    # Not Signed Cancel Order
    def get_remain_cancel(self, l):
        for _l in l:
            rmn_lst = self.ubt.get_order(_l)
            if len(rmn_lst) > 0:
                for rmn in rmn_lst:
                    self.ubt.cancel_order(rmn['uuid'])

    
    # Set Profit List
    def set_profit_list(self, symbol, qty, _ror, end=False):
        pft_sum = copy.deepcopy(self.p_l[symbol]['sum_pft'])
        pft_cur = (qty / self.p_l[symbol]['fst_qty']) * _ror
        self.p_l[symbol]['sum_pft'] = pft_sum + pft_cur

        if end:
            pft_ttl = copy.deepcopy(self.p_l[symbol]['ttl_pft'])
            pft_sum = copy.deepcopy(self.p_l[symbol]['sum_pft'])
            self.p_l[symbol]['ttl_pft'] = pft_ttl * pft_sum
            self.p_l[symbol]['sum_pft'] = 0

            print(self.p_l[symbol]['ttl_pft'])

            if self.p_l[symbol]['ttl_pft'] > 2:
                line_message(symbol)

    
    # All Sell
    def all_sell_order(self):
        _, _, bal_lst, _  = self.get_balance_info(self.q_l)
        for bl in bal_lst:
            resp = self.ubt.sell_market_order(bl, bal_lst[bl]['b'])
            print(resp)
            time.sleep(0.25)


if __name__ == '__main__':

    bu = BotUpbit()
    # bu.init_per_day()
    # bu.stock_order()
    # bu.all_sell_order()

    while True:

        try:

            tn = datetime.datetime.now()
            tn_start = tn.replace(hour=8, minute=58, second=25)

            if tn >= tn_start and bu.bool_start == False:
                bu.init_per_day()
                bu.stock_order()
                bu.bool_start = True

        except Exception as e:

            line_message(f"BotUpbit Error : {e}")
            break

