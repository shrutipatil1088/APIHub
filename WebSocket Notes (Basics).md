\# 📘 WebSocket Notes (Basics)



\---



\# 1. What is WebSocket?



\*\*Definition:\*\*



WebSocket is a \*\*communication protocol\*\* that provides a \*\*persistent, full-duplex connection\*\* between a client and a server.



\*\*Key Points:\*\*



\* It is a \*\*protocol\*\*, not a library.

\* It allows \*\*real-time communication\*\*.

\* The connection stays open until one side closes it.

\* Both client and server can send messages at any time.



\---



\# 2. Why WebSocket?



HTTP follows the \*\*Request → Response\*\* model.



```text

Browser ----Request----> Server

Browser <---Response---- Server



Connection Closed

```



For real-time features (chat, notifications), HTTP requires polling, which wastes resources.



WebSocket solves this by keeping one connection open.



```text

Browser <===================> Server

```



\---



\# 3. HTTP vs WebSocket



| HTTP                        | WebSocket                            |

| --------------------------- | ------------------------------------ |

| Request-Response            | Full-Duplex Communication            |

| Connection closes           | Connection remains open              |

| Client starts communication | Client and server both send messages |

| Stateless                   | Stateful (connection stays alive)    |

| Best for normal web pages   | Best for real-time applications      |



\---



\# 4. What is a Protocol?



A protocol is a \*\*set of rules\*\* that defines how two systems communicate.



Examples:



\* HTTP

\* HTTPS

\* WebSocket

\* FTP

\* SMTP



\---



\# 5. Is WebSocket a Library?



\*\*No.\*\*



WebSocket is a \*\*protocol\*\*.



Different programming languages use different libraries to implement it.



Examples:



Python:



\* Django Channels

\* websockets

\* aiohttp



Node.js:



\* ws

\* Socket.IO (adds extra features on top of WebSockets)



\---



\# 6. Internet Communication Layers



```text

Application Layer

\----------------------

HTTP

WebSocket

FTP



\----------------------

TCP



\----------------------

IP



\----------------------

Ethernet / Wi-Fi

```



WebSocket works on top of \*\*TCP\*\*.



\---



\# 7. What is TCP?



TCP (Transmission Control Protocol) is responsible for:



\* Reliable communication

\* Correct order of data

\* Retransmitting lost packets

\* Error checking



WebSocket depends on TCP for reliable transport.



\---



\# 8. Client and Server



\### Client



A client requests a service.



Examples:



\* Chrome

\* Firefox

\* Mobile App



\### Server



A server provides a service.



Examples:



\* Django

\* Node.js

\* FastAPI



Example:



```text

Browser (Client)

&#x20;      │

&#x20;      ▼

Django (Server)

```



\---



\# 9. During Development



When running:



```bash

python manage.py runserver

```



\* Django application acts as the \*\*server\*\*.

\* Browser acts as the \*\*client\*\*.



The browser sends HTTP requests to:



```text

http://127.0.0.1:8000

```



\---



\# 10. What is 127.0.0.1?



`127.0.0.1` is the \*\*localhost (loopback) IP address\*\*.



It always refers to \*\*your own computer\*\*.



\---



\# 11. What is Port 8000?



A port identifies a specific service running on a computer.



Example:



```text

127.0.0.1:8000



127.0.0.1  → Computer

8000       → Django Server

```



\---



\# 12. Can the Server Send Data Without a Request?



\### HTTP



❌ No



The server must wait for a client request.



\### WebSocket



✅ Yes



After the WebSocket connection is established, the server can send messages whenever needed.



\---



\# 13. What is Django Channels?



Django Channels extends Django to support \*\*long-lived protocols\*\* like WebSockets.



Without Channels:



```text

Browser

&#x20;   │

&#x20;HTTP

&#x20;   │

Django

```



With Channels:



```text

Browser

&#x20;   │

WebSocket

&#x20;   │

Django Channels

&#x20;   │

Django Application

```



\---



\# 14. What is a WebSocket Handshake?



A WebSocket handshake is the process of upgrading a normal HTTP connection into a WebSocket connection.



Steps:



1\. Browser sends HTTP Upgrade request.

2\. Server validates the request.

3\. Server responds with \*\*101 Switching Protocols\*\*.

4\. Connection becomes WebSocket.



\---



\# 15. Important Handshake Headers



Browser sends:



```http

Upgrade: websocket

Connection: Upgrade

Sec-WebSocket-Key

Sec-WebSocket-Version

```



Server replies:



```http

101 Switching Protocols

Upgrade: websocket

Connection: Upgrade

Sec-WebSocket-Accept

```



\---



\# 16. What is HTTP Status 101?



```http

101 Switching Protocols

```



Meaning:



> Server accepted the upgrade request and switched from HTTP to the WebSocket protocol.



\---



\# 17. What is a WebSocket Frame?



After the handshake:



HTTP is no longer used.



Messages travel as \*\*WebSocket frames\*\*.



```text

Client



↓



Frame



↓



Server

```



\---



\# 18. WebSocket Lifecycle



```text

Connect



↓



Handshake



↓



Accept



↓



Receive



↓



Send



↓



Ping / Pong



↓



Disconnect

```



\---



\# 19. Connect



Browser starts the connection.



JavaScript:



```javascript

new WebSocket("ws://127.0.0.1:8000/ws/chat/");

```



Django Channels:



```python

async def connect(self):

&#x20;   await self.accept()

```



\---



\# 20. accept()



```python

await self.accept()

```



Accepts the WebSocket connection.



Without `accept()`, the connection is rejected.



\---



\# 21. Receive



When the browser sends data:



```javascript

socket.send("Hello");

```



Django receives it:



```python

async def receive(self, text\_data):

```



\---



\# 22. Send



Server sends data back:



```python

await self.send(text\_data="Hello")

```



Browser receives it:



```javascript

socket.onmessage = function(event){

&#x20;   console.log(event.data)

}

```



\---



\# 23. Ping / Pong



Used to check whether the connection is still alive.



```text

Server → Ping



Client → Pong

```



Usually handled automatically by the WebSocket implementation or ASGI server.



\---



\# 24. Disconnect



When the connection closes:



Browser:



```javascript

socket.close()

```



Django:



```python

async def disconnect(self, close\_code):

```



\---



\# 25. Browser WebSocket API



\### Methods



```javascript

new WebSocket()



socket.send()



socket.close()

```



\### Events



```javascript

onopen



onmessage



onclose



onerror

```



\---



\# 26. Django Channels Methods



```python

connect()



receive()



send()



disconnect()

```



\---



\# 27. Browser ↔ Django Mapping



| Browser           | Django Channels       | Purpose                |

| ----------------- | --------------------- | ---------------------- |

| `new WebSocket()` | `connect()`           | Create connection      |

| `onopen`          | `await self.accept()` | Connection established |

| `socket.send()`   | `receive()`           | Client → Server        |

| `self.send()`     | `onmessage`           | Server → Client        |

| `socket.close()`  | `disconnect()`        | Close connection       |



\---



\# 28. Common Uses of WebSocket



\* 💬 Chat applications

\* 🔔 Live notifications

\* 📈 Stock market updates

\* 💹 Cryptocurrency prices

\* 🎮 Multiplayer games

\* 📍 Live GPS tracking

\* 📊 Real-time dashboards

\* ✍️ Collaborative editing



\---



\# 29. Key Takeaways



\* WebSocket is a \*\*protocol\*\*, not a library.

\* It provides \*\*persistent, full-duplex communication\*\*.

\* It starts with an \*\*HTTP handshake\*\*.

\* After the handshake, communication uses \*\*WebSocket frames\*\*.

\* Both client and server can send messages at any time.

\* Django supports WebSockets through \*\*Django Channels\*\*.

\* The main lifecycle is: \*\*Connect → Accept → Receive → Send → Disconnect\*\*.

\* WebSocket is ideal for \*\*real-time applications\*\*.













1. **Daphne**

\- Daphne is an ASGI server. 

\- Every HTTP request and every WebSocket connection first reaches Daphne.

\-ASGI server.

\-Accepts both HTTP and WebSocket connections.

\-Entry point for incoming requests.





**2. Channels**

\- Channels is a Django package.

\-Extends Django to support WebSockets.

\-Introduces Consumers, Groups, and Channel Layers.



Django (traditional WSGI) does not support WebSockets directly because it is designed for HTTP request-response communication. Django Channels extends Django to add WebSocket support using ASGI.



One-line note:

