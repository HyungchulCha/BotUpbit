import os
DIRECTORY = os.getcwd()

UB_ACCESS_KEY_NAJU = 'dGZaKiwwfCu3znS8vkOAt0J8QWnVUlZh4LXlA1vs'
UB_SECRET_KEY_NAJU = 'uzYHzPwKkyeRDsxDyDFJEcJLgJPV7eeo65hPtxSd'
UB_IP_NAJU = '58.125.138.167'

UB_ACCESS_KEY_AWS = 'DSFClZsOVLbkjL31uZdwLlsU3adyQoE9fWsuhhMN'
UB_SECRET_KEY_AWS = '3x0vv6PyRzm1wRczWqxYqdHmQRgEP0OczHijCveB'
UB_IP_AWS = '13.125.245.97'

FILE_URL = DIRECTORY + '/Data'
FILE_URL_BLNC_3M = FILE_URL + '/BalanceList_Coin.pickle'
FILE_URL_PRFT_3M = FILE_URL + '/ProfitList_Coin.pickle'
FILE_URL_BACK = DIRECTORY + '/BacktestResult'
FILE_URL_BLNC_TEST_3M = FILE_URL_BACK + '/BalanceListTest_Coin.pickle'

LINE_URL = 'https://notify-api.line.me/api/notify'
LINE_TOKEN = '48zl8RmuB0lZoPOoVmqowZzjsUE0P53JO7jfVFCyLwh'