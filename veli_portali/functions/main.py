from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/rapor_uret', methods=['POST'])
def rapor_uret():
    data = request.json
    # Senin eski AI/PDF kodların buraya gelecek
    return jsonify({"durum": "Başarılı"})

if __name__ == '__main__':
    app.run()