"""Exercise real inference and API contracts using an isolated test database."""
import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, default=Path('D:/CodexOutputs/2026-09-05-Forest-AI/acceptance.json'))
    args = parser.parse_args()
    work = Path('D:/CodexWork/2026-09-05/forest-acceptance')
    work.mkdir(parents=True, exist_ok=True)
    checks = []
    def check(name, condition):
        checks.append({'name': name, 'passed': bool(condition)})
    with tempfile.TemporaryDirectory(dir=work) as temporary:
        os.environ['FOREST_DATABASE_PATH'] = str(Path(temporary) / 'test.db')
        os.environ['FOREST_RESULTS_DIR'] = str(Path(temporary) / 'results')
        from fastapi.testclient import TestClient
        from AI.api_server import app
        with TestClient(app) as client:
            response = client.get('/api/health')
            health = response.json()
            check('health and model weights', response.status_code == 200 and health['model_exists'])
            check('V0.5 trained artifact available', health['campus_v05_available'])
            response = client.get('/')
            check('built Vue homepage served', response.status_code == 200 and '<div id="app">' in response.text)
            check('OpenAPI documentation', client.get('/openapi.json').status_code == 200)
            check('empty isolated sensor database', client.get('/api/sensors/latest').status_code == 404)
            reading = dict(device_id='acceptance-simulation', temperature_c=23.5, humidity_pct=65,
                           co2_ppm=420, light_lux=1000, soil_moisture_pct=40)
            response = client.post('/api/sensors/readings', json=reading)
            check('simulated sensor upload', response.status_code == 201)
            response = client.get('/api/sensors/latest', params={'device_id': reading['device_id']})
            check('sensor persistence and filtering', response.status_code == 200 and response.json()['temperature_c'] == 23.5)
            check('sensor history', client.get('/api/sensors/readings').json()['count'] == 1)
            check('invalid sensor rejected', client.post('/api/sensors/readings', json={**reading, 'humidity_pct': 101}).status_code == 422)
            for name, data, content_type, code in [('text', b'hello', 'text/plain', 415),
                                                  ('corrupt', b'not an image', 'image/png', 400),
                                                  ('oversized', b'x' * (10 * 1024 * 1024 + 1), 'image/png', 413)]:
                check(f'{name} upload rejected', client.post('/api/detect', files={'file': ('bad.png', data, content_type)}).status_code == code)
            sample = (ROOT / 'AI/input/tree.png').read_bytes()
            for method in ['baseline', 'campus_v05']:
                response = client.post('/api/detect', params={'vegetation_method': method}, files={'file': ('tree.png', sample, 'image/png')})
                check(f'{method} PNG inference', response.status_code == 200)
                if response.status_code == 200:
                    body = response.json()
                    check(f'{method} valid coverage', 0 <= body['vegetation']['coverage_pct'] <= 100)
                    for key in ['result_url', 'vegetation_url']:
                        image = client.get(body[key])
                        check(f'{method} {key} retrievable', image.status_code == 200 and image.headers['content-type'].startswith('image/'))
            check('unknown analysis mode rejected', client.post('/api/detect?vegetation_method=typo', files={'file': ('tree.png', sample, 'image/png')}).status_code == 422)
    report = {'created_at': datetime.now(timezone.utc).isoformat(), 'checks': checks,
              'passed': all(item['passed'] for item in checks), 'health': health,
              'scope': 'real local model inference, Vue static serving, API contracts; sensors simulated, no physical hardware or browser camera verified'}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=True, indent=2))
    sys.exit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
