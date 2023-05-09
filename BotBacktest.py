from BotConfig import *
from BotUtil import *
import pandas as pd
import numpy as np
import pyupbit
import os
import datetime
import copy
import time

'''
방금전봉보다 5프로 이하
5봉전부터 과거 20봉간 최고최저폭 10~20%이상
이평선 정배열 5 > 20 > 60
지금종가가 20이평 100~105% 사이인지
지금종가가 5이평 위에 있냐
'''

dir = os.getcwd()
# flist = os.listdir(dir + '/BacktestData')
# xlsx_list = np.array([x for x in flist if x.endswith('.xlsx')])

ttl_code_array = []
ttl_buy_array = []
ttl_sel_array = []
ttl_sucs_per_array = []
ttl_fail_per_array = []
ttl_prft_array = []

obj = {}
bal_obj = {}

if os.path.isfile(FILE_URL_BLNC_TEST_3M):
    os.remove(FILE_URL_BLNC_TEST_3M)
    print('Delete!!!')

tk_list = pyupbit.get_tickers("KRW")

tt = 0
for code in tk_list:

    temp_df = gen_neck_df(pyupbit.get_ohlcv(code, interval='minute60', count=2880))
    
    if not temp_df is None:

        buy_p = 0
        buy_c = 0
        sucs_c = 0
        fail_c = 0
        item_buy_c = 0
        item_sel_c = 0
        _ror = 1

        has_buy = False
        fst_lop = False
        bal_obj[code] = {'p': 0, 'q': 0, 'a': 0, 'pft': 1}

        if os.path.isfile(FILE_URL_BLNC_TEST_3M):
            obj = load_file(FILE_URL_BLNC_TEST_3M)
            print('Loaded!!!')
        else:
            obj = {}
            save_file(FILE_URL_BLNC_TEST_3M, obj)
            print(obj)
            print('Saved!!!')

        for i, row in temp_df.iterrows():
            
            cls_val = row['close']
            clp_val = row['close_prev']
            hgt_val = row['height_5_20']
            m05_val = row['ma05']
            m20_val = row['ma20']
            m60_val = row['ma60']

            # buy
            if \
            (1.1 < hgt_val < 15) and \
            (m60_val < m20_val < m05_val < cls_val < clp_val * 1.05) and \
            (m20_val < cls_val < m20_val * 1.05) and \
            has_buy == False \
            :
                bal_obj[code]['q'] = 10
                bal_obj[code]['a'] = int(cls_val)
                has_buy = True
                item_buy_c += 1
                print('buy', bal_obj[code]['a'])
                obj[code] = {'a': int(cls_val), 'max': int(cls_val), 'sel': 1}

            bal_obj[code]['pft'] = (cls_val / bal_obj[code]['a']) if bal_obj[code]['a'] != 0 else 1

            # sell
            t1 = 0.035
            t2 = 0.045
            t3 = 0.055
            ct = 0.8
            hp = 100
            
            if has_buy == True:

                if obj[code]['max'] < cls_val:
                    obj[code]['max'] = cls_val

                if obj[code]['max'] > cls_val:
                    
                    bal_fst = copy.deepcopy(bal_obj[code]['a'])
                    bal_qty = copy.deepcopy(bal_obj[code]['q'])
                    bal_pft = copy.deepcopy(bal_obj[code]['pft'])
                    obj_max = copy.deepcopy(obj[code]['max'])
                    obj_fst = copy.deepcopy(obj[code]['a'])
                    sel_cnt = copy.deepcopy(obj[code]['sel'])
                    obj_pft = obj_max / obj_fst
                    los_dif = obj_pft - bal_pft
                    ord_rto_01 = 0.2
                    ord_rto_02 = (3/8)
                    ord_qty_01 = bal_qty * ord_rto_01
                    ord_qty_02 = bal_qty * ord_rto_02
                    sam_qty_01 = (bal_qty == ord_qty_01)
                    sam_qty_02 = (bal_qty == ord_qty_02)

                    if 1 < bal_pft < hp:

                        if sel_cnt == 1 and t1 <= los_dif:

                            _ror = ror(bal_fst * ord_qty_01, cls_val * ord_qty_01, _ror)
                            bal_obj[code]['q'] = bal_qty - ord_qty_01
                            obj[code]['sel'] = sel_cnt + 1
                            print(f'1차매도 : {_ror}')

                            if cls_val - bal_fst > 0:
                                sucs_c += 1
                            else:
                                fail_c += 1
                            item_sel_c += 1

                        elif sel_cnt == 2 and t2 <= los_dif:

                            _ror = ror(bal_fst * ord_qty_02, cls_val * ord_qty_02, _ror)
                            bal_obj[code]['q'] = bal_qty - ord_qty_02
                            obj[code]['sel'] = sel_cnt + 1
                            print(f'2차매도 : {_ror}')

                            if cls_val - bal_fst > 0:
                                sucs_c += 1
                            else:
                                fail_c += 1
                            item_sel_c += 1
                            
                        elif sel_cnt == 3 and t3 <= los_dif:

                            _ror = ror(bal_fst * bal_qty, cls_val * bal_qty, _ror)
                            print(f'3차매도 : {_ror}')

                            if cls_val - bal_fst > 0:
                                sucs_c += 1
                            else:
                                fail_c += 1
                            item_sel_c += 1

                            has_buy = False
                            obj.pop(code, None)

                    elif hp <= bal_pft:
                        _ror = ror(bal_fst * bal_qty, cls_val * bal_qty, _ror)
                        print(f'익절 : {_ror}')

                        if cls_val - bal_fst > 0:
                            sucs_c += 1
                        else:
                            fail_c += 1
                        item_sel_c += 1

                        buy_c = 0
                        has_buy = False
                        obj.pop(code, None)

                    # 손절
                    elif bal_pft <= ct:
                        _ror = ror(bal_fst * bal_qty, cls_val * bal_qty, _ror)
                        print(f'손절 : {_ror}')

                        if cls_val - bal_fst > 0:
                            sucs_c += 1
                        else:
                            fail_c += 1
                        item_sel_c += 1

                        has_buy = False
                        obj.pop(code, None)

        if sucs_c != 0:
            sucs_per = round(((sucs_c * 100) / (sucs_c + fail_c)), 2)
            fail_per = round((100 - sucs_per), 2)
            prft_per = round(((_ror - 1) * 100), 2)
        else:
            sucs_per = 0
            if item_buy_c > 0:
                fail_per = round((100 - sucs_per), 2)
                prft_per = round(((_ror - 1) * 100), 2)
            else:
                fail_per = 0
                prft_per = 0

        ttl_code_array.append(code)
        ttl_buy_array.append(item_buy_c)
        ttl_sel_array.append(item_sel_c)
        ttl_sucs_per_array.append(sucs_per)
        ttl_fail_per_array.append(fail_per)
        ttl_prft_array.append(prft_per)

        print('종목:{}, 매수: {}회, 매도: {}회, 성공률 : {}%, 실패율 : {}%, 누적수익률 : {}%'.format(code, item_buy_c, item_sel_c, sucs_per, fail_per, prft_per))

        save_file(FILE_URL_BLNC_TEST_3M, obj)

    if tt % 10 == 0:
        time.sleep(0.4)
    tt = tt + 1
    
prft_df = pd.DataFrame({'code': ttl_code_array, 'buy': ttl_buy_array, 'sell': ttl_sel_array, 'success': ttl_sucs_per_array, 'fail': ttl_fail_per_array, 'profit': ttl_prft_array})
prft_df = prft_df.sort_values('profit', ascending=False)
prft_df.to_excel(dir + '/BacktestResult/BotCoinSwing' + datetime.datetime.now().strftime('%m%d%H%M%S') + '.xlsx')