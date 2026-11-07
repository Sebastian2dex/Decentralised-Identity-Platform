"""
test_threats.py - evidence for the threat-model section.
Run from the project root:   python3 test_threats.py
"""
import os, sys, json, time, hmac, hashlib, tempfile

# Must be set BEFORE the app is imported (p2p_auth reads the secret at import time).
os.environ["P2P_SECRET"] = "unit-test-secret"
os.environ["ADMIN_USER"] = "admin"
os.environ["ADMIN_PASS"] = "admin123"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from blockchain.chain import Block
from utils.p2p_auth import headers_for, _sign

results = []


def check(threat, label, ok):
    results.append((threat, label, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {threat:<12} {label}")


def new_node():
    d = tempfile.mkdtemp()
    app = create_app(chain_path=f"{d}/chain.json", peers_path=f"{d}/peers.json",
                     auth_db_path=f"{d}/auth.db", node_url="http://localhost:5000")
    return app.test_client(), app.config["STORE"]


def new_did(c):
    return c.post("/wallet/create-did").get_json()["did"]


def issue(c, did, degree="B.Tech"):
    return c.post("/issuer/issue", json={"did": did, "username": "Alpha Beta",
                                         "degree": degree, "expiry": "2030-01-01"})


def next_block(store, did, data=None, mine=True):
    b = Block(index=store.chain_length(), timestamp=time.time(),
              block_type="CREDENTIAL", did=did,
              data=data or {"username": "Alpha Beta", "degree": "X",
                            "expiry": "2030-01-01",
                            "verification_hash": store.compute_verification_hash("Alpha Beta", did)},
              prev_hash=store.last_block.hash)
    if mine:
        b.mine(3)
    else:
        while b.hash.startswith("000"):        # make sure PoW is NOT satisfied
            b.timestamp += 1
            b.hash = b._compute_hash()
    return b


def signed_post(c, block):
    body = json.dumps(block.to_dict()).encode()
    return c.post("/p2p/receive-block", data=body,
                  headers={**headers_for(body), "Content-Type": "application/json"})


# ── 1. Tampering ─────────────────────────────────────────────────────────────
c, store = new_node()
did = new_did(c)
issue(c, did, "B.Tech")
issue(c, did, "M.Tech")
blocks = store.chain.chain

check("Tampering", "untouched chain is valid", store.is_chain_valid())

blocks[1].data["degree"] = "PhD"
check("Tampering", "edit block data -> chain invalid", not store.is_chain_valid())

blocks[1].hash = blocks[1]._compute_hash()
check("Tampering", "edit + recompute hash -> next link breaks", not store.is_chain_valid())

blocks[1].nonce = 0
blocks[1].hash = blocks[1]._compute_hash()
blocks[1].mine(3)
check("Tampering", "edit + re-mine only that block -> still invalid", not store.is_chain_valid())

nonces = []
for i in range(30):
    b = Block(index=i, timestamp=time.time(), block_type="CREDENTIAL", did="d",
              data={"i": i}, prev_hash="0" * 64)
    b.mine(3)
    nonces.append(b.nonce)
mean = sum(nonces) / len(nonces)
check("Tampering", f"mean PoW attempts over 30 blocks = {mean:.0f} (theory: 4096)",
      1000 < mean < 12000)

# ── 2. Spoofing ──────────────────────────────────────────────────────────────
c, store = new_node()
did = new_did(c)
issue(c, did)
good = next_block(store, did)
body = json.dumps(good.to_dict()).encode()
ts = str(int(time.time()))
JSON = "application/json"

r = c.post("/p2p/receive-block", data=body, content_type=JSON)
check("Spoofing", "unsigned block -> 401", r.status_code == 401)

bad_sig = hmac.new(b"wrong-key", ts.encode() + b"." + body, hashlib.sha256).hexdigest()
r = c.post("/p2p/receive-block", data=body, content_type=JSON,
           headers={"X-P2P-Timestamp": ts, "X-P2P-Signature": bad_sig})
check("Spoofing", "signature made with wrong key -> 401", r.status_code == 401)

old = str(int(time.time()) - 3600)
r = c.post("/p2p/receive-block", data=body, content_type=JSON,
           headers={"X-P2P-Timestamp": old, "X-P2P-Signature": _sign(body, old)})
check("Spoofing", "valid signature, 1 h old timestamp -> 401", r.status_code == 401)

h = headers_for(body)
changed = json.dumps({**good.to_dict(), "did": "did:decen:" + "a" * 64}).encode()
r = c.post("/p2p/receive-block", data=changed, content_type=JSON, headers=h)
check("Spoofing", "body changed after signing -> 401", r.status_code == 401)

check("Spoofing", "unsigned GET /p2p/chain -> 401", c.get("/p2p/chain").status_code == 401)
check("Spoofing", "unsigned register-peer -> 401",
      c.post("/p2p/register-peer", json={"url": "http://evil:1"}).status_code == 401)
check("Spoofing", "signed GET /p2p/chain -> 200",
      c.get("/p2p/chain", headers=headers_for()).status_code == 200)
check("Spoofing", "correctly signed valid block -> 200", signed_post(c, good).status_code == 200)

# ── 3. Credential forgery ────────────────────────────────────────────────────
c, store = new_node()
did = new_did(c)
issue(c, did)

fake = next_block(store, did, mine=False)
check("Forgery", "signed block without proof of work -> 409",
      signed_post(c, fake).status_code == 409)

wrong_prev = next_block(store, did)
wrong_prev.prev_hash = "f" * 64
wrong_prev.hash = wrong_prev._compute_hash()
check("Forgery", "block with wrong prev_hash -> 409",
      signed_post(c, wrong_prev).status_code == 409)

did2 = new_did(c)
data = {"username": "Alpha Beta", "degree": "PhD", "expiry": "2099-01-01",
        "verification_hash": "0" * 64}
forged = next_block(store, did2, data=data)
check("Forgery", "mined block with bad verification hash is structurally accepted",
      signed_post(c, forged).status_code == 200)
cred = c.get(f"/wallet/credentials?did={did2}").get_json()["credentials"][0]
check("Forgery", "wrong verification hash is flagged hash_valid=false",
      cred["hash_valid"] is False)

c2, _ = new_node()
r = issue(c2, new_did(c2))
print(f"[INFO] Forgery      POST /issuer/issue without login -> HTTP {r.status_code}"
      + ("  (KNOWN GAP: issuer endpoint is open)" if r.status_code == 201 else ""))

# ── 4. Unauthorised revocation ───────────────────────────────────────────────
c, store = new_node()
did = new_did(c)
issue(c, did)

check("Revocation", "revoke without login -> 401",
      c.post("/verifier/revoke", json={"did": did, "reason": "x"}).status_code == 401)
check("Revocation", "login with wrong password -> 401",
      c.post("/verifier/login", json={"username": "admin", "password": "wrong"}).status_code == 401)
check("Revocation", "revoke after failed login -> 401",
      c.post("/verifier/revoke", json={"did": did, "reason": "x"}).status_code == 401)

c.post("/verifier/login", json={"username": "admin", "password": "admin123"})
check("Revocation", "revoke after real login -> 200",
      c.post("/verifier/revoke", json={"did": did, "reason": "test"}).status_code == 200)
check("Revocation", "revoke twice -> 409",
      c.post("/verifier/revoke", json={"did": did, "reason": "x"}).status_code == 409)
check("Revocation", "revoke unknown DID -> 404",
      c.post("/verifier/revoke", json={"did": "did:decen:" + "b" * 64}).status_code == 404)
check("Revocation", "issue to revoked DID -> 403", issue(c, did).status_code == 403)

did3 = new_did(c)
issue(c, did3)
rev = Block(index=store.chain_length(), timestamp=time.time(), block_type="REVOKE",
            did=did3, data={"reason": "x"}, prev_hash=store.last_block.hash)
rev.mine(3)
check("Revocation", "unsigned REVOKE block over P2P -> 401",
      c.post("/p2p/receive-block", json=rev.to_dict()).status_code == 401)

# ── summary ──────────────────────────────────────────────────────────────────
failed = [r for r in results if not r[2]]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)