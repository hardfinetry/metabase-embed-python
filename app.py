from flask import Flask, render_template
import jwt
import time
import os
"""
This version passes account_uuid and property_uuid as locked parameters
in the JWT, which then gets passed on to the sql query filters in Metabase.
"""
app = Flask(__name__)

# --- Metabase config ---
METABASE_SITE_URL = "http://metabase-enterprise.fcs1hk.com"
METABASE_SECRET_KEY = "e98da16a0f37180b293bcf3008d89ccb43d8097b27e93a925cef896647799e46"
DASHBOARD_ID = 38  # dashboard id, Esther need to provide the correct one


def read_uuid_list(filename: str):
    """
    Read a text file (one UUID per line), strip whitespace,
    and return a list of non-empty strings.
    """
    path = os.path.join(os.path.dirname(__file__), filename)
    if not os.path.exists(path):
        # If file doesn't exist, treat as empty list
        print(f"[WARN] {filename} not found, treating as empty list")
        return []

    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def build_iframe_url() -> str:
    """
    Build the Metabase embed iframe URL with locked parameters
    account_uuid and property_uuid.

    Rules (for locked params):
    - Param key must always be present in JWT "params".
    - If the filter is OFF, use [] as the value to disable it.
    - If the filter is ON, use a comma-separated string of UUIDs.

    I'm using text files to simulate dynamic input for the locked params.
    Each file contains one UUID per line. If the file is empty or missing,
    the corresponding filter will be turned OFF.
    1) account_uuid_list.txt
    2) property_uuid_list.txt
    This should actually be derived from Jimmy's token implementation
    """

    # 1) Read account UUIDs
    account_uuids = read_uuid_list("account_uuid_list.txt")  # one per line
    if account_uuids:
        account_param_value = ",".join(account_uuids)
    else:
        # Metabase static embedding docs: [] turns off a locked param
        account_param_value = []

    # 2) Read property UUIDs
    property_uuids = read_uuid_list("property_uuid_list.txt")  # one per line
    if property_uuids:
        property_param_value = ",".join(property_uuids)
    else:
        property_param_value = []

    print("[DEBUG] account_uuid param for JWT:", account_param_value)
    print("[DEBUG] property_uuid param for JWT:", property_param_value)

    # 3) Build JWT payload
    payload = {
        "resource": {"dashboard": DASHBOARD_ID},
        "params": {
            "account_uuid": account_param_value,
            "property_uuid": property_param_value,
        },
        "exp": int(time.time()) + 10 * 60,  # 10 minutes
    }

    token = jwt.encode(payload, METABASE_SECRET_KEY, algorithm="HS256")
    # pyjwt may return bytes in some versions; normalize to str
    if isinstance(token, bytes):
        token = token.decode("utf-8")

    iframe_url = f"{METABASE_SITE_URL}/embed/dashboard/{token}#bordered=true&titled=true"
    print("[DEBUG] iframe_url =", iframe_url)
    return iframe_url


@app.route("/")
def index():
    iframe_url = build_iframe_url()
    return render_template("index.html", iframe_url=iframe_url)


if __name__ == "__main__":
    # Run Flask dev server on http://localhost:5000
    app.run(debug=True, port=5000)
