from flask import (Flask, json, Response, request, abort)
import feedparser
from datetime import datetime
import time
from dateutil import tz
import os

app = Flask(__name__)
app.config.from_object("feedservice.default_settings")

if "FEEDSERVICE_SETTINGS" in os.environ:
    app.config.from_envvar("FEEDSERVICE_SETTINGS")

feeddb = app.config['BACKEND'](app.config)

@app.route("/feed/")
def read():
    feedurl = request.args.get("q")
    callback = request.args.get("callback")
    refresh = request.args.get("refresh")

    if not feedurl:
        abort(404)

    if refresh:
        data = feeddb.refresh(feedurl)
    else:
        data = feeddb.get(feedurl)

    jsonstr = json.dumps(data, default=unicode)

    if callback:
        return "%s(%s)" % (callback, jsonstr)
    else:
        return jsonstr

    
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)

