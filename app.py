from flask import Flask, render_template
import jwt
import time
import os

app = Flask(__name__)

# --- Metabase config ---
METABASE_SITE_URL = "http://metabase-enterprise.fcs1hk.com"
METABASE_SECRET_KEY = "e98da16a0f37180b293bcf3008d89ccb43d8097b27e93a925cef896647799e46"
DASHBOARD_ID = 34  # dashboard id


def build_iframe_url():
    # Read UUIDs from file (one per line)
    uuid_file_path = os.path.join(os.path.dirname(__file__), "uuid_list.txt")
    with open(uuid_file_path, "r", encoding="utf-8") as f:
        uuids = [line.strip() for line in f if line.strip()]

    # Build single comma-separated string: "uuid1,uuid2,uuid3"
    account_uuid_param = ",".join(uuids)

    # JWT payload with LOCKED param
    payload = {
        "resource": {"dashboard": DASHBOARD_ID},
        "params": {
            "account_uuid": account_uuid_param  # must match SQL/locked param
        },
        "exp": int(time.time()) + 10 * 60,  # 10 minutes
    }

    token = jwt.encode(payload, METABASE_SECRET_KEY, algorithm="HS256")

    # pyjwt may return bytes depending on version; normalize to str
    if isinstance(token, bytes):
        token = token.decode("utf-8")

    iframe_url = f"{METABASE_SITE_URL}/embed/dashboard/{token}#bordered=true&titled=true"
    return iframe_url


@app.route("/")
def index():
    iframe_url = build_iframe_url()
    return render_template("index.html", iframe_url=iframe_url)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
