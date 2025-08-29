import os
import time
from dotenv import load_dotenv

load_dotenv()
BOT_OWNER_ID = str(os.getenv("BOT_OWNER_ID"))

# 🔐 Ensure logs folder and required files exist
os.makedirs("logs", exist_ok=True)
for file in ["users.txt", "blocked.txt", "block_count.txt"]:
    path = f"logs/{file}"
    if not os.path.exists(path):
        open(path, "a").close()

USERS_FILE = "logs/users.txt"
BLOCKED_FILE = "logs/blocked.txt"
BLOCK_COUNT_FILE = "logs/block_count.txt"

# 🚨 Flood / DDoS Tracking
user_request_log = {}
DDOS_REQUEST_LIMIT = 100   # max requests
DDOS_TIME_WINDOW = 10      # seconds


# ✅ Save user (with display info)
def save_user(user):
    user_id = str(user.id)
    if user_id == BOT_OWNER_ID:
        return

    username = f"@{user.username}" if user.username else None
    name = user.full_name or f"User {user_id}"
    display = username if username else f"{name} ({user_id})"

    with open(USERS_FILE, "r+") as f:
        users = f.read().splitlines()
        if user_id not in [u.split(" | ")[0] for u in users]:
            f.write(f"{user_id} | {display}\n")


# ✅ Check if user is banned
def is_banned(user_id):
    user_id = str(user_id)
    if user_id == BOT_OWNER_ID:
        return False
    with open(BLOCKED_FILE, "r") as f:
        return user_id in f.read().splitlines()


# ✅ Block user manually
def block_user(user_id):
    user_id = str(user_id)
    if user_id == BOT_OWNER_ID:
        return
    with open(BLOCKED_FILE, "r+") as f:
        blocked = set(f.read().splitlines())
        if user_id not in blocked:
            blocked.add(user_id)
            f.seek(0)
            f.write("\n".join(blocked) + "\n")


# ✅ Unblock user manually
def unblock_user(user_id):
    user_id = str(user_id)
    with open(BLOCKED_FILE, "r") as f:
        blocked = set(f.read().splitlines())
    if user_id in blocked:
        blocked.remove(user_id)
        with open(BLOCKED_FILE, "w") as f:
            f.write("\n".join(blocked) + "\n")


# ✅ Auto-block after 3 warnings
def handle_bot_block(user_id):
    user_id = str(user_id)
    if user_id == BOT_OWNER_ID:
        return False

    counts = {}
    with open(BLOCK_COUNT_FILE, "r+") as f:
        lines = f.read().splitlines()
        for line in lines:
            if ":" in line:
                uid, count = line.split(":")
                counts[uid] = int(count)

    current_count = counts.get(user_id, 0) + 1
    counts[user_id] = current_count

    with open(BLOCK_COUNT_FILE, "w") as f:
        for uid, count in counts.items():
            f.write(f"{uid}:{count}\n")

    if current_count >= 3:
        block_user(user_id)
        print(f"🚫 Blocked User {user_id}")
        return True

    print(f"⚠️ Warning {user_id} - {current_count}/3")
    return False


# ✅ Detect DDoS / Flood
def detect_ddos(user_id: int) -> bool:
    if str(user_id) == BOT_OWNER_ID:
        return False

    now = time.time()
    requests = user_request_log.get(user_id, [])
    requests = [t for t in requests if now - t < DDOS_TIME_WINDOW]
    requests.append(now)
    user_request_log[user_id] = requests

    return len(requests) > DDOS_REQUEST_LIMIT


# ✅ Check if user allowed (all security checks)
def is_user_allowed(user_id: int) -> bool:
    user_id = str(user_id)

    # Owner always allowed
    if user_id == BOT_OWNER_ID:
        return True

    # Already banned?
    if is_banned(user_id):
        print(f"🚫 Blocked user tried: {user_id}")
        return False

    # Flood / DDoS detection
    if detect_ddos(user_id):
        handle_bot_block(user_id)
        print(f"🚨 DDoS detected from {user_id}")
        return False

    return True


# ✅ Get user display name (from saved data)
def get_user_name(user_id: str) -> str:
    user_id = str(user_id)
    with open(USERS_FILE, "r") as f:
        for line in f.read().splitlines():
            if line.startswith(user_id + " | "):
                return line.split(" | ", 1)[1]
    return f"User {user_id}"
