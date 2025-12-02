from flask import Flask, render_template
import jwt
import time
import os

app = Flask(__name__)

# --- Metabase config ---
METABASE_SITE_URL = "http://metabase-enterprise.fcs1hk.com"
METABASE_SECRET_KEY = "e98da16a0f37180b293bcf3008d89ccb43d8097b27e93a925cef896647799e46"
DASHBOARD_ID = 39  # dashboard id, Esther need to provide the correct one


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


def build_param_values(account_uuids, property_uuids):
    """
    Decide how to encode locked parameters based on the dashboard.

    - Dashboard 34, my first test version to pass locked params into SQL:
        Uses SQL with split({{param}}, ',') so it expects a
        comma-separated string like "id1,id2,id3".
        [] is used to turn off the filter.

    - Other dashboards (e.g. 38, using models & field filters):
        Expect JSON arrays like ["id1", "id2"] for multi-select filters.
        [] is used to turn off the filter.
    """
    if DASHBOARD_ID == 34:
        account_param_value = ",".join(account_uuids) if account_uuids else []
        property_param_value = ",".join(property_uuids) if property_uuids else []
    else:
        # For dashboards using field filters / models, pass arrays
        account_param_value = account_uuids if account_uuids else []
        property_param_value = property_uuids if property_uuids else []

    return account_param_value, property_param_value


def build_iframe_url() -> str:
    """
    Build the Metabase embed iframe URL with locked parameters
    account_uuid and property_uuid.

    Rules (for locked params):
    - Param key must always be present in JWT "params".
    - If the filter is OFF, use [] as the value to disable it.
    - If the filter is ON:
        * For dashboard 34: use a comma-separated string of UUIDs.
        * For other dashboards (e.g. 38 with models): use a list of UUIDs.

    I'm using text files to simulate dynamic input for the locked params.
    Each file contains one UUID per line. If the file is empty or missing,
    the corresponding filter will be turned OFF.
    1) account_uuid_list.txt
    2) property_uuid_list.txt
    """

    # 1) Read account UUIDs
    account_uuids = read_uuid_list("account_uuid_list.txt")  # one per line

    # 2) Read property UUIDs
    property_uuids = read_uuid_list("property_uuid_list.txt")  # one per line

    # 3) Encode param values depending on dashboard
    account_param_value, property_param_value = build_param_values(
        account_uuids, property_uuids
    )

    print("[DEBUG] DASHBOARD_ID:", DASHBOARD_ID)
    print("[DEBUG] account_uuid param for JWT:", account_param_value)
    print("[DEBUG] property_uuid param for JWT:", property_param_value)

    # 4) Build JWT payload
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
