# Service for recieving currency rates

Cервис, через который можно получать курсы валютных пар с биржи. Необходимо, чтобы сервис возвращал курсы по следующим валютным парам: BTC-USDT ETH-USDT XRP-USDT 
Требования: 
- Сервис может обработать до 1500 запросов в ед. времени 
- Курсы обновляются раз в 5 секунд 
- Сервис работает отказаустойчиво (если одна из бирж перестаёт возвращать курсы, то сервис переключается на другой) 
- В сервисе необходимо реализовать логирование 
- Курсы необходимо получать из OKX и Binance (приоритет отдаётся OKX) 
- Работа с биржей происходит по websocket’ам 
- Нагрузочное тестирование реализовать через locust 

Интерфейс сервиса: 
ip:port/courses - получить курсы всех валютных пар (списком) 
ip:port/{pair_name:str} - получить курс определенной валютной пары


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