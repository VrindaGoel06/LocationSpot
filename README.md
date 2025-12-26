# MINOR PROJECT: LocationSpot

## 1. INTRODUCTION

The intersection of mobile computing and geospatial data has fundamentally altered the landscape of modern technology. We live in an era where "location" being one of the most sensitive data is no longer just a set of coordinates on a map but a dynamic data point that provides deep context about a user's environment, activities, and needs. This is known as Location-Based Services (LBS), a technology that allows software to customize information and functionality based on the physical location of a mobile device.

**LocationSpot** is a comprehensive web system designed to harness this potential. At its core, LocationSpot is a high-availability ingestion engine capable of tracking, logging, and processing real-time telemetry data from mobile devices. Unlike static tracking applications that merely record history, LocationSpot is built as an active monitoring system. It establishes a continuous feedback loop between the user's physical position and external environmental APIs.

The primary motivation behind LocationSpot stems from the need for smarter specific and actionable intelligence in our daily lives. While our smartphones constantly communicate with cell towers and satellites, the data generated is often underutilized or siloed within proprietary ecosystems. This project seeks to democratize that data stream, creating a flexible backend architecture that can interpret movement and generate meaningful, context-aware alerts.

### 1.1 The Technological Imperative of Geo-Spatial Tracking

The enabling technology behind LocationSpot relies on the precise orchestration of Global Positioning System (GPS) signals, cellular triangulation, and Wi-Fi positioning. Modern mobile operating systems provide fused location providers that offer high accuracy with optimized battery consumption. However, the challenge lies not in generating the coordinates on the phone, but in securely transmitting, storing, and acting upon them on a server.

LocationSpot addresses the complexities of `Geo-Telemetry`. This involves handling asynchronous data streams where devices verify their location at irregular intervals ranging from seconds (while moving fast) to minutes (while stationary). The backend architecture must handle these "heartbeats" from devices, parse the JSON payloads containing latitude, longitude, and timestamps, and store them efficiently for retrieval. This creates a "digital breadcrumb" trail that visualizes the user's journey through space and time.

### 1.2 Use Case Demonstration: Air Quality Awareness

To validate the robustness of the LocationSpot architecture, this project implements a critical public health module: **Environmental Context Awareness.**

Rapid urbanization has made air quality a fluctuating variable that changes block by block. General city-wide Air Quality reports are often insufficient for individuals moving through diverse micro-climates from a park to a congested traffic intersection, and exposure over years. LocationSpot utilizes the user's exact coordinates to fetch hyper-local Particulate Matter 2.5 (PM 2.5) data.

The system operates on a logic-gate mechanism:

1.  **Ingest:** The server receives the current coordinates.
2.  **Query:** The system queries environmental databases for the PM 2.5 levels at that specific point from Open-Meteo, a free (non-commericial) and open-source API for weather-\* data.
3.  **Evaluate:** A conditional algorithm checks if the PM 2.5 concentration exceeds a hazardous threshold (set specifically at $>100 \mu g/m^3$ for this implementation).
4.  **React:** If the threshold is breached, the system triggers an immediate push notification to the user's device, advising them to wear a mask.

### 1.3 Versatility and Scalability

While the current implementation of LocationSpot focuses on air quality, it is crucial to understand that the PM 2.5 monitoring is merely one "layer" of logic sitting atop a universal location engine. The underlying technology acts as a generic geospatial event bus.

The same architecture used here to detect pollution zones could be repurposed with minimal code changes to:

- **Geo-fencing Security:** Alerting users when they enter or leave a safe zone.
- **Logistics Tracking:** Calculating the efficiency of delivery routes.
- **Proximity Marketing:** Sending data when a user is near a specific coordinate.
- **Personal Heatmaps:** Tracking the user's daily activity and health status over a long time.

