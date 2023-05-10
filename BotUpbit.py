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

class BotCoin():


    def __init__(self):

        self.is_aws = True
        self.access_key = UB_ACCESS_KEY_AWS if self.is_aws else UB_ACCESS_KEY_NAJU
        self.secret_key = UB_SECRET_KEY_AWS if self.is_aws else UB_SECRET_KEY_NAJU
        self.pu = pyupbit.Upbit(self.access_key, self.secret_key)
        
        self.q_l = []
        self.r_l = []
        self.b_l = []

        self.time_order = None
        self.time_rebalance = None

        self.bool_start = False
        self.bool_balance = False
        self.bool_order = False
        
        self.tot_evl_price = 0
        self.buy_max_price = 0

    
    def init_per_day(self):

        if self.bool_balance == False:

            tn = datetime.datetime.now()
            tn_div = tn.minute % 30
            time.sleep(1800 - (60 * tn_div) - tn.second - 90)
            self.bool_balance = True

        _tn = datetime.datetime.now()
        _tn_micro = _tn.microsecond / 1000000

        self.pu = pyupbit.Upbit(self.access_key, self.secret_key)
        _b_l = self.get_balance_code_list()
        self.q_l = self.get_ticker_rank()
        self.r_l = list(set(_b_l).difference(self.q_l))
        self.b_l = list(set(self.q_l + _b_l))

        _ttl_evl_prc = int(self.get_total_price(_b_l))
        self.tot_evl_price = _ttl_evl_prc if _ttl_evl_prc < 400000000 else 400000000
        _buy_max_prc = self.tot_evl_price / len(self.q_l)
        self.buy_max_price = _buy_max_prc if _buy_max_prc > 5000 else 5000

        # line_message(f'BotUpbit \n평가금액 : {self.tot_evl_price}원 \n상위종목 : {self.q_l} \n다른종목 : {self.r_l}')
        line_message(f'BotUpbit \n평가금액 : {self.tot_evl_price}원')

        __tn = datetime.datetime.now()
        tn_diff = (__tn - _tn).seconds

        self.time_rebalance = threading.Timer(43200 - tn_diff - _tn_micro, self.init_per_day)
        self.time_rebalance.start()

    
    def get_total_price(self, _l):
        if 'KRW-KRW' in _l:
            _l.pop('KRW-KRW', None)
        _o = self.get_balance_code_list(True)
        _p = pyupbit.get_current_price(_l)
        _t = 0
        if len(_l) > 0:
            for l in _l:
                _t = _t + (float(_p[l]) * _o[l]['b'])
        _t = _t + _o['KRW-KRW']['t']
        return _t
    
    
    def get_ticker_rank(self):
        _tks = pyupbit.get_tickers("KRW")
        tks = pyupbit.get_current_price(_tks, True, True)[0]
        tks_srt = sorted(tks, key=lambda x: x['acc_trade_price_24h'])
        tks_rnk = []
        for tk in tks_srt:
            tks_rnk.append(tk['market'])
        return tks_rnk


    def stock_order(self):

        if self.bool_order == False:

            tn = datetime.datetime.now()
            tn_div = tn.minute % 30
            time.sleep(1800 - (60 * tn_div) - tn.second)
            self.bool_order = True

        _tn = datetime.datetime.now()

        print('##################################################')

        self.get_remain_cancel(self.b_l)

        bal_lst = self.get_balance_code_list(True)
        sel_lst = []

        if os.path.isfile(FILE_URL_BLNC_3M):
            obj_lst = load_file(FILE_URL_BLNC_3M)
        else:
            obj_lst = {}
            save_file(FILE_URL_BLNC_3M, obj_lst)

        i = 1
        for symbol in self.b_l:

            is_notnul_obj = not (not obj_lst)
            is_symbol_bal = symbol in bal_lst
            is_symbol_obj = symbol in obj_lst
            is_posble_ord = (bal_lst['KRW-KRW']['b'] > self.buy_max_price)
            is_remain_sym = symbol in self.r_l

            _df = pyupbit.get_ohlcv(symbol, interval='minute30', count=80)
            df = gen_neck_df(_df)

            if not (df is None):
                
                df_head = df.tail(2).head(1)
                cls_val = df_head['close'].iloc[-1]
                clp_val = df_head['close_prev'].iloc[-1]
                hgt_val = df_head['height_5_20'].iloc[-1]
                m05_val = df_head['ma05'].iloc[-1]
                m20_val = df_head['ma20'].iloc[-1]
                m60_val = df_head['ma60'].iloc[-1]

                cur_prc = float(cls_val)
                cur_bal = round((self.buy_max_price / cur_prc), 4)

                if is_symbol_bal and (not is_symbol_obj):
                    obj_lst[symbol] = {'x': copy.deepcopy(bal_lst[symbol]['a']), 'a': copy.deepcopy(bal_lst[symbol]['a']), 's': 1, 'd': datetime.datetime.now().strftime('%Y%m%d')}
                    print(f'{symbol} : Miss Match, Obj[X], Bal[O] !!!')
                
                if (not is_symbol_bal) and is_symbol_obj:
                    obj_lst.pop(symbol, None)
                    print(f'{symbol} : Miss Match, Obj[O], Bal[X] !!!')

                if (not is_remain_sym) and is_posble_ord and ((not is_symbol_bal) or (is_symbol_bal and (cur_prc * bal_lst[symbol]['b'] <= 10000))):

                    if \
                    (1.1 < hgt_val < 15) and \
                    (m60_val < m20_val < m05_val < cls_val < clp_val * 1.05) and \
                    (m20_val < cls_val < m20_val * 1.05) \
                    :
                        self.pu.buy_market_order(symbol, self.buy_max_price)
                        print(f'Buy - Symbol: {symbol}, Balance: {cur_bal}')
                        obj_lst[symbol] = {'a': cur_prc, 'x': cur_prc, 's': 1, 'd': datetime.datetime.now().strftime('%Y%m%d')}
                        sel_lst.append({'c': '[B]' + symbol, 'r': cur_bal})                    

                if is_symbol_bal and is_notnul_obj:

                    t1 = 0.035
                    t2 = 0.045
                    t3 = 0.055
                    ct = 0.8
                    hp = 100

                    if obj_lst[symbol]['x'] < cur_prc:
                        obj_lst[symbol]['x'] = cur_prc
                        obj_lst[symbol]['a'] = copy.deepcopy(bal_lst[symbol]['a'])

                        print(f'{symbol} : 현재가 {cur_prc}, Increase !!!')

                    if obj_lst[symbol]['x'] > cur_prc:
                        
                        bal_fst = bal_lst[symbol]['a']
                        bal_qty = bal_lst[symbol]['b']
                        obj_max = obj_lst[symbol]['x']
                        obj_pft = ror(bal_fst, obj_max)
                        bal_pft = ror(bal_fst, cur_prc)
                        los_dif = obj_pft - bal_pft
                        sel_cnt = copy.deepcopy(obj_lst[symbol]['s'])

                        ord_rto_01 = 0.2
                        ord_rto_02 = (3/8)
                        ord_qty_01 = bal_qty * ord_rto_01
                        ord_qty_02 = bal_qty * ord_rto_02
                        sam_qty_01 = (bal_qty == ord_qty_01)
                        sam_qty_02 = (bal_qty == ord_qty_02)
                        psb_ord_00 = cur_prc * bal_qty > 5000
                        psd_ord_01 = cur_prc * ord_qty_01 > 5000
                        psb_ord_02 = cur_prc * ord_qty_02 > 5000

                        print(f'{symbol} : 최고가 {obj_max}, 최고수익 {round(obj_pft, 4)}, 현재가 {cur_prc}, 현재수익 {round(bal_pft, 4)}')

                        if 1 < bal_pft < hp:

                            if (sel_cnt == 1) and (t1 <= los_dif) and psb_ord_00:

                                bool_01_end = False
                                if psd_ord_01:
                                    qty = ord_qty_01
                                elif psb_ord_02:
                                    qty = ord_qty_02
                                else:
                                    qty = bal_qty
                                    bool_01_end = True

                                self.pu.sell_market_order(symbol, qty)
                                _ror = ror(bal_fst * qty, cur_prc * qty)
                                print(f'Sell - Symbol: {symbol}, Profit: {round(_ror, 4)}')
                                sel_lst.append({'c': '[S1] ' + symbol, 'r': round(_ror, 4)})
                                obj_lst[symbol]['d'] = datetime.datetime.now().strftime('%Y%m%d')
                                obj_lst[symbol]['s'] = sel_cnt + 1

                                if bool_01_end:
                                    obj_lst.pop(symbol, None)
                            
                            elif (sel_cnt == 2) and (t2 <= los_dif) and psb_ord_00:

                                bool_02_end = False
                                if psb_ord_02:
                                    qty = ord_qty_02
                                else:
                                    qty = bal_qty
                                    bool_02_end = True

                                self.pu.sell_market_order(symbol, qty)
                                _ror = ror(bal_fst * qty, cur_prc * qty)
                                print(f'Sell - Symbol: {symbol}, Profit: {round(_ror, 4)}')
                                sel_lst.append({'c': '[S2] ' + symbol, 'r': round(_ror, 4)})
                                obj_lst[symbol]['d'] = datetime.datetime.now().strftime('%Y%m%d')
                                obj_lst[symbol]['s'] = sel_cnt + 1

                                if bool_02_end:
                                    obj_lst.pop(symbol, None)

                            elif (sel_cnt == 3) and (t3 <= los_dif) and psb_ord_00:

                                self.pu.sell_market_order(symbol, bal_qty)
                                _ror = ror(bal_fst * bal_qty, cur_prc * bal_qty)
                                print(f'Sell - Symbol: {symbol}, Profit: {round(_ror, 4)}')
                                sel_lst.append({'c': '[S3] ' + symbol, 'r': round(_ror, 4)})
                                obj_lst[symbol]['d'] = datetime.datetime.now().strftime('%Y%m%d')
                                obj_lst[symbol]['s'] = sel_cnt + 1

                                obj_lst.pop(symbol, None)

                        elif (hp <= bal_pft) and psb_ord_00:

                            self.pu.sell_market_order(symbol, bal_qty)
                            _ror = ror(bal_fst * bal_qty, cur_prc * bal_qty)
                            print(f'Sell - Symbol: {symbol}, Profit: {round(_ror, 4)}')
                            sel_lst.append({'c': '[S+] ' + symbol, 'r': round(_ror, 4)})
                            obj_lst.pop(symbol, None)

                        elif (bal_pft <= ct) and psb_ord_00:

                            self.pu.sell_market_order(symbol, bal_qty)
                            _ror = ror(bal_fst * bal_qty, cur_prc * bal_qty)
                            print(f'Sell - Symbol: {symbol}, Profit: {round(_ror, 4)}')
                            sel_lst.append({'c': '[S-] ' + symbol, 'r': round(_ror, 4)})
                            obj_lst.pop(symbol, None)

            # if i % 8 == 0:
            #     time.sleep(0.4)
            # i = i + 1

        save_file(FILE_URL_BLNC_3M, obj_lst)

        sel_txt = ''
        for sl in sel_lst:
            sel_txt = sel_txt + '\n' + str(sl['c']) + ' : ' + str(sl['r'])

        __tn = datetime.datetime.now()
        __tn_div = __tn.minute % 30
        self.time_backtest = threading.Timer(1800 - (60 * __tn_div) - __tn.second, self.stock_order)
        self.time_backtest.start()
        line_message(f'BotUpbit \n시작 : {_tn}, \n금액 : {int(self.tot_evl_price)}원, \n종료 : {__tn}, {sel_txt}')
        
        
    def get_balance_code_list(self, obj=False):
        bal_lst = self.pu.get_balances()
        o = {}
        l = []
        if len(bal_lst) > 0:
            for i in bal_lst:
                if i['unit_currency'] + '-' + i['currency'] != 'KRW-KRW':
                    l.append(i['unit_currency'] + '-' + i['currency'])
                o[i['unit_currency'] + '-' + i['currency']] = {
                    'a': float(i['avg_buy_price']),
                    'b': float(i['balance']),
                    't': float(i['balance']) * float(i['avg_buy_price']) if (i['unit_currency'] + '-' + i['currency']) != 'KRW-KRW' else float(i['balance'])
                }
        return o if obj else l
        
    
    def get_remain_cancel(self, l):
        for _l in l:
            rmn_lst = self.pu.get_order(_l)
            if len(rmn_lst) > 0:
                for rmn in rmn_lst:
                    self.pu.cancel_order(rmn['uuid'])


if __name__ == '__main__':

    bc = BotCoin()
    # bc.init_per_day()
    # bc.stock_order()

    while True:

        try:

            tn = datetime.datetime.now()
            tn_085825 = tn.replace(hour=8, minute=58, second=25)

            if tn >= tn_085825 and bc.bool_start == False:
                bc.init_per_day()
                bc.stock_order()
                bc.bool_start = True

        except Exception as e:

            line_message(f"BotUpbit Error : {e}")
            break

