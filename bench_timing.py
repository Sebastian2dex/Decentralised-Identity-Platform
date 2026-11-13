"""
bench_timing.py - measures real execution times for the report.

Run from the project root (next to app.py):
    python3 bench_timing.py            # full run
    python3 bench_timing.py --quick    # smaller, faster run

Uses temp folders only, so your real chain.json / auth.db are untouched.
Results are printed and saved to bench_results.json.
"""
import os, sys, time, json, statistics, tempfile, threading, logging, argparse, platform

# Must be set BEFORE importing the app (p2p_auth reads the secret at import).
os.environ.setdefault("P2P_SECRET", "bench-secret")
os.environ["ADMIN_USER"] = "admin"
os.environ["ADMIN_PASS"] = "admin123"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from werkzeug.serving import make_server
from app import create_app
from blockchain.chain import Block

logging.getLogger("werkzeug").setLevel(logging.ERROR)
logging.getLogger("blockchain.store").setLevel(logging.ERROR)

ap = argparse.ArgumentParser()
ap.add_argument("--quick", action="store_true")
args = ap.parse_args()

if args.quick:
    N_MINE, N_ISSUE, SIZES, N_LOOKUP, PEER_COUNTS, N_PROP = 100, 30, [10, 100], 100, [1, 2], 15
else:
    N_MINE, N_ISSUE, SIZES, N_LOOKUP, PEER_COUNTS, N_PROP = 300, 100, [10, 100, 500, 1000], 200, [1, 2, 4], 30

BASE_PORT = 5600
WARMUP = 3
results = {}


# ── helpers ──────────────────────────────────────────────────────────────────
def stats(xs):
    """xs in milliseconds."""
    xs = sorted(xs)
    n = len(xs)
    return {
        "n": n,
        "mean": round(statistics.mean(xs), 3),
        "median": round(statistics.median(xs), 3),
        "p95": round(xs[int(0.95 * (n - 1))], 3),
        "min": round(xs[0], 3),
        "max": round(xs[-1], 3),
        "stdev": round(statistics.stdev(xs), 3) if n > 1 else 0.0,
    }


def show(name, s):
    print(f"  {name:<34} mean {s['mean']:>9.3f} | median {s['median']:>9.3f} | "
          f"p95 {s['p95']:>9.3f} | min {s['min']:>9.3f} | max {s['max']:>9.3f} ms  (n={s['n']})")


def new_node(port):
    d = tempfile.mkdtemp()
    app = create_app(chain_path=f"{d}/chain.json", peers_path=f"{d}/peers.json",
                     auth_db_path=f"{d}/auth.db", node_url=f"http://127.0.0.1:{port}")
    return app, app.config["STORE"]


