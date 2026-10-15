from pathlib import Path
import math
import requests
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
API_KEY = 'ad717d0494e943a08af83f318f6e54d5'


@app.get('/')
def index():
    return send_from_directory(str(BASE_DIR), 'kakao.html')


@app.get('/api/cctv')
def get_cctv():
    try:
        coords = {name: float(request.args[name]) for name in ('minX', 'maxX', 'minY', 'maxY')}
        road_type = request.args.get('type', 'ex')
        if road_type not in ('ex', 'its') or not all(math.isfinite(v) for v in coords.values()):
            raise ValueError()
        if not (-180 <= coords['minX'] < coords['maxX'] <= 180 and -90 <= coords['minY'] < coords['maxY'] <= 90):
            raise ValueError()
    except (KeyError, ValueError):
        return jsonify(error='올바른 지도 영역과 도로 유형을 선택해주세요.'), 400
    try:
        response = requests.get(
            'https://openapi.its.go.kr:9443/cctvInfo',
            params=dict(apiKey=API_KEY, type=road_type, cctvType='5', getType='json', **coords),
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        body = payload.get('response', {})
        if not isinstance(body, dict) or 'data' not in body:
            return jsonify(error='ITS 응답에 CCTV 목록이 없습니다. 인증키와 API 이용 상태를 확인해주세요.'), 502
        items = body['data']
        if items is None:
            items = []
        if isinstance(items, dict):
            items = [items]
        if not isinstance(items, list):
            return jsonify(error='ITS CCTV 응답 형식을 확인해주세요.'), 502
        return jsonify([item for item in items if isinstance(item, dict)])
    except (requests.RequestException, ValueError, AttributeError):
        return jsonify(error='ITS CCTV 조회에 실패했습니다. 잠시 후 다시 시도해주세요.'), 502


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
