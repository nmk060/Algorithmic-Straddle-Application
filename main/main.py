
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta, TH
from kiteconnect import KiteConnect

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Initialize KiteConnect API
kite = KiteConnect(api_key='YOUR_API_KEY')
kite.set_access_token('YOUR_ACCESS_TOKEN')

# Get current market price of a given trading symbol
def getCMP(tradingSymbol):
    quote = kite.quote(tradingSymbol)
    if quote:
        return quote[tradingSymbol]['last_price']
    else:
        return 0

# Get the tradingsymbol of a Bank Nifty option for a given expiry, strike, and option type
def get_symbol(expiry, strike, option_type):
    instruments = kite.instruments('NFO')
    symbols = [instrument['tradingsymbol'] for instrument in instruments if
               instrument['expiry'] == expiry and
               instrument['strike'] == strike and
               instrument['instrument_type'] == 'CE' and
               instrument['name'] == 'BANKNIFTY']
    if option_type == 'CE':
        return symbols[0]
    else:
        return symbols[1]

# Place an order for a given trading symbol, quantity, price, and transaction type (BUY or SELL)
def place_order(tradingSymbol, quantity, price, transaction_type):
    try:
        order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=kite.EXCHANGE_NFO,
            tradingsymbol=tradingSymbol,
            transaction_type=transaction_type,
            quantity=quantity,
            price=price,
            product=kite.PRODUCT_MIS,
            order_type=kite.ORDER_TYPE_LIMIT)
        logging.info('Order placed successfully, order_id = %s', order_id)
        return order_id
    except Exception as e:
        logging.error('Order placement failed: %s', e.message)

# Calculate 20% stop loss for a given price
def calculate_stop_loss(price):
    return round(price * 0.2)

# Get the current time
now = datetime.now().strftime('%H:%M:%S')

# Check if it is before the trade execution time of 9:20 AM
if now < '09:20:00':
    logging.info('Waiting for trade execution time of 9:20 AM...')
    while now < '09:20:00':
        now = datetime.now().strftime('%H:%M:%S')

from time import sleep

if name == 'main':
    # Find ATM Strike of Bank Nifty
    atm_strike = round(getCMP('NSE:BANKNIFTY'), -100)

    next_thursday_expiry = datetime.today() + relativedelta(weekday=TH(1))

    symbol_ce = get_symbols(next_thursday_expiry.date(), 'BANKNIFTY', atm_strike, 'CE')
    symbol_pe = get_symbols(next_thursday_expiry.date(), 'BANKNIFTY', atm_strike, 'PE')

    ce_price = getCMP(symbol_ce)
    pe_price = getCMP(symbol_pe)

    # Calculate the total margin required for the trade
    margin_required = (ce_price + pe_price) * lot_size * margin_multiplier

    # Check if there is sufficient balance to place the trade
    balance = kite.margins()['available']['cash']
    if balance < margin_required:
        logging.info('Insufficient balance to place the trade')
        exit()

    # Place the straddle order
    ce_order_id = place_order(symbol_ce, ce_price, lot_size, kite.TRANSACTION_TYPE_SELL, KiteConnect.EXCHANGE_NFO,
                              KiteConnect.PRODUCT_MIS, KiteConnect.ORDER_TYPE_LIMIT)
    pe_order_id = place_order(symbol_pe, pe_price, lot_size, kite.TRANSACTION_TYPE_SELL, KiteConnect.EXCHANGE_NFO,
                              KiteConnect.PRODUCT_MIS, KiteConnect.ORDER_TYPE_LIMIT)

    logging.info('Straddle order placed successfully, order ids = %s, %s', ce_order_id, pe_order_id)

    # Set stoploss orders for each leg
    ce_stoploss_price = round(ce_price * 1.2, 2)
    pe_stoploss_price = round(pe_price * 1.2, 2)


ce_stoploss_order_id = place_order(symbol_ce, ce_stoploss_price, lot_size, kite.TRANSACTION_TYPE_BUY,
                                       KiteConnect.EXCHANGE_NFO, KiteConnect.PRODUCT_MIS,
                                       KiteConnect.ORDER_TYPE_SLM)
    pe_stoploss_order_id = place_order(symbol_pe, pe_stoploss_price, lot_size, kite.TRANSACTION_TYPE_BUY,
                                       KiteConnect.EXCHANGE_NFO, KiteConnect.PRODUCT_MIS,
                                       KiteConnect.ORDER_TYPE_SLM)

    logging.info('Stoploss orders placed successfully, order ids = %s, %s', ce_stoploss_order_id, pe_stoploss_order_id)

    # Wait for the market to close
    sleep(3900)

    # Cancel the stoploss orders
    kite.cancel_order(variety=kite.VARIETY_REGULAR, order_id=ce_stoploss_order_id)
    kite.cancel_order(variety=kite.VARIETY_REGULAR, order_id=pe_stoploss_order_id)

    logging.info('Stoploss orders cancelled successfully')
