# Research notes — Python HTTP libraries

Working notes kept between research sessions. `atlas_v6.py` reads this file
during the Chapter 7 acceptance run ("read any existing research notes").

- requests: synchronous only; the long-time default. Simple API, huge
  ecosystem. No async support — pair it with a thread pool for concurrency.
- httpx: requests-compatible API with first-class async support (and HTTP/2).
  Sync and async clients share one interface.
- aiohttp: asyncio-native client and server. Fastest for high-concurrency
  fan-out, but its API differs most from requests.

Open question from the last session: how do timeout defaults differ?
(requests: none by default; httpx: 5 s default; aiohttp: 300 s total.)