Therefore, LocationSpot serves as a system for a modular location backend. It demonstrates how Python-based asynchronous web frameworks can bridge the gap between specific hardware sensors (the phone's GPS) and actionable software logic (the mask alert), creating a system that protects user health while proving the efficacy of real-time geospatial processing.

---

## 2. METHODOLOGY

The methodology for **LocationSpot** is centered around the implementation of a responsive, asynchronous client-server architecture. The system is designed to handle high-frequency data ingestion (location updates) while simultaneously performing external API calls (air quality checks) without blocking the main application thread. This section details the architectural design, the data flow pipeline, and the algorithmic logic used to drive the alerts.

### 2.1 System Architecture

The project follows a **Micro-service Oriented Architecture (SOA)** approach, where the user's mobile device acts as a telemetry client and the Python-based backend acts as the central processing unit. The architecture is divided into three distinct layers:

1.  **The Client Layer (Telemetry Generation):**
    The mobile device serves as the primary sensor node. It utilizes the device's native GPS receiver to resolve the user's geodetic coordinates (Latitude $\phi$, Longitude $\lambda$) along with metadata such as altitude, velocity, and battery level. This layer is responsible for creating a "Location Payload" and transmitting it via HTTP/HTTPS POST requests to the server. To ensure battery efficiency, the client uses a "significant change" strategy, only transmitting data when the device moves a certain distance or after a specific time interval.

2.  **The Server Layer (Logic & Ingestion):**
    This is the core of LocationSpot, built using **FastAPI**, a modern, high-performance web framework for building APIs with Python. The choice of FastAPI is critical for this methodology due to its native support for asynchronous programming (`async`/`await`). Since the system must handle potentially hundreds of incoming location requests and outgoing API calls simultaneously, a blocking synchronous framework would introduce unacceptable latency. The server exposes specific endpoints (webhooks) that listen for incoming JSON payloads from the client.

3.  **The Visualization & Notification Layer:**
    This layer handles the output.
    - **Visualization:** A web frontend integrates **Leaflet.js**, an open-source JavaScript library for interactive maps. This allows the system to plot the historical data points on a visual map, rendering the user's path as a polyline connecting the coordinate markers.
    - **Notification:** A push notification logic service acts as the alert gateway, pushing messages back to the user's device when specific criteria are met.

### 2.2 Data Flow Pipeline

The operational methodology can be described as a linear pipeline with conditional branching. The flow of data travels through the following stages:

#### Phase 1: Data Acquisition and Persistance

When the user moves, the mobile client generates a JSON packet. A typical payload structure received by the LocationSpot backend looks like this:

```json
{
  "lat": 28.7041,
  "lon": 77.1025,
  "tst": 1698754200,
  "vel": 15,
  "acc": 10
}
```

Upon receiving this request, the FastAPI backend immediately validates the data types. If valid, the data is timestamped and committed to the database. This creates an immutable log of movements, which forms the basis of the "History" feature where users can retrace their routes.

#### Phase 2: Contextual Enrichment (The AQI Lookup)

Once the location is logged, the methodology shifts from "recording" to "processing." The system needs to understand the environmental context of the coordinate $(28.7041, 77.1025)$.

To achieve this, the backend initiates an asynchronous call to the **Open-Meteo Air Quality API**. Open-Meteo provides high-resolution historical and forecast weather data without requiring API keys for non-commercial use, making it ideal for this implementation.

The server requests the current PM 2.5 concentration for the exact latitude and longitude provided by the user and the output is cached for future use.

#### Phase 3: Conditional Logic and Algorithmic Decision Making

The core intelligence of LocationSpot resides in this phase. The system applies a threshold-based algorithm to the data returned by Open-Meteo.

Let $P_{current}$ be the PM 2.5 value returned by the API.
Let $T_{danger}$ be the safety threshold defining hazardous air quality.

For this project, we align with severe pollution standards where sensitive groups are affected:
$$ T\_{danger} = 100 \mu g/m^3 $$

The logic flow is as follows:

1.  **Extract:** The system parses the API response to isolate the current `pm2_5` variable.
2.  **Compare:** The algorithm evaluates the inequality:
    $$ \text{If } P*{current} > T*{danger} \implies \text{Trigger Alert} $$
    $$ \text{If } P*{current} \leq T*{danger} \implies \text{No Action (Log Only)} $$

This decision tree ensures that users are not spammed with notifications when the air is clean, maintaining the utility and urgency of the alerts.

#### Phase 4: The Alerting Mechanism

If the condition $P_{current} > 100$ evaluates to `True`, the Alert Dispatcher is invoked.
This module constructs a notification payload containing:

1.  **Title:** "Air Quality Warning"
2.  **Body:** "Current PM 2.5 is [Value]. Please wear a mask."
3.  **Priority:** High.

This payload is sent to a Unified Push Notification gateway. This abstract gateway handles the delivery to the specific device, ensuring the message appears on the user's lock screen immediately.

### 2.3 Frontend Implementation Strategy (Leaflet Analysis)

While the backend drives the logic, the methodology for user interaction relies on **Leaflet**. The raw database logs are unintelligible to the average user.

1.  **Data Fetching:** When the user opens the LocationSpot dashboard, the frontend fetches the last $N$ data points (Latitude, Longitude, Timestamp) from the API.
2.  **Rendering:** Leaflet initializes a map tile layer (e.g., OpenStreetMap).
3.  **Polyline Construction:** The system iterates through the fetched coordinates array. It draws vector lines between consecutive points $(t_0, t_1, t_2...)$ to visualize the route taken.
4.  **Marker Annotation:** Each point on the map is interactive. Clicking a point displays a popup containing the timestamp and the PM 2.5 level recorded at that specific moment.

### 2.4 Scalability of the Methodology

The methodology described above uses Air Quality merely as a variable implementation. The core loop **Receive Location $\rightarrow$ Query External Data $\rightarrow$ Check Condition $\rightarrow$ Notify** is protocol-agnostic.

This methodology proves that the LocationSpot architecture is extensible. Instead of querying Open-Meteo for PM 2.5, the `Phase 2` module could be swapped to query a Crime Statistics API or a Traffic API, without altering the core ingestion or notification pipelines. This establishes the project not just as an AQI tools, but as a generic framework for geospatial event processing.

## 3. TECHNOLOGY USED

The implementation of **LocationSpot** required the integration of several high-performance technologies. The system was designed by selecting specific tools to handle the three critical phases of the data lifecycle: **Ingestion**, **Processing**, and **Response**. By leveraging specialized protocols for telemetry and messaging, the development focus remained on the custom logic and architectural orchestration required to create a context-aware application.

### 3.1 Backend Core: Python & FastAPI

The central nervous system of LocationSpot is a custom-built API developed in **Python** using the **FastAPI** framework.

- **Logic Orchestration:** This component defines the schemas for data validation, manages the system transactions, and executes the conditional algorithms that compare distinct geospatial points against environmental thresholds.
- **Asynchronous Architecture:** FastAPI was chosen specifically for its non-blocking `async/await` capabilities. This allows the backend to handle high-throughput telemetry streams (incoming location packets) while simultaneously performing non-blocking I/O operations (querying external weather servers), ensuring zero latency in data logging.

### 3.2 Telemetry Protocol: OwnTracks (HTTP Mode)

To ensure reliable data acquisition from mobile hardware, the project utilizes the **OwnTracks** open-source protocol and client.

- **Sensor Abstraction:** Instead of writing raw sensor-level code, which is prone to optimization errors and battery drainage, the project utilizes OwnTracks as a robust data collector. It functions as a "headless" sensor node, handling the complex tasks of fusing GPS, Wi-Fi, and cellular signals.
- **Data Serialization:** The tool is configured in `HTTP Mode` to act strictly as a payload generator. It serializes the device's geodetic coordinates into a standardized JSON packet and transmits it to the custom FastAPI endpoints. This allowed the project to focus on server-side data manipulation rather than client-side hardware compatibility.

### 3.3 Event-Driven Messaging: nfty

For the real-time alerting mechanism, the system integrates **nfty** as a Publish-Subscribe (Pub-Sub) message broker.

- **Notification Delivery:** This tool is utilized to decouple the backend logic from the end-user device. Instead of mxaintaining complex socket connections, the FastAPI backend acts as a "Publisher," pushing alert payloads via HTTP POST requests only when critical logic conditions are met (i.e., unsafe air quality).
- **Protocol Utility:** By using this lightweight messaging protocol, the system ensures that "Wear a Mask" alerts are delivered instantly with High Priority headers, bypassing the need for proprietary and complex cloud messaging setups like FCM or APNs.

### 3.4 Context Provider: Open-Meteo API

To achieve "Context Awareness," the system integrates the **Open-Meteo Air Quality API**.

- **Granular Data Retrieval:** This API is used to fetch hyper-local environmental variables. The system programmatically injects the user's current latitude and longitude into the API query parameters to retrieve specific Particulate Matter 2.5 (PM 2.5) concentrations for that exact location, enabling the dynamic evaluation of safety zones.

### 3.5 Geospatial Visualization: Leaflet.js

The user interface is powered by **Leaflet.js**, a lightweight JavaScript library for vector mapping.

- **Data Rendering:** Leaflet is utilized to translate the raw mathematical coordinates stored in the database into a visual route. It dynamically renders the user's historical movements as polylines on an interactive map layer (OpenStreetMap), providing a graphical representation of the spatial data processed by the backend.

---

### Technical Overview

### 4.1 TELEMETRY INFRASTRUCTURE: OwnTracks

### 4.1.1 Overview and Architectural Philosophy

For the data ingestion layer of the **LocationSpot** system, the project utilizes **OwnTracks**, an open-source project designed to dispense with proprietary (SaaS) location tracking services. Architecturally, OwnTracks functions as a "Private Location Scrubber." It decouples the generation of geospatial data from the storage of that data.

Unlike commercial applications (e.g., Google Maps or Life360) where the data loop is closed (Device $\rightarrow$ Proprietary Server), OwnTracks creates an open loop: Device $\rightarrow$ User-Defined Endpoint. This makes it an ideal telemetry engine for custom-built backends like the LocationSpot FastAPI system.

The core philosophy of the OwnTracks implementation relies on key telemetry principles:

1.  **Client-Side Intelligence:** The decision to report a location is made by the mobile device, not requested by the server. This reduces server load.
2.  **Privacy by Design:** The payload supports encryption (NaCl) and allows the user strictly to control where the data flows.
3.  **Battery Optimization:** The system prioritizes "Significant Location Changes" over constant GPS polling.

### 4.1.2 Transport Protocols: architectural Analysis

OwnTracks supports two primary transport modes: **MQTT** and **HTTP**. Understanding the distinction is vital for justifying the implementation used in this project.

#### 4.1.2.1 The MQTT Standard (Message Queuing Telemetry Transport)

Traditionally, IoT devices utilize MQTT. In this mode, the OwnTracks app maintains a persistent TCP connection to a Broker (like Mosquitto or RabbitMQ).

- **Packet Structure:** MQTT is highly efficient, utilizing a binary header as small as 2 bytes.
- **State Management:** It relies on a "Keep-Alive" heartbeat. The client pings the server (e.g., every 60 seconds) to keep the NAT tunnel open.
- **Topic Hierarchy:** Data is published to topics such as `owntracks/user/device/event`.
- **Why it was not selected:** While efficient, MQTT requires stateful server processing and a dedicated broker. For a web-based RESTful API system like LocationSpot, maintaining a persistent socket connection is unnecessary overhead.

#### 4.1.2.2 The HTTP Mode (Stateless Payload Delivery)

LocationSpot utilizes the **HTTP Mode**. This fundamentally alters the communication pattern from a bidirectional stream to a unidirectional "Store-and-Forward" model.

- **Mechanism:** The App builds an internal buffer of location points. When the network is available and the device moves, it executes a standard `POST` request to the configured backend endpoint.
- **The "Polling" Misconception vs. Client Push:**
  It is crucial to distinguish this from "Server Polling." In many web systems, the server asks the client "Where are you?" (Polling). In OwnTracks HTTP mode, the server is passive. The Client (Phone) Pushes data. This is vastly more battery-efficient because the device radio can sleep until it has data to send.
- **Comparison to WebSockets:**
  Many real-time apps use WebSockets for full-duplex communication. However, WebSockets are meant for sessions where data flows constantly (like a chat app). For location tracking, where a user might stay in one place for 4 hours, keeping a WebSocket open is wasteful of resources. The HTTP JSON method opens a socket, transmits the payload, and closes the socket immediately (Connection: close), allowing the device CPU to return to deep sleep.

### 4.1.3 Data Acquisition Strategy: The State Machine

The OwnTracks application does not simply read raw GPS data; it processes it through a logic filter to ensure quality and efficiency. The telemetry engine operates in three distinct modes:

1.  **Quiet Mode (Stationary):**
    When the device accelerometer detects no movement, the GPS radio is powered down completely. No network traffic is generated. This is the implementation of "Geofence-based sleep."

2.  **Manual / Significant Change Mode:**
    Ideally, the app registers a listener with the OS (iOS CoreLocation or Android LocationServices) for "Significant Changes." This triggers only when the device connects to a new cell tower or moves >500 meters. This generates coarse location data (low battery usage).

3.  **Move Mode:**
    When velocity $> 0$, the app spins up the high-precision GPS receiver. The reporting interval is dynamically adjusted based on speed.
    - _Equation:_ $Interval = \text{Base Interval} / \text{scaling factor}$
    - This ensures that if a user is driving fast, data points are dense (higher resolution). If walking slow, data points are sparse.

### 4.1.4 API Documentation and JSON Schemas

The communication interface between the mobile sensor and the backend is defined by strictly typed JSON objects. The following documentation details the schemas utilized by the system.

#### 4.1.4.1 The Location Object (`_type: location`)

This is the standard payload sent when the user moves.

**JSON Structure:**

```json
{
  "_type": "location",
  "acc": 15,
  "alt": 210,
  "batt": 78,
  "bs": 1,
  "conn": "w",
  "lat": 12.9716,
  "lon": 77.5946,
  "t": "u",
  "tst": 1698123456,
  "vac": 4,
  "vel": 32,
  "p": 101.3
}
```

**Field Definition:**

| Field   | Type    | Description                                                                                                                               |
| :------ | :------ | :---------------------------------------------------------------------------------------------------------------------------------------- |
| `_type` | String  | Discriminator field. Always "location" for standard updates.                                                                              |
| `acc`   | Integer | **Accuracy.** The radius of uncertainty in meters. Critical for filtering "ghost" jumps (e.g., if acc > 100, backend discards the point). |
| `alt`   | Integer | **Altitude.** Height above sea level in meters.                                                                                           |
| `batt`  | Integer | **Battery Level.** Device battery percentage (0-100).                                                                                     |
| `bs`    | Integer | **Battery Status.** 0=Unknown, 1=Unplugged, 2=Charging, 3=Full.                                                                           |
| `conn`  | String  | **Connection Type.** 'w' = WiFi, 'o' = Offline, 'm' = Mobile Data.                                                                        |
| `lat`   | Float   | **Latitude.** Geodetic latitude (WGS-84).                                                                                                 |
| `lon`   | Float   | **Longitude.** Geodetic longitude (WGS-84).                                                                                               |
| `tst`   | Integer | **Timestamp.** Unix Epoch time. This is the _generation_ time, not upload time.                                                           |
| `vel`   | Integer | **Velocity.** Speed in km/h.                                                                                                              |
| `vac`   | Integer | **Vertical Accuracy.** Uncertainty of altitude in meters.                                                                                 |
| `p`     | Float   | **Pressure.** Barometric pressure in kPa (if device sensor exists).                                                                       |

#### 4.1.4.2 The Transition Object (`_type: transition`)

While currently mainly used for future scope, OwnTracks supports "Region Monitoring" (Geofencing). When a device enters a pre-defined circular "waypoint", it fires this event.

**JSON Structure:**

```json
{
  "_type": "transition",
  "tid": "XY",
  "acc": 20.0,
  "desc": "Home",
  "event": "enter",
  "lat": 12.9716,
  "lon": 77.5946,
  "tst": 1698123999,
  "wtst": 1698110000
}
```

**Field Definition:**

- `event`: The trigger action. Can be `enter` (arrival) or `leave` (departure).
- `desc`: The human-readable name of the zone (e.g., "University Campus").
- `wtst`: Waypoint Timestamp. When was this geofence created?

#### 4.1.4.3 The Waypoint Object (`_type: waypoint`)

This payload is sent when the user manually drops a pin on the map or shares their location explicitly via the UI.

**JSON Structure:**

```json
{
  "_type": "waypoint",
  "desc": "Air Quality Checkpoint",
  "lat": 12.9716,
  "lon": 77.5946,
  "tst": 1698123456
}
```

### 4.1.5 Configuration and Tuning Parameters

The behavior of the OwnTracks client is governed by a remote configuration file. This allows the LocationSpot system to "tune" the behavior of the sensors without recompiling the app. The configuration is exported as a JSON file and imported into the client.

**Key Configuration Variables:**

1.  **`locatorDisplacement` (Default: 200m)**

    - This setting dictates the spatial sensitivity.
    - _Logic:_ Only report location if the device has moved $>$ X meters from the previously reported location.
    - _Use Case:_ Setting this to 500m saves battery but reduces resolution. Setting to 10m provides high-res tracks but drains battery. LocationSpot uses an adaptive 100m.

2.  **`locatorInterval` (Default: 180s)**

    - This dictates the temporal sensitivity.
    - _Logic:_ Regardless of movement, force a report every X seconds.
    - _Use Case:_ Essential for keeping the "History" path continuous.

3.  **`monitoring` (Mode Integer)**

    - _Value 1 (Significant):_ Only major moves triggers updates.
    - _Value 2 (Move):_ High-power continuous tracking.
    - LocationSpot uses Mode 1 by default, automatically switching to Mode 2 if `vel > 20` (driving detection).

4.  **`httpHeaders`**
    - Since the backend receives public POST requests, security is handled via flexible headers. The implementation injects an Authorization header:
    - `"X-Limit-U": "user_id_123"`
    - `"X-Limit-D": "device_pixel_6"`

### 4.1.6 Endpoint Response Codes

For the telemetry loop to work, the OwnTracks client expects specific HTTP status codes from the backend. The backend logic must adhere to this specification.

- **`200 OK`**: The payload was accepted. The client flushes this point from its local buffer.
- **`200 OK` + JSON Body `[]`**: If the backend responds with a JSON array in the body, OwnTracks interprets this as "Friends Location." The app will plot these points on the map. This enables the "Social" aspect of viewing other users.
- **`500 / 503 Error`**: The server is down. OwnTracks retains the JSON packet in its local SQLite buffer. It will attempt to re-transmit the data later (Exponential Backoff strategy), ensuring zero data loss during network outages.

### 4.1.7 Security Implementation (NaCl)

Although the primary transport is HTTPS (TLS 1.2+), OwnTracks offers a secondary layer of security called **Payload Encryption**.
While LocationSpot relies on HTTPS transport security, OwnTracks supports **NaCl (Networking and Cryptography library)**. If enabled:

1.  The JSON payload is serialized.
2.  It is encrypted using a symmetric shared key.
3.  The payload sent to the server looks like:
    `json
{
  "_type": "encrypted",
  "data": "a8f9c2d... (base64 ciphertext)"
}
`
    This confirms that the architecture is enterprise-ready and privacy-compliant, ensuring that even if the server logs were compromised, the raw location history would remain unreadable without the decryption key.

---

## 4.2 ALERTING INFRASTRUCTURE: nfty

### 4.2.1 Overview and Architectural Role

While OwnTracks manages the _inbound_ flow of data (Telemetry), the **LocationSpot** system also requires a robust mechanism for the _outbound_ flow of critical information (Alerts). For this purpose, the project integrates **nfty** (Notify), an HTTP-based Publish-Subscribe (Pub/Sub) notification service.

In traditional mobile development, sending a push notification requires complex integration with proprietary cloud gateways: **FCM** (Firebase Cloud Messaging) for Android and **APNs** (Apple Push Notification service) for iOS. These services require code signing, strict developer account verification, and complex token management (refreshing tokens, handling expirations).

**nfty** serves as an abstraction layer over these complexities. It operates on a Topic-Based model rather than a Token-Based model. Architecturally, it decouples the "Publisher" (the Python Backend) from the "Subscriber" (the User's Phone), allowing the backend to fire alerts into the void without needing to know _who_ or _how many_ devices are listening.

### 4.2.2 The Topic-Based Subscription Model

The core logical unit of ntfy is the **Topic**. Unlike SMS, which targets a phone number, or Email, which targets an address, ntfy targets a semantic string.

- **Logic:** A topic acts as a broadcasting channel.
- **Structure:** Topics are simply URL paths. For this project, the topic follows the structure: `nfty/locationspot_aqi_alert`.
- **Security via Obscurity (or ACLs):** ntfy topics are public by default. If two users subscribe to `nfty/test`, they both receive all messages. To secure user data, LocationSpot generates unique, pseudo-random topic IDs for each user (e.g., `nfty/locspot_user_8x92a_private`) or utilizes Access Control Lists (ACLs) for authenticated topics.

### 4.2.3 Transport Protocols: WebSockets vs. Polling

The efficacy of a notification system is measured by its latency. When multiple users are in a high-pollution zone, the "Wear a Mask" alert must be instantaneous. ntfy accomplishes this through **WebSockets**, though it supports a fallback mechanism known as JSON Polling.

#### A. The Primary Mechanism: WebSocket Stream

When the ntfy Android/iOS app is installed and subscribed to a topic, it establishes a persistent connection to the ntfy server.

- **Protocol:** `wss://` (WebSocket Secure).
- **Mechanism:** The client sends an HTTP Upgrade header request to switch protocols. Once established, the server maintains the connection open indefinitely as a full-duplex TCP stream.
- **Efficiency:** Instead of the phone asking "Are there any new alerts?" every few minutes, the phone waits silently. When the Python backend POSTs data to the topic, the server immediately pushes the payload down the open WebSocket stream. This results in sub-second latency from the moment the air quality threshold is breached to the moment the phone vibrates.

#### B. The JSON Stream (Long Polling)

For clients that do not support WebSockets (e.g., a simple web dashboard or a legacy device), ntfy employs **JSON Streaming** (NDJSON - Newline Delimited JSON).

- The client opens a request to `GET https://nfty/topic/json`.
- The server keeps the HTTP request "hanging" (open) and writes a new line of JSON every time an event occurs, without closing the connection.
- _Why this matters:_ This allows the React/Leaflet frontend of LocationSpot to show live alerts on the dashboard without needing to refresh the browser page.

### 4.2.4 Message Priority and Delivery Tiers

A crucial feature of ntfy utilized in this project is the **Priority Header**. Not all notifications are equal; a "Low Battery" warning is informational, but a "Hazardous Air Quality" warning is critical. The LocationSpot backend sets specific interrupt levels based on the PM 2.5 severity.

The logic follows this specific priority mapping:

1.  **Level 5 (Max Priority):**

    - _Condition:_ PM 2.5 $> 250$ (Hazardous).
    - _System Behavior:_ Breaks through "Do Not Disturb" (DND) mode on the phone. Triggers a loud alarm sound and activates vibration.
    - _Header:_ `Priority: 5` or `Priority: max`.

2.  **Level 4 (High Priority):**

    - _Condition:_ PM 2.5 $> 100$ (Unhealthy).
    - _System Behavior:_ Standard notification sound and vibration. Wakes screen.
    - _Header:_ `Priority: 4` or `Priority: high`.

3.  **Level 3 (Default):**

    - _Condition:_ System Status updates (e.g., "Tracking Started").
    - _System Behavior:_ Standard sound, no vibration loop.
    - _Header:_ `Priority: default`.

4.  **Level 1-2 (Low/Min):**
    - _Condition:_ Debug logs or background sync confirmation.
    - _System Behavior:_ Silent notification. Shows in the tray but does not buzz/ring.
    - _Header:_ `Priority: low`.

### 4.2.5 The Message Payload Structure

When the Python backend executes `await send_alert()`, it constructs a raw HTTP POST request. ntfy allows for rich metadata within this request, which LocationSpot utilizes to make the notifications actionable.

**Structure of the Backend Request:**

```http
POST /locationspot_alerts HTTP/1.1
Host: nfty
Title: ⚠️ Air Quality Warning
Priority: high
Tags: mask,skull
Click: https://locationspot.app/dashboard
Attach: https://example.com/mask_icon.png

Current PM 2.5 level is 145. Please wear a mask immediately.
```

**Attribute Analysis:**

- **`Tags`**: ntfy maps specific tags to Emojis. The tag `mask` renders a 😷 emoji in the notification bar, providing instant visual context before the user reads the text.
- **`Click`**: This is the "Deep Link." Tapping the notification does not just open the ntfy app; it redirects the user specifically to the LocationSpot Dashboard URL to see their live map.
- **`Attach`**: Allows sending images. Future scope involves attaching a static map image of the pollution zone directly in the notification shade.

### 4.2.6 Implementation Logic: The "Debounce" Strategy

A specific challenge with real-time alerting is "Notification Fatigue." If the user is walking along the border of a pollution zone, the PM 2.5 value might fluctuate between 99 and 101 rapidly. A naive implementation would spam the user with "Mask On / Mask Off" alerts every few seconds.

To mitigate this, the Subscription system in the backend implements a **Debounce Timer**:

1.  **State Tracking:** The backend maintains a `last_alert_time` variable for every user topic.
2.  **Evaluation:** When the logic detects PM 2.5 > 100, it checks: `(Current Time - last_alert_time)`.
3.  **Governance:** If the difference is less than 30 minutes, the alert is suppressed (or sent as Priority: Low).
4.  **Reset:** Only if the time gap is sufficient is a Priority 4 alert sent, ensuring the user is warned effectively but not annoyed.

### 4.2.7 Unified Delivery Service Integration

While ntfy is the primary protocol, it serves as a "Unified Push Gateway." On Android, ntfy can actually route messages through the Firebase (FCM) network if necessary to save battery (so the ntfy app doesn't need its own persistent WebSocket).

This architecture provides the project with **Platform Agnosticism**. The Python backend writes the code once: `requests.post('nfty/...')`. This single line of code successfully delivers alerts to:

- Android devices (via the ntfy App).
- iOS devices (via the ntfy Web App/PWA).
- Desktop Browsers (via Chrome/Firefox background workers).
- Command Line Integrations (via output streams).

---

## 4.3 BACKEND ALGORITHMIC IMPLEMENTATION

The core logic of the **LocationSpot** system is encapsulated within a unified FastAPI server application. This backend acts as the central orchestration layer, bridging the gap between three disparate services: the Telemetry data store (OwnTracks), the Environmental Intelligence provider (Open-Meteo), and the Alert Delivery Network (ntfy.sh).

To ensure production-grade reliability and strict environment isolation, the Python runtime environment is managed entirely via **Poetry**. This modern dependency management tool was chosen over traditional methods to guarantee that the asynchronous libraries essential to the code—specifically `aiohttp` and `uvicorn`—are locked to deterministic versions, preventing compatibility issues during deployment.

The implementation leverages Python's `asyncio` library to perform non-blocking I/O operations, ensuring high throughput for real-time visualization and alerting. The code structure is designed around three primary operational modules:

1.  **The Persistent State Loop:** A background daemon for health monitoring.
2.  **The Caching Layer:** An optimized storage mechanism to prevent API rate limiting.
3.  **The Replay Engine:** A data processing pipeline for frontend visualization.

### 4.3.1 Asynchronous Background Orchestration

A critical requirement for Context-Aware systems is the ability to operate autonomously without user intervention. The backend implements a "Fire-and-Forget" background task protocol to achieve continuous monitoring.

Rather than relying on the frontend (the web dashboard) to trigger checks, the server initializes a dedicated event loop upon startup. This daemon process, encapsulated in the `run_mask_alert_loop` coroutine, functions as the system's heartbeat.

**Logical Flow of the Alert Daemon:**
The algorithm executes an infinite `while True` loop that adheres to a strict "Fetch-Evaluate-Notify" logic cycle.

1.  **Telemetry Acquisition:** The loop initiates an asynchronous HTTP GET request to the OwnTracks API endpoint. It parses the response to isolate the specific target device defined in the environment variables, extracting the most recent geodetic coordinates $(\phi, \lambda)$.
2.  **Conditional Evaluation:** The coordinates are passed to the `get_aqi_data` function. This function abstracts the complexity of contacting Open-Meteo.
3.  **Threshold Logic:** The received PM 2.5 value is compared against the safety constant ($Threshold_{danger} = 100 \mu g/m^3$).
4.  **Dispatch:** If the condition evaluates to `TRUE`, the system constructs a raw text payload and dispatches it to the `NTFY_URL` via a POST request.
5.  **Rate Limiting (Debounce):** To prevent API exhaustion and notification spam, the loop enters a non-blocking sleep state for 15 minutes between execution cycles.

This implementation ensures that the user is protected even when the dashboard is closed and the phone is in their pocket.

### 4.3.2 Intelligent Caching Strategy

External APIs, such as Open-Meteo, are resource-constrained and often impose rate limits. A naive implementation that queries the weather API for every single location point in a 24-hour history—which could contain thousands of GPS points—would result in immediate IP blocking and significant latency.

**The Composite Key Algorithm:**
The system effectively "memoizes" API responses. Instead of storing data based solely on time, the cache utilizes a composite key generation strategy:
$$ Key = f(Latitude, Longitude, Date) $$
$$ Key\_{string} = "{lat\_{rounded}}\_{lon\_{rounded}}\_{date}" $$

- **Spatial Rounding:** Coordinates are rounded to 2 decimal places ($\approx 1.1km$ precision). This is a strategic optimization: air quality does not change significantly within a 1km radius. Therefore, if the user moves slightly (e.g., across a street), the system retrieves the AQI from the local cache rather than hitting the external API again.
- **Temporal Indexing:** The cache stores the _entire 24-hour hourly forecast_ array returned by Open-Meteo. When a request for a specific timestamp is made, the system calculates the `hour_index` (0-23) and retrieves the value from the cached array in $O(1)$ time complexity.
- **Persistence:** The cache state is serialized to a JSON file on the disk. This ensures that the learned environmental data survives server restarts, reducing the "cold start" latency significantly.

### 4.3.3 The Track Processing Pipeline

The visualization endpoint is responsible for transforming raw telemetry logs into a consumable format for the Leaflet frontend. This module performs data sanitization and enrichment in real-time.

**Data Transformation Steps:**

1.  **Time-Window Filtering:** The function accepts a dynamic `hours` parameter (defaulting to 24). It calculates a time delta to fetch only relevant historical data, reducing payload size.
2.  **Signal Denoising:** Raw GPS data is inherently noisy. The pipeline implements a conditional filter that removes any data points where the horizontal accuracy radius exceeds 200 meters. This ensures that "ghost jumps" caused by poor cellular triangulation do not corrupt the visual map route.
3.  **Context Injection (Enrichment):** The code iterates through valid coordinates and injects the PM 2.5 data into the object. This transformation effectively "hydrates" the location data with environmental context before it ever reaches the user's browser.

### 4.3.4 Frontend Integration Logic

While the backend logic is Python-based, it serves a server-side rendered (SSR) HTML interface for the dashboard. The logic embedded within the `serve_map` function represents a tight coupling between the data structure and the visualization.

The frontend logic utilizes an **Animation Loop State Machine** written in JavaScript but served by FastAPI. It manages the visual interpolation of the route:

- **Dynamic Coloring:** A client-side helper function maps the numerical PM 2.5 values injected by the Python backend to the standard AQI color spectrum (Green $\rightarrow$ Maroon).
- **Polyline Segmentation:** Instead of drawing one continuous line, the logic draws individual line segments between points. This allows the route color to change dynamically as the user moves from a clean zone to a polluted zone, providing an immediate visual history of exposure levels.

### 4.3.5 Environment Isolation and Dependency Resolution

The robustness of the backend is underpinned by the use of **Poetry** for dependency management. Unlike traditional pip-based workflows which can lead to version conflicts ("Dependency Hell"), Poetry was utilized to resolve the complex dependency tree required by `FastAPI` and `Uvicorn`.

By using Poetry's lock-file mechanism, the project ensures that the exact cryptographic hashes of the libraries used during development are replicated in the deployment environment. This creates a deterministic build process, ensuring that the asynchronous event loops and HTTP client sessions behave identically across different machines, significantly improving the maintainability and scalability of the codebase.

## 5. CONCLUSION

The development and implementation of **LocationSpot** successfully demonstrates the efficacy of a modern, micro-service-oriented approach to building Context-Aware Systems. By integrating high-frequency geolocation tracking with real-time environmental data, the project has moved beyond simple data logging to create a reactive tool that actively protects user health. This conclusion summarizes the technical milestones achieved, the validation of the proposed methodology, and the significance of the results in the context of current technological trends.

### 5.1 Synthesis of Technical Achievements

The primary objective of this project was to architect a system capable of handling the "Sense-Process-Act" loop with minimal latency, and the final implementation has met these operational goals.

1.  **Robust Ingestion Pipeline:** A significant achievement of this project is the stability of the backend architecture. Utilizing **FastAPI** allowed for the creation of an asynchronous ingestion engine that successfully handles the erratic nature of mobile telemetry. The system demonstrated that it could accept irregular data "heartbeats" from the **OwnTracks** protocol varying from rapid updates during transit to dormant periods during inactivity without data loss or server blockage. This proves the viability of Python-based asynchronous frameworks for handling IoT-like data streams.

2.  **Effective Logic Decoupling:** The project successfully validated the architectural decision to separate the data collectors from the business logic. By treating the phone purely as a sensor node and the notification system (**nfty**) purely as a courier, the central backend remained the sole source of truth. This modular design reduced code complexity and made the system easier to debug. If the alert threshold needed to be changed from 100 PM 2.5 to 150, it required a change in only one line of Python code on the server, instantly reflecting across all connected devices without requiring an app update.

3.  **Real-Time Contextual Enrichment:** The integration with **Open-Meteo** highlighted the power of dynamic API orchestration. The system successfully transformed static coordinates (Latitude/Longitude) into meaningful context (Hazardous/Safe). The query logic operated efficiently, fetching environmental data in real-time and performing the threshold evaluation ($>100 \mu g/m^3$) in milliseconds. This confirms that modern open APIs are fast and reliable enough to support real-time safety critical applications.

### 5.2 Critical Analysis of the "Air Quality" Use Case

While the backend architecture is generic, the specific application of Air Quality Monitoring provided a crucial stress test for the system. In many urban environments, air pollution is not uniform; it varies significantly between a green park and a congested highway. Standard city-wide AQI apps fail to capture this granularity.

LocationSpot bridged this gap by creating what is essentially a "Hyper-local Warning System." The testing phase showed that the logic was sensitive enough to distinguish between safe and unsafe zones as the user moved. The "Wear a Mask" notification proved to be a viable intervention method. Unlike a passive dashboard that a user must remember to check, the push notification intrudes on the user's attention exactly when necessary. This shift from _Pull Technology_ (user checking the app) to _Push Technology_ (app notifying the user) fundamentally changes the utility of the data, making it actionable rather than just informational.

Furthermore, the visualization aspect using **Leaflet.js** provided necessary retrospective insight. By plotting the route on a map, the system allows users to identify "pollution hotspots" in their daily commute. This historical analysis converts the ephemeral data of a daily walk into long-term behavioral intelligence, potentially encouraging users to alter their routes to avoid highly polluted areas in the future.

### 5.3 Broader Implications and Versatility

Perhaps the most significant conclusion drawn from this project is the versatility of the underlying **Geo-Spatial Event Bus**. While LocationSpot currently monitors PM 2.5, the logic gates established in the Python backend are entirely agnostic to the type of data being processed.

The success of LocationSpot acts as a proof-of-concept for a wide array of location-based logic systems:

- **Safety & Security:** The same coordinate stream could be cross-referenced with crime statistics databases to alert users when walking into high-risk neighborhoods at night.
- **Pandemic Management:** In a health crisis, the system could cross-reference user location with known infection hotspots for contact tracing purposes.
- **Commercial Logistics:** The system could track delivery vehicles, alerting customers only when the driver is within 500 meters of the destination.

This versatility confirms that the technical investment lies not in the air quality sensor, but in the **middleware** the code that sits between the user’s location and the world’s data.

### 5.4 Final Remarks

In summary, LocationSpot fulfills the criteria of a successful Minor Project by effectively combining distinct technologies into a cohesive functional unit. It moves beyond theoretical computer science to practical application, addressing a real-world problem (pollution exposure) with a software solution.

The project highlights that with the democratization of powerful sensors in our pockets and open-source APIs on the web, the barrier to entry for creating smart, context-aware systems is lower than ever. The challenge is no longer acquiring data, but filtering it intelligently. LocationSpot addresses this challenge, filtering the noise of constant GPS pings to extract the signal of a health risk, ultimately proving that efficient software architecture can directly contribute to personal well-being. The system stands as a scalable foundation, ready to be expanded into a more complex suite of location-based services in the future.

---

## 6. FUTURE SCOPE

While **LocationSpot** successfully demonstrates the core principles of real-time geospatial tracking and context-aware alerting, the current implementation represents a foundational prototype. The modular nature of the architecture separating ingestion, processing, and visualization provides a robust platform for significant future enhancements. The scope for future development spans three key areas: Advanced Data Analytics, System Scalability, and Enhanced User Functionality.

### 6.1 Advanced Analytics and Predictive Modeling

Currently, the system operates on a "reactive" basis: it sees a location, checks the current air quality, and reacts. The next stage of development involves shifting towards "predictive" analysis.

- **Machine Learning Integration:** By accumulating long-term data on user movement patterns and historical air quality, a Machine Learning (ML) model could be trained. The system could learn the user's daily commute routine and predict their exposure _before_ they leave their house. For example, if the system knows the user travels to a specific downtown area at 9:00 AM every weekday, it could preemptively check the forecasted AQI for that destination and warn the user to take a mask `before` they start their journey.
- **Heatmap Generation:** Instead of simple polylines showing routes, the frontend could be upgraded to generate "Pollution Heatmaps." by aggregating data from multiple users (anonymously), the system could identify city-wide pollution hotspots that official sensors might miss, essentially crowdsourcing air quality data.
- **Cumulative Exposure Tracking:** The system currently alerts based on instantaneous thresholds. A future scope would be to calculate _cumulative_ exposure. The backend could integrate the PM 2.5 levels over time to estimate the total dosage of pollutants a user inhaled during a specific trip, providing a more medically relevant health metric.

### 6.2 System Scalability and Multi-Tenancy

The current architecture is optimized for a single-user or small-group scenario. To scale this into a commercial-grade product, several architectural changes would be required.

- **Multi-User & Social Features:** The database schema can be expanded to support true multi-tenancy with robust authentication (OAuth2). This would allow for "Family Safety" features, where a parent receives an alert not only when they enter a pollution zone, but also when their child enters a specific area.
- **Geofencing Capabilities:** Moving beyond just Air Quality, the system can implement dynamic geofencing. Users could define custom polygons on the map (e.g., "Home," "Office," "Gym"). The backend would then trigger generic webhooks upon entering or exiting these zones, allowing integration with Home Automation systems (e.g., turning on the air purifier when the user is 1km away from home).
- **Protocol Diversity:** While OwnTracks (HTTP) and Open-Meteo are excellent tools, the backend could be abstracted further to accept data from other sources, such as dedicated hardware IoT sensors (like Arduino or ESP32 based GPS trackers) attached to vehicles or assets, expanding the use case to fleet management.

### 6.3 Enhanced Notification and Interactivity

The current alerting mechanism is binary (Mask / No Mask). Future iterations could offer richer interactions.

- **Granular Alerting Profiles:** Users should be able to set their own sensitivity thresholds. An asthmatic user might want an alert at PM 2.5 > 50, while another user might only want alerts at > 150.
- **Multi-Channel Notifications:** Integrating with platforms beyond simple push notifications, such as WhatsApp Business API or SMS gateways (via Twilio), ensuring that critical alerts reach the user even without an internet data connection.
- **Apple Watch / WearOS Integration:** Since the project is health-focused, extending the frontend to wearable devices would be a logical step. A simple vibration on the wrist when entering a high-pollution zone is far more effective than a phone notification that might be missed in a pocket.

### 6.4 Conclusion on Scope

In conclusion, LocationSpot stands as a versatile "Geospatial Event Bus." The immediate future scope lies in refining the intelligence of the alerts moving from simple "IF THIS THEN THAT" logic to predictive, AI-driven suggestions. By leveraging the existing Python-FastAPI backbone, these features can be added iteratively, transforming the project from a location logger into a comprehensive Personal Environmental Health Assistant.