def start_server(app, port):
    srv = make_server("127.0.0.1", port, app, threaded=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def new_did(client):
    return client.post("/wallet/create-did").get_json()["did"]


# ── 1. block generation ──────────────────────────────────────────────────────
print("\n[1] Block generation")

# 1a. pure proof of work (difficulty 3)
times, nonces = [], []
for i in range(N_MINE + 20):
    b = Block(index=1, timestamp=time.time(), block_type="CREDENTIAL", did="did:x",
              data={"i": i, "username": "Alpha Beta", "degree": "B.Tech", "expiry": "2030-01-01"},
              prev_hash="0" * 64)
    t0 = time.perf_counter()
    b.mine(3)
    dt = (time.perf_counter() - t0) * 1000
    if i >= 20:                                   # skip warm-up
        times.append(dt)
        nonces.append(b.nonce)
s = stats(times)
s["mean_nonce"] = round(statistics.mean(nonces), 1)
results["mining_pow_only"] = s
show("proof of work only", s)
print(f"  mean attempts (nonce) = {s['mean_nonce']}  (theory: 4096)")

# 1b. full issue: mine + validate + append + write chain.json (no peers)
app, store = new_node(BASE_PORT)
c = app.test_client()
did = new_did(c)
times = []
for i in range(N_ISSUE + 5):
    t0 = time.perf_counter()
    store.issue_credential(did, "Alpha Beta", f"Degree {i}", "2030-01-01")
    dt = (time.perf_counter() - t0) * 1000
    if i >= 5:
        times.append(dt)
s = stats(times)
results["issue_full"] = s
show("issue (mine + save, no peers)", s)

# ── 2. credential verification vs chain size ─────────────────────────────────
print("\n[2] Credential verification (lookup + hash check)")
results["verification"] = {}
for size in SIZES:
    app, store = new_node(BASE_PORT + 1)
    c = app.test_client()
    target = None
    for i in range(size):                         # build a chain of `size` blocks
        d = new_did(c)
        store.chain.issue_credential(d, "Alpha Beta", "B.Tech", "2030-01-01")
        target = d
    direct, http = [], []
    for i in range(N_LOOKUP + 10):
        t0 = time.perf_counter()
        r = store.get_credentials_for_did(target)
        dt1 = (time.perf_counter() - t0) * 1000
        t0 = time.perf_counter()
        resp = c.get(f"/wallet/credentials?did={target}")
        dt2 = (time.perf_counter() - t0) * 1000
        assert r["status"] == "active" and resp.status_code == 200
        if i >= 10:
            direct.append(dt1)
            http.append(dt2)
    results["verification"][size] = {"direct": stats(direct), "endpoint": stats(http)}
    show(f"chain={size:<5} direct lookup", stats(direct))
    show(f"chain={size:<5} HTTP endpoint", stats(http))

# ── 3. P2P propagation ───────────────────────────────────────────────────────
print("\n[3] P2P propagation (sender broadcast -> all peers appended)")
results["propagation"] = {}
port = BASE_PORT + 10
for n_peers in PEER_COUNTS:
    s_app, sender = new_node(port)
    port += 1
    servers, receivers = [], []
    for _ in range(n_peers):
        r_app, r_store = new_node(port)
        servers.append(start_server(r_app, port))
        receivers.append(r_store)
        sender.register_peer(f"http://127.0.0.1:{port}")
        port += 1
    time.sleep(0.5)                               # let the servers come up

    did = new_did(s_app.test_client())
    times, timeouts = [], 0
    for i in range(N_PROP + WARMUP):
        block = sender.chain.issue_credential(did, "Alpha Beta", f"Degree {i}", "2030-01-01")
        target_len = sender.chain_length()
        t0 = time.perf_counter()                  # clock starts AFTER mining
        sender._broadcast_block(block)
        deadline = t0 + 5.0
        arrived = True
        while any(r.chain_length() < target_len for r in receivers):
            if time.perf_counter() > deadline:
                arrived = False
                break
            time.sleep(0.0002)
        if arrived:
            if i >= WARMUP:                       # skip warm-up rounds
                times.append((time.perf_counter() - t0) * 1000)
        else:
            timeouts += 1
            print(f"    timeout #{timeouts} at block {i}")
            if timeouts >= 3:
                print("    giving up: broadcast is not reaching peers")
                break
    for srv in servers:
        srv.shutdown()
    if times:
        s = stats(times)
        s["timeouts"] = timeouts
        results["propagation"][n_peers] = s
        show(f"1 sender -> {n_peers} peer(s)", s)
    else:
        print(f"  1 sender -> {n_peers} peer(s): no successful runs")

# ── summary ──────────────────────────────────────────────────────────────────
results["environment"] = {
    "os": platform.platform(),
    "machine": platform.machine(),
    "processor": platform.processor(),
    "python": platform.python_version(),
    "difficulty": 3,
    "quick_mode": args.quick,
}
with open("bench_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\nEnvironment:", results["environment"]["os"], "| Python", results["environment"]["python"])
print("Saved to bench_results.json")
