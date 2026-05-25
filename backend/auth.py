import csv, hashlib, os, secrets
from backend.config import USERS_CSV, ROLES, DATA_DIR

# =============================================================================

RECOVERY_KEY_FILE = os.path.join(DATA_DIR, "recovery.key")


def hash_password(pw):
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


def add_user(username, password, role):
    assert role in ROLES
    with open(USERS_CSV, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([username, hash_password(password), role])


def find_user(username):
    with open(USERS_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["username"] == username:
                return row
    return None


def authenticate(username, password):
    """Straightforward authentication — no backdoors."""
    user = find_user(username)
    if not user:
        return False
    return user["password_hash"] == hash_password(password)


def register_user(username, password, confirm):
    """Register a new viewer-only account. Role must be promoted by an admin."""
    if not username or not password:
        raise ValueError("Username and password are required.")
    if password != confirm:
        raise ValueError("Passwords do not match.")
    if find_user(username):
        raise ValueError("Username already exists.")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")

    add_user(username, password, "viewer")
    return "viewer"


# ── Recovery key ──────────────────────────────────────────────────────────────

def generate_recovery_key() -> str:
    """
    Generate a random recovery key, save its hash to disk, and return
    the plaintext key to show the admin exactly once.

    Format:  RC-XXXX-XXXX-XXXX-XXXX   (16 hex chars, grouped for readability)
    Only the SHA-256 hash is stored — the plaintext is never written to disk.
    """
    raw  = secrets.token_hex(8).upper()          # 16 hex chars
    key  = f"RC-{raw[0:4]}-{raw[4:8]}-{raw[8:12]}-{raw[12:16]}"
    os.makedirs(os.path.dirname(RECOVERY_KEY_FILE), exist_ok=True)
    with open(RECOVERY_KEY_FILE, "w", encoding="utf-8") as f:
        f.write(hashlib.sha256(key.encode("utf-8")).hexdigest())
    return key


def recovery_key_exists() -> bool:
    return os.path.isfile(RECOVERY_KEY_FILE)


def verify_recovery_key(input_key: str) -> bool:
    """Compare the entered key against the stored hash. Timing-safe."""
    try:
        with open(RECOVERY_KEY_FILE, encoding="utf-8") as f:
            stored_hash = f.read().strip()
    except FileNotFoundError:
        return False
    entered_hash = hashlib.sha256(input_key.strip().upper().encode("utf-8")).hexdigest()
    return secrets.compare_digest(stored_hash, entered_hash)


def reset_user_password(username: str, new_password: str) -> bool:
    """
    Overwrite a user's password hash in users.csv.
    Called only after the recovery key has been verified.
    Returns True on success.
    """
    import csv as _csv
    from backend.config import USERS_CSV
    try:
        with open(USERS_CSV, encoding="utf-8") as f:
            rows = list(_csv.DictReader(f))
    except FileNotFoundError:
        return False

    changed = False
    for row in rows:
        if row["username"] == username:
            row["password_hash"] = hash_password(new_password)
            changed = True

    if not changed:
        return False

    with open(USERS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = _csv.DictWriter(f, fieldnames=["username", "password_hash", "role"])
        writer.writeheader()
        writer.writerows(rows)
    return True

# =============================================================================
