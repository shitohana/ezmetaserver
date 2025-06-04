from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

cache = {}
custom = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization"
}


@app.route('/proxy', methods=['GET', 'POST', 'OPTIONS'])
def proxy():
    target_url = request.args.get("url")
    if not target_url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    if request.method == "OPTIONS":
        return "", 200, custom

    strx = json.dumps([request.method, target_url, request.get_json()])
    key = 'cache-' + str(hash(strx))
    if key in cache:
        print("FROM CACHE!", key)
        return cache[key], 200, custom

    try:
        if request.method == "POST":
            response = requests.post(
                target_url, headers=request.headers, data=request.data)
        else:
            response = requests.get(
                target_url, headers=request.headers)

        headers = dict(response.headers)
        headers = {**headers, **custom}
        cache[key] = response.content

        return response.content, response.status_code, headers

    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9091, debug=True)

# http://0.0.0.0:9091/proxy?url=http://localhost:9090/api/v1/dump/api/ezmetafetch
