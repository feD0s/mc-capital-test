# Service for recieving cryptocurrency rates

A service through which you can receive rates for cryptocurrency pairs from the exchange. The service returns rates for the following pairs: BTC-USDT ETH-USDT XRP-USDT

## Requirements:

 - The service can process up to 1500 requests per second
 - Rates are updated every 5 seconds
 - The service is fail-safe (if one of the exchanges stops returning rates, the service switches to another)
 - Logging is implemented
 - Rates are gathered from OKX and Binance (priority given to OKX)
 - Websockets are used to communicate with the exchanges
 - Stress testing is implemented (locust)

 - Service interface:
     -  ip:port/courses - get the rates of all currency pairs
     -  ip:port/{pair_name:str} - get the rate of a certain currency pair


## Getting Started

### Prerequisites

To run the service, you must first install docker
```
pip install docker
```

### Installing and running

1. git clone https://github.com/feD0s/mc-capital-test.git
2. cd mc-capital-test
3. docker build -t rates_service .
4. docker run -p 3000:3000 rates_service
5. open http://localhost:3000/courses in browser

## Running the tests

locust must be installed
```
pip install locust
```

In separate terminal window:
1. cd mc-capital-test
2. type "locust" in terminal
3. open http://localhost:8089/ in browser
4. example: set number of users: 100 and spawn rate: 10, host: http://localhost:3000/, start swarming

## Screenshots
![Alt text](stress_testing.jpg?raw=true "Stress testing")