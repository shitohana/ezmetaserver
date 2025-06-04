from flask import Flask, request, jsonify, render_template
import requests
import json

app = Flask(__name__, static_url_path='',
            static_folder="dist", template_folder="dist")
cache = {}
HX = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization"
}


@app.route("/")
def main():
    return render_template('index.html')


@app.route('/proxy', methods=['GET', 'POST', 'OPTIONS'])
def proxy():
    target_url = request.args.get("url")
    if not target_url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    if request.method == "OPTIONS":
        return "", 200, HX

    obj = [target_url, request.data.decode('utf-8')]
    key = 'X' + str(hash(json.dumps(obj)))
    if key in cache:
        print('Hash found!', key)
        return cache[key], 200, HX

    try:
        if request.method == "POST":
            response = requests.post(
                target_url, headers=request.headers, data=request.data)
        else:
            response = requests.get(
                target_url, headers=request.headers)

        headers = dict(response.headers)
        headers["Access-Control-Allow-Origin"] = "*"
        headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        cache[key] = response.content
        return cache[key], response.status_code, headers

    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9091, debug=True)

# http://0.0.0.0:9091/proxy?url=http://localhost:9090/api/v1/dump/api/ezmetafetch
