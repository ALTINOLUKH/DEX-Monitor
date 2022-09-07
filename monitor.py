import json
import math
import requests
import threading
from time import sleep
from urllib.parse import urlencode

session = requests.Session()
tokens = {
    'eth': {'address': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', 'decimals': 18}, # WETH
    'btc': {'address': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599', 'decimals': 8},
    'ftt': {'address': '0x50D1c9771902476076eCFc8B2A83Ad6b9355a4c9', 'decimals': 18},  # FTX Token
    'aave': {'address': '0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9', 'decimals': 18},
    'link': {'address': '0x514910771AF9Ca656af840dff83E8264EcF986CA', 'decimals': 18}, # ChainLink    
    
    'usdt': {'address': '0xdAC17F958D2ee523a2206206994597C13D831ec7', 'decimals': 6},  # Stable
    'usdc': {'address': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', 'decimals': 6},  # Stable
}

dexes = {
    'uniswap': 'Uniswap_V3',
    'sushiswap': 'SushiSwap'
}

prices = {k:{} for k in dexes.keys()}

def getDexPrice(dex, op, token_pair, amount):
    #    global session

    buyToken = token_pair.split('_')[0]
    sellToken = token_pair.split('_')[1]

    query = {
        'buyToken': tokens.get(buyToken).get('address'),
        'sellToken': tokens.get(sellToken).get('address'),
        'includedSources': dex
    }

    if op == 'buy':
        decimals = tokens.get(buyToken).get('decimals')
        amount = amount * (10**decimals)
        query.update({'buyAmount': amount})
    elif op == 'sell':
        decimals = tokens.get(sellToken).get('decimals')
        amount = amount * (10**decimals)
        query.update({'sellAmount': amount})

    url = f"https://api.0x.org/swap/v1/price?{urlencode(query)}"
    while True:
        if 'session' in globals():
            r = session.get(url)
        else:
            r = requests.get(url)
        if r.status_code == 200:
            break

    r_json = json.loads(r.text)
    #print(json.dumps(r_json, indent=4, sort_keys=True))
    return r_json['price']


def updatePrices(dex, op, token_pair, amount):
    price = getDexPrice(dexes.get(dex), op, token_pair, amount)
    prices.get(dex).update({token_pair:price})

# Create a list of given token combinations (not permutations)
def generateTokenPairs(token_names):
    token_pairs = []
    for token in token_names:
        other_tokens = (name for name in token_names if name != token)
        # Listenin güncellenen bir yapı olmasının sebebi element eklenirken hâlihazırda (tersi) var mı diye bakılmasıdır.
        token_pairs = token_pairs + [f"{token}_{name}" for name in other_tokens if f"{name}_{token}" not in (pair for pair in token_pairs)]
    return token_pairs

token_pairs = generateTokenPairs(tokens.keys())

# Create threads
threads = {f"{dex[0]}_{pair}":f"threading.Thread(target=updatePrices, args=('{dex}', 'buy', '{pair}', 1))" for pair in token_pairs for dex in dexes.keys()}

def runThreads():
    while True:
        for thread_name, thread in threads.items():
            exec(f"{thread_name} = {thread}")
            eval(thread_name).start()
        # for thread_name in threads.keys():
        #     eval(thread_name).join()
        sleep(.1)

run_threads_thread = threading.Thread(target=runThreads)
run_threads_thread.start()

while not (len(prices.get('uniswap')) == len(prices.get('sushiswap')) == math.comb(len(tokens.keys()), 2)):
    pass

while True:
    print(json.dumps(prices, sort_keys=True, indent=4))
    sleep(5)
