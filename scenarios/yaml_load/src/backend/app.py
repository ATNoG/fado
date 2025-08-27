from chalice import Chalice
import yaml
from io import BytesIO
import cgi
import os
from time import sleep, time

app = Chalice(app_name='dvfaas-insecure-deserialization')


def _get_parts():
    rfile = BytesIO(app.current_request.raw_body)
    content_type = app.current_request.headers['content-type']
    _, parameters = cgi.parse_header(content_type)
    parameters['boundary'] = parameters['boundary'].encode('utf-8')
    parsed = cgi.parse_multipart(rfile, parameters)
    return parsed


def anomaly_detected():
    signal_dir = '/shared'
    stime = time()
    while time() - stime < 1:
        try:
            files = os.listdir(signal_dir)
        except FileNotFoundError:
            files = []
        if 'anomalous' in files:
            file = signal_dir + "/anomalous"
            os.remove(file)
            return True
        sleep(0.01)
    return False


@app.route('/test')
def test_route():
    print('Test is working')
    return {'success': 'test'}

@app.route('/yaml_upload/{email}', methods = ['POST'], content_types=['multipart/form-data'], cors = True)
def index(email):
    files = _get_parts()
    try:
        for k, v in files.items():
            yaml_content = yaml.unsafe_load(BytesIO(v[0]))
            if anomaly_detected():
                return "Anomalous"
            return str(yaml_content)
    except Exception as e:
        return {"error": str(e)}
