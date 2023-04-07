import asyncio
import json
import logging
from datetime import datetime

import websockets
import yaml
from aiohttp import web

# Set up logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')

with open("config.yml", "r") as yamlfile:
    cfg = yaml.load(yamlfile, Loader=yaml.FullLoader)
    log.info("Config loaded")

# Define the currency symbols and the exchanges
SYMBOLS = cfg['SYMBOLS']
EXCHANGES = cfg['EXCHANGES']

# Define the websocket URLs for each exchange
WS_URLS = cfg['WS_URLS']

# A local dictionary to store the rates for each exchange and symbol
rates = {}
# A local dictionary to store rates which are to be returned to the client
rates_result = {}

# Define a lock to ensure thread-safety
lock = asyncio.Lock()


# Define a function to update the rates dictionary
async def update_rates_dict(symbol, rate, timestamp, exchange):
    # Acquire the lock
    async with lock:
        # Check if the symbol is already in the dictionary
        if symbol in rates:
            # If the symbol is in the dictionary, update the rate
            rates[symbol][exchange] = {'rate': rate, 'timestamp': timestamp}
        else:
            # If the symbol is not in the dictionary, add it
            rates[symbol] = {
                exchange: {
                    'rate': rate,
                    'timestamp': timestamp
                }
            }
    # Log the event - commented not to spam the console
    # log.info(f'Updated {symbol} rate from {exchange}: {rate}')


# A callback function to handle binance websocket messages
async def handle_binance_message(msg):
    # Parse the message as JSON
    data = json.loads(msg)
    # Check if the message is a trade update from binance
    if "e" in data and data["e"] == "trade":
        # Extract the symbol, price and timestamp from the message
        symbol = data["s"]
        rate = float(data["p"])
        timestamp = datetime.fromtimestamp(data['E'] / 1000)
        # Update the rates dictionary with the latest price
        await update_rates_dict(symbol, rate, timestamp, exchange='Binance')


# A callback function to handle okx websocket messages
async def handle_okx_message(msg):
    # Parse the message as JSON
    data = json.loads(msg)
    # Check if the message is a trade update from okx
    if "data" in data and data["arg"]["channel"] == "trades":
        # Extract the symbol, price and timestamp from the message
        symbol = data["data"][0]["instId"].replace("-", "")
        rate = float(data["data"][0]["px"])
        timestamp = datetime.fromtimestamp(int(data["data"][0]['ts']) / 1000)
        # Update the rates dictionary with the latest price
        await update_rates_dict(symbol, rate, timestamp, exchange='OKX')


# Define a function to start binance websocket listener
async def binance_listener():
    # Define the websocket URL
    url = WS_URLS['Binance']
    # Add the stream names to the websocket URL
    streams = [
        f'{symbol.replace("-", "").lower()}@trade' for symbol in SYMBOLS]
    url += "/" + "/".join(streams)
    # Set a maximum number of retries and a retry count
    max_retries = 10
    retry_count = 0
    # Connect to the websocket
    # Loop until the connection is successful or the maximum retries is reached
    while True: 
        try:
            async with websockets.connect(url) as ws:
                # Reset the retry count if the connection is successful
                retry_count = 0
                # Loop forever
                while True:
                    # Wait for a message from the websocket
                    msg = await ws.recv()
                    # Handle the message with the callback function
                    await handle_binance_message(msg)
        except ConnectionResetError:
            # Handle the connection reset error here
            log.error("Binance: Connection reset by peer.")
            # Increment the retry count
            retry_count += 1
            # Check if the maximum retries is reached
            if retry_count > max_retries:
                log.error("Binance: Maximum retries reached. Exiting.")
                break
            else:
                log.error(f"Binance: Retrying connection in 5 seconds. Attempt {retry_count} of {max_retries}.")
                # Wait for 5 seconds before retrying
                await asyncio.sleep(5)