Django (WSGI) → HTTP only.

Django + Channels (ASGI) → HTTP + WebSockets.



Simple flow:

Browser

&#x20;   │

HTTP ─────────────► Django Views



WebSocket ───────► Django Channels → Consumers



So, Channels acts as the bridge that allows Django to communicate using the WebSocket protocol.





**3. Redis**

Redis acts as the message broker.

With Redis:



Server 1



↓



Redis



↓



Server 2



Redis allows all Django processes to exchange messages.







**4. ASGI\_APPLICATION**

\-Points to the main ASGI application (config.asgi.application).

\-Daphne starts execution from this application.



**5.CHANNEL\_LAYERS**

\-Messaging layer used by Django Channels.

\-Allows Consumers and other parts of Django to communicate.



**6.RedisChannelLayer**

\-Stores and routes messages through Redis.

\-Supports multiple Django processes and servers.

\-Recommended for production.



**7.InMemoryChannelLayer**

\-Stores channel and group messages in the current Python process memory.

\-Fast and simple.

\-Best for testing or single-process development.

\-Not suitable for production.





✅ A browser always starts a WebSocket connection with an **HTTP handshake**.

✅ After the server replies with 101 Switching Protocols, the connection becomes a WebSocket.

✅ After that, communication uses WebSocket frames, not HTTP requests/responses.





* settings.py → Configures Channels.
* asgi.py → Receives WebSocket connections.
* routing.py → Finds the correct Consumer.
* consumers.py → Actually handles the WebSocket connection.





| HTTP           | WebSocket                |

| -------------- | ------------------------ |

| View           | Consumer                 |

| `request`      | `scope`                  |

| `HttpResponse` | `send()` / `send\_json()` |







**AsyncJsonWebsocketConsumer?**



It is a base class provided by Django Channels.



It already knows how to:



Accept WebSocket connections

Close connections

Send JSON

Receive JSON

Access the channel layer



Base class for JSON-based asynchronous WebSocket consumers.

Provides methods like accept(), close(), send\_json(), and access to the channel layer.



**connect()**

Runs when a new WebSocket connection reaches the consumer.

Used to authenticate the user, join groups, and accept or reject the connection.



**self.scope**

Similar to Django's request.

Contains connection information such as user, headers, path, cookies, and more.



**group\_add(**)

Adds the current WebSocket connection (channel\_name) to a named group.



**self.channel\_name**

A unique identifier automatically generated for each WebSocket connection.



**accept()**

Accepts the WebSocket connection and completes the handshake.



**disconnect()**

Runs when the WebSocket connection closes.

Typically used to remove the connection from groups.



**group\_discard()**

Removes the current WebSocket connection from a group.



**group\_send()**

Sends an event to every connection in a group.



**Event Handler Methods**

Methods like admin\_dashboard\_update() are automatically called when group\_send() sends an event whose "type" matches the method name.





**.as\_asgi()** → Converts the Consumer into an ASGI application so Django Channels can run it.







**-- Overall WebSocket Flow (Your Project)**



Browser

&#x20;  │

&#x20;  ▼

1\. new WebSocket("ws://127.0.0.1:8000/ws/dashboard/")

&#x20;  │

&#x20;  ▼

2\. HTTP Handshake (Upgrade Request)

&#x20;  │

&#x20;  ▼

3\. Daphne receives the request

&#x20;  │

&#x20;  ▼

4\. config/asgi.py

&#x20;     ├── ProtocolTypeRouter

&#x20;     ├── AuthMiddlewareStack

&#x20;     └── URLRouter

&#x20;  │

&#x20;  ▼

5\. apps/dashboard/routing.py

&#x20;     "/ws/dashboard/"

&#x20;     │

&#x20;     ▼

&#x20;     DashboardConsumer.as\_asgi()

&#x20;  │

&#x20;  ▼

6\. DashboardConsumer.connect()

&#x20;     ├── Check authentication

&#x20;     ├── Join group

&#x20;     └── accept()

&#x20;  │

══════════════════════════════

&#x20;WebSocket Connection Open

══════════════════════════════

&#x20;  │

&#x20;  ▼

7\. User performs some action

&#x20;  (API call, create project, subscription, etc.)

&#x20;  │

&#x20;  ▼

8\. Database changes

&#x20;  │

&#x20;  ▼

9\. Django Signal fires

&#x20;  │

&#x20;  ▼

10\. DashboardWebSocketService

&#x20;     ├── Get latest dashboard data

&#x20;     └── group\_send()

&#x20;  │

&#x20;  ▼

11\. Channel Layer

&#x20;     (Redis/InMemory)

&#x20;  │

&#x20;  ▼

12\. DashboardConsumer

&#x20;     admin\_dashboard\_update()

&#x20;  │

&#x20;  ▼

13\. send\_json()

&#x20;  │

&#x20;  ▼

14\. Browser receives updated data

&#x20;     (No page refresh)

```



\---



\# Each File's Responsibility



\## 1️⃣ `settings.py`



\*\*Purpose:\*\*



Configures the Channel Layer.



```python

CHANNEL\_LAYERS = {...}

```



✔️ Tells Channels whether to use:



\* Redis

\* InMemory



\---



\## 2️⃣ `config/asgi.py`



\*\*Purpose:\*\*



Entry point for HTTP and WebSocket.



It decides:



```text

HTTP

&#x20;  ↓

Django Views



WebSocket

&#x20;  ↓

Consumers

```



\---



\## 3️⃣ `config/routing.py`



\*\*Purpose:\*\*



Collects WebSocket routes from all apps.



Similar to:



```text

config/urls.py

```



but for WebSockets.



\---



\## 4️⃣ `dashboard/routing.py`



\*\*Purpose:\*\*



Maps WebSocket URL to Consumer.



```text

/ws/dashboard/



↓



DashboardConsumer

```



\---



\## 5️⃣ `DashboardConsumer`



\*\*Purpose:\*\*



Handles WebSocket connection.



Main methods:



```python

connect()

```



→ User connected



```python

disconnect()

```



→ User disconnected



```python

admin\_dashboard\_update()

```



→ Receives message from Channel Layer



```python

send\_json()

```



→ Sends data to browser



\---



\## 6️⃣ `DashboardService`



\*\*Purpose:\*\*



Calculates dashboard data from the database.



It \*\*doesn't know anything about WebSockets\*\*.



\---



\## 7️⃣ `DashboardWebSocketService`



\*\*Purpose:\*\*



Broadcasts data to connected clients.



Flow:



```text

Get latest dashboard data



↓



group\_send()



↓



Channel Layer

```



\---



\## 8️⃣ Signals



Example:



```python

post\_save

```



Purpose:



Automatically detect database changes.



Example:



```text

UsageLog created



↓



Signal fires



↓



DashboardWebSocketService

```



\---



\## 9️⃣ Channel Layer



Purpose:



Acts as the messenger.



```text

DashboardWebSocketService



↓



Redis/InMemory



↓



DashboardConsumer

```



\---



\## 🔟 Browser



Receives:



```javascript

socket.onmessage

```



Dashboard updates instantly.



No refresh needed.



\---



\# One-Line Summary for Each File



| File                        | Responsibility                                                          |

| --------------------------- | ----------------------------------------------------------------------- |

| `settings.py`               | Configure Channel Layer (Redis/InMemory).                               |

| `asgi.py`                   | Entry point; routes HTTP and WebSocket requests.                        |

| `config/routing.py`         | Combines all WebSocket routes.                                          |

| `dashboard/routing.py`      | Maps `/ws/dashboard/` to `DashboardConsumer`.                           |

| `DashboardConsumer`         | Handles WebSocket connect, disconnect, and sending data to the browser. |

| `DashboardService`          | Calculates dashboard statistics.                                        |

| `DashboardWebSocketService` | Sends dashboard updates to Channel Layer using `group\_send()`.          |

| `signals.py`                | Detects database changes and triggers WebSocket broadcasts.             |

| `Channel Layer`             | Delivers messages from services to Consumers.                           |

| `Browser`                   | Receives updates instantly through WebSocket.                           |



\---



\# The One Sentence You Should Remember ⭐



> \*\*Browser opens a WebSocket → `asgi.py` routes it to `DashboardConsumer` → Consumer joins a group → Database changes trigger a Signal → Signal calls `DashboardWebSocketService` → Service sends a message through the Channel Layer → Consumer receives it and sends JSON to the browser → Dashboard updates instantly without refreshing.\*\*



This single sentence describes your entire WebSocket architecture from start to finish.





