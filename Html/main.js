let days = document.getElementById("days");
let hours = document.getElementById("hours");
let minutes = document.getElementById("minutes");
let seconds = document.getElementById("seconds");

let interval = document.getElementById("timeToRestart");


let views = document.getElementById('views')
let videos = document.getElementById('videos')

function timeNotTwoDigits(number) {
    if (number < 10 && number >= 0) {
        return "0" + number;
    }
    if  (number < 0&&  number > -10) {
        return "-0" + Math.abs(number);
    }
    
    return number;
}

const HEARTBEAT_INTERVAL = 1000; // Интервал heartbeat в миллисекундах
const HEARTBEAT_VALUE = 1;     // Значение heartbeat-сообщения
const RECONNECT_INTERVAL = 1000; // Интервал переподключения в миллисекундах
let WS_URL = "ws://localhost:8001";

let afterQ = document.location.href.split('?=')[1]
if (afterQ){
    WS_URL = "ws://" + afterQ 
}


class WebSocketClient {
    constructor(url, reconnectInterval, heartbeatInterval) {
        this.url = url;
        this.reconnectInterval = reconnectInterval;
        this.heartbeatInterval = heartbeatInterval;
        this.websocket = null;
        this.isConnecting = false;
        this.heartbeatTimer = null;
        this.connect();
    }

    connect() {
        if (this.isConnecting) {
            console.log("Подключение уже в процессе.");
            return;
        }
        this.isConnecting = true;
        console.log("Попытка подключения к:", this.url);
        this.websocket = new WebSocket(this.url);

        this.websocket.onopen = () => {
            console.log("Соединение WebSocket открыто");
            this.isConnecting = false;
            this.startHeartbeat();
            this.onOpen();
        };

        this.websocket.onmessage = (event) => {
            this.onMessage(event);
        };

        this.websocket.onclose = (event) => {
            console.log("Соединение WebSocket закрыто:", event.code, event.reason);
            this.isConnecting = false;
            this.stopHeartbeat();
            this.onClose(event);
            if (event.code !== 1000) {
                this.reconnect();
            }
        };

        this.websocket.onerror = (error) => {
            console.error("Ошибка WebSocket:", error);
            this.isConnecting = false;
            this.stopHeartbeat();
            this.onError(error);
            this.reconnect();
        };
    }

    startHeartbeat() {
        if (this.heartbeatInterval <= 0) return
        this.heartbeatTimer = setInterval(() => {
          if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                this.websocket.send(HEARTBEAT_VALUE);
            } else {
                console.log("Не удалось отправить heartbeat, соединение не установлено");
                this.stopHeartbeat();
            }
        }, this.heartbeatInterval);
    }

    stopHeartbeat() {
        clearInterval(this.heartbeatTimer);
    }


    reconnect() {
        console.log(`Попытка переподключения через ${this.reconnectInterval / 1000} секунд.`);
        setTimeout(() => {
            this.connect();
        }, this.reconnectInterval);
    }

    send(data) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(data);
        } else {
            console.log("Соединение WebSocket не установлено, сообщение не отправлено:", data)
        }
    }

    onOpen() {
        console.log("Соединение открыто!");
    }

    onMessage(event) {
        try {
             let data = JSON.parse(event.data);
             console.log(data)
             views.innerHTML = data.data.views
             videos.innerHTML = data.data.videos
            //  this.setTimerFromWSData(data.data.time);
            //  this.setReloadTimeFromWSData(data.data.timerToRestart);
            //  this.setTextUpdating(data.data.isUpdating);
            
             
        } catch (e) {
            console.log("Получено некорректное сообщение", event.data)
        }
    }

    onClose(event) {
        console.log("Соединение закрыто.", event)
    }

    onError(error) {
        console.log("Произошла ошибка:", error)
    }

    // setTimerFromWSData(data) {
    //     let time = data;
    //     let days_ = Math.floor(time / (60 * 60 * 24));
    //     let hours_ = Math.floor(time / (60 * 60)) % 24;
    //     let minutes_ = Math.floor(time / 60) % 60;
    //     let seconds_ = time % 60;
    //     days.innerHTML = timeNotTwoDigits(days_);
    //     hours.innerHTML = timeNotTwoDigits(hours_);
    //     minutes.innerHTML = timeNotTwoDigits(minutes_);
    //     seconds.innerHTML = timeNotTwoDigits(seconds_);
    // }
    setReloadTimeFromWSData(data) {
        let time = data;
        interval.innerHTML = `Обновление через - ${time} секунд`;
    }
    setTextUpdating(data) {
        if (data) {
           
            interval.innerHTML = "Обновление данных...";
        } 
    }
}


const client = new WebSocketClient(WS_URL, RECONNECT_INTERVAL, HEARTBEAT_INTERVAL);