import hmac, hashlib, os, time

SECRET = os.environ.get("P2P_SECRET", "")

def _sign(body: bytes, ts: str) -> str:
    return hmac.new(SECRET.encode(), ts.encode() + b"." + body,
                    hashlib.sha256).hexdigest()

def headers_for(body: bytes = b"") -> dict:
    ts = str(int(time.time()))
    return {"X-P2P-Timestamp": ts, "X-P2P-Signature": _sign(body, ts)}

def verify(req) -> bool:
    ts  = req.headers.get("X-P2P-Timestamp", "")
    sig = req.headers.get("X-P2P-Signature", "")
    if not SECRET or not ts.isdigit() or abs(time.time() - int(ts)) > 60:
        return False
    return hmac.compare_digest(sig, _sign(req.get_data(), ts))