# Define a function to start okx websocket listener
async def okx_listener():
    # Define the websocket URL
    url = WS_URLS['OKX']
    # Define the streams to subscribe to
    streams = [{"channel": "trades", "instId": symbol} for symbol in SYMBOLS]
    # Set a maximum number of retries and a retry count
    max_retries = 10
    retry_count = 0
    # Connect to the websocket
    # Loop until the connection is successful or the maximum retries is reached
    while True: 
        try:
            async with websockets.connect(url) as ws:
                # Send a subscribe request to join the channels
                subscribe_msg = {"op": "subscribe", "args": streams}
                await ws.send(json.dumps(subscribe_msg))
                # Loop forever
                while True:
                    # Wait for a message from the websocket
                    msg = await ws.recv()
                    # Handle the message with the callback function
                    await handle_okx_message(msg)
        except ConnectionResetError:
            # Handle the connection reset error here
            log.error("OKX: Connection reset by peer.")
            # Increment the retry count
            retry_count += 1
            # Check if the maximum retries is reached
            if retry_count > max_retries:
                log.error("OKX: Maximum retries reached. Exiting.")
                break
            else:
                log.error(f"OKX: Retrying connection in 5 seconds. Attempt {retry_count} of {max_retries}.")
                # Wait for 5 seconds before retrying
                await asyncio.sleep(5)


# Define a function to update the rates_result dictionary every 5 seconds
async def update_rates():
    # Loop indefinitely
    while True:
        await asyncio.sleep(5)
        # Get the current time
        now = datetime.now()
        # Iterate over the currency symbols
        for symbol in SYMBOLS:
            symbol = symbol.replace("-", "")
            # Iterate over the exchanges
            for exchange in EXCHANGES:
                # Get the rate and timestamp from the rates dictionary
                rate_info = rates.get(symbol, {}).get(exchange, {})
                rate = rate_info.get('rate', None)
                timestamp = rate_info.get('timestamp', None)
                time_passed = (
                    now - timestamp).total_seconds() if timestamp != None else None
                # Check if the rate is not None and if the timestamp is less than 5 seconds old
                if (rate is not None) and (time_passed is not None) and (time_passed < 5):
                    rates_result[symbol] = rates[symbol][exchange]['rate']
                    # Use this exchange rate as the final rate and break the loop
                    log.info(f'Using {exchange} rate for {symbol}: {rate}')
                    break
                else:
                    # if the rate is None or more then 5 seconds passed since the update, go to the next exchange
                    log.warning(f'No data from {exchange} for {symbol}')
        log.info(rates_result)


# Define a function to start the web app
async def web_app():
    # Create a web app
    app = web.Application()
    # Add the routes
    app.add_routes([web.get('/courses', handle_courses),
                    web.get('/{pair_name}', handle_rates)])
    # Run the web app
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 3000)
    await site.start()
    log.info('Web app started')
    # Wait until the app is stopped
    while True:
        await asyncio.sleep(3600)


# Define a callback function to handle requests for /courses
async def handle_courses(request):
    # Handle the request for /courses and return the rates as a JSON response
    log.info(f'Received request: {request}')
    # Acquire the lock and get the rates from the dictionary
    async with lock:
        response = rates_result
    log.info(f'Sent response: {response}')
    return web.json_response(response)


# Define a callback function to handle requests for /<pair_name>
async def handle_rates(request):
    # Handle the request for /<pair_name> and return the rates as a JSON response
    log.info(f'Received request: {request}')
    # Acquire the lock and get the rates from the dictionary
    async with lock:
        # get rates for the pair name from the request_result dictionary
        response = {request.match_info['pair_name']: rates_result.get(request.match_info['pair_name'].replace("-",""), None)}
    log.info(f'Sent response: {response}')
    return web.json_response(response)


# Get the current event loop
loop = asyncio.get_event_loop()
# Run both async functions using asyncio.gather() until they are complete
loop.run_until_complete(asyncio.gather(
    binance_listener(), okx_listener(), update_rates(), web_app()))