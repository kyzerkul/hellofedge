# cTrader Open API Research – 2026-09-28

## 1. Historical Trendbars (ProtoOAGetTrendbarsReq)

### Time Range Limits
- **M1**: Approximately 2 weeks (14 days) maximum; some documentation claims 5 weeks but practical limit is ~2 weeks.
- **Other periods**: Constraints vary by ProtoOATrendbarPeriod; no detailed table found in fetched docs.
- **History depth**: No documented overall limit; availability depends on broker. Data is retrievable as long as it exists on the broker's servers.

### Maximum Bar Count
- **Hard limit**: 14,000 bars per request.
- Common practical limits: ~2 weeks of M1 = ~20,160 bars (exceeds hard limit).
- Truncation: When time range exceeds limits, API silently truncates data (no error returned).

### Price Encoding
- **Format**: low price (int64) + deltaOpen, deltaClose, deltaHigh (all uint64 offsets from low).
- **Conversion**: Divide low by 100,000, add deltas (also in 1/100,000 units), round to symbol digits.
- **Example**: low=123000 (1.23), deltaClose=50000 (0.50) → close=1.73.
- **Bid/Ask**: Trendbars built exclusively from **bid prices**; ask-based bars not available.

### utcTimestampInMinutes
- **Definition**: Unix time in minutes representing bar open time.
- **Usage**: Compare values across successive bars to detect bar close (when it changes, previous bar is closed).

### Live Trendbar Delivery
- **Message**: ProtoOASubscribeLiveTrendbarReq subscribes; updates arrive in **ProtoOASpotEvent** messages.
- **Close signal**: utcTimestampInMinutes changes = new bar opened = previous bar closed.
- **Prerequisite**: Must first subscribe to ProtoOASubscribeSpotsReq for spot events.

**Sources**: 
- https://help.ctrader.com/open-api/symbol-data/
- https://help.ctrader.com/open-api/model-messages/

---

## 2. Rate Limits

- **Historical data** (ProtoOAGetTrendbarsReq, ProtoOAGetTickDataReq): **5 requests/second per connection**.
- **Other requests** (orders, positions, subscriptions): **50 requests/second per connection**.
- **Scope**: Per connection, not per user or application.
- **Excess**: Returns HTTP 429 with Retry-After header.

**Source**: https://help.ctrader.com/open-api/

---

## 3. Authentication & Tokens

### OAuth Flow
1. User authorizes app via redirect to `https://id.ctrader.com/my/settings/openapi/grantingaccess/`
2. Authorization code (1-minute expiry) returned
3. App exchanges code for access token via POST to `https://openapi.ctrader.com/apps/token`
4. Send ProtoOAApplicationAuthReq with credentials

### Access Token
- **Lifetime**: ~2,628,000 seconds ≈ 30 days.
- **Field in response**: expiresIn (seconds).

### Refresh Token
- **Lifetime**: Non-expiring (valid indefinitely).
- **How to refresh**: 
  - Protobuf: Send ProtoOARefreshTokenReq → receive ProtoOARefreshTokenRes
  - HTTP: POST to `https://openapi.ctrader.com/apps/token?grant_type=refresh_token&refresh_token=<token>&client_id=<id>&client_secret=<secret>`
- **Token invalidation**: Old tokens automatically invalidated when new ones are issued.

### Scopes
- **accounts**: Read-only access to account data.
- **trading**: Full trading and account management.

**Source**: https://help.ctrader.com/open-api/account-authentication/

---

## 4. Connection Details

### Hosts & Ports
| Environment | Protobuf (5035) | JSON (5036) |
|-----------|------|-----|
| **Demo** | demo.ctraderapi.com:5035 | demo.ctraderapi.com:5036 |
| **Live** | live.ctraderapi.com:5035 | live.ctraderapi.com:5036 |

- Both TCP (SSL/TLS required) and WebSocket supported.
- Separate connections for demo and live; each connection supports unlimited accounts of its type.

### Heartbeat
- **Message**: ProtoHeartbeatEvent.
- **Interval**: Send every 10 seconds to maintain connection (or if no messages for >30 seconds).

### JSON Message Format
```json
{
  "clientMsgId": "unique_string_id",
  "payloadType": 2100,
  "payload": { "clientId": "...", "clientSecret": "..." }
}
```
- **clientMsgId**: Client-assigned unique identifier (string).
- **payloadType**: Integer identifying message type.
- **payload**: Nested JSON object with message contents.

**Sources**:
- https://help.ctrader.com/open-api/proxies-endpoints/
- https://help.ctrader.com/open-api/connection/
- https://help.ctrader.com/open-api/sending-receiving-json/

---

## 5. Application Registration

### Process
1. Navigate to https://openapi.ctrader.com/
2. Log in with cTrader ID
3. Click "Add new app"
4. Complete form with detailed description
5. Submit → status = "submitted"
6. Email notification from Spotware (approval or request for details)

### Details
- **Cost**: Free (Spotware reserves right to change pricing).
- **Approval timeline**: NOT DOCUMENTED; no specific SLA given.
- **Demo accounts**: Supported; allowed for development and testing.
- **Broker demo accounts**: Standard cTrader demo accounts from any affiliated broker can be used.
- **Prop firm accounts**: NOT CONFIRMED (search results mention prop trials but no explicit Open API restriction documented).

**Sources**:
- https://help.ctrader.com/open-api/api-application/
- https://openapi.ctrader.com/

---

## 6. Symbols & USDJPY

### ProtoOASymbolsListReq
- **Purpose**: Retrieve available symbols for a trading account.
- **Returns**: List with symbolId and digits for each symbol.

### USDJPY Details
- **symbolId**: Varies by broker and server environment (example: 4 on some brokers).
- **digits**: Returned in ProtoOASymbolsListReq response (typically 3 for JPY pairs).
- **Lookup method**: Call ProtoOASymbolsListReq, filter by symbol name "USDJPY".

**Source**: https://help.ctrader.com/open-api/messages/

---

## 7. Account Flow

1. **ProtoOAApplicationAuthReq**: Authenticate application (clientId, clientSecret).
2. **ProtoOAGetAccountListByAccessTokenReq**: Retrieve list of authorized trading accounts.
3. **ProtoOAAccountAuthReq**: Authenticate specific account (ctidTraderAccountId, accessToken).

Each step requires successful response before proceeding.

**Source**: https://help.ctrader.com/open-api/account-authentication/

---

## Summary of "NOT CONFIRMED" Items

1. **Prop firm account restrictions**: No explicit ban documented; unclear if certain prop firms restrict Open API.
2. **Approval timeline**: No SLA or typical delay published.
3. **M3 bars**: Not mentioned in official Open API (would need custom aggregation from M1).

---

## Key Technical Notes

- **Trendbars from bid**: All OHLC bars use bid prices; ask quotes via ProtoOASubscribeSpotsReq.
- **M1 practical limit**: Despite documentation suggesting 5 weeks, approximately 2 weeks is achievable (see forum discussions).
- **Silent truncation**: Exceeding time range limits returns truncated data without error.
- **Heartbeat critical**: Maintain 10-second heartbeat or connection may drop after 30 seconds of inactivity.
- **Token refresh proactive**: Refresh before expiration to avoid authentication failures.

