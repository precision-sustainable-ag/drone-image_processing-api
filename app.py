import os
import io
import json
import logging
import zipfile
from datetime import datetime

import flask
from flask import Flask, send_from_directory
from flask_cors import CORS

from pyproj import Transformer
from rasterio.mask import mask
from shapely.geometry import Polygon, mapping
import numpy as np
from PIL import Image

import rasterio
from rasterio.mask import mask
from shapely.geometry import Polygon, mapping

import main
import utils
from config import config

# import sentry_sdk

app = Flask(__name__)
CORS(app)

utils.setup_logging()
logger = logging.getLogger(__name__)


# sentry_sdk.init(
#     dsn="http://349d2009f4a4516e69f08acbd4baf4b8@20.169.137.216//4",
#     traces_sample_rate=1.0, debug=True, environment='test'
# )

# -------------------------------------------------------------------
# Frontend static file serving (React build)
# -------------------------------------------------------------------

# Absolute path to the directory containing index.html and static/
FRONTEND_BUILD_DIR = os.path.join(os.path.dirname(__file__), '..', 'drone-image-manipulation', 'build')

@app.route('/static/<path:path>')
def serve_frontend_static(path):
    """Serve JS/CSS/assets from the React build's static/ directory."""
    return send_from_directory(os.path.join(FRONTEND_BUILD_DIR, 'static'), path)

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory(FRONTEND_BUILD_DIR, 'manifest.json')

@app.route('/favicon.ico')
@app.route('/drone-favicon.ico')
def serve_favicon():
    return send_from_directory(FRONTEND_BUILD_DIR, 'drone-favicon.ico')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    logging.info({
            'dir': FRONTEND_BUILD_DIR,
        })
    if path != "" and os.path.exists(os.path.join(FRONTEND_BUILD_DIR, path)):
        return send_from_directory(FRONTEND_BUILD_DIR, path)
    else:
        return send_from_directory(FRONTEND_BUILD_DIR, 'index.html')

@app.route('/ping', methods=['GET'])
def ping():
    response_body = {
        'status': 'healthy',
        'version': '1.0.0'
    }
    client, db_collection = utils.connectDb()
    query = {'cog_path': {'$exists': True}}
    results = db_collection.find(query)
    logging.info(results)
    return flask.Response(response=json.dumps(response_body), status=200,
                          mimetype='application/json')


@app.route('/flight-list', methods=['GET', 'POST'])
def loadFlightListSidebar():
    if flask.request.method == 'GET':
        logging.info({
            'service': 'flight-list get call',
            'message': 'processing started'
        })
        client, db_collection = utils.connectDb()
        query = {'cog_path': {'$exists': True}}
        results = db_collection.find(query)
        logging.info({
            'service': 'flight-list get call',
            'message': 'database queried'
        })
        # flight_details = []
        flight_details = {}
        for row in results:
            flight_details[row['flight_id']] = utils.formatMetadata(row)
        response = {
            'flights': flight_details
        }
        logging.info({
            'service': 'flight-list get call',
            'message': 'processing complete'
        })
        return flask.Response(response=json.dumps(response), status=200,
                              mimetype='application/json')
    else:
        logging.info({
            'service': 'flight-list post call',
            'message': 'processing started'
        })
        spatial_query = flask.request.get_json()

        # print(spatial_query['start_date'], type(spatial_query['start_date']))

        sq_start_date = datetime.strptime(spatial_query['start_date'],
                                          '%Y-%m-%dT%H:%M:%S.%fZ')
        sq_end_date = datetime.strptime(spatial_query['end_date'],
                                        '%Y-%m-%dT%H:%M:%S.%fZ')
        client, db_collection = utils.connectDb()
        # query = {'orthomosaic_url': {'$exists': True}}
        query = {
            '$and': [
                {'cog_path': {'$exists': True}},
                {'mission_start_time': {'$gte': sq_start_date, '$lte':
                    sq_end_date}},
            ]
        }
        results = db_collection.find(query)
        logging.info({
            'service': 'flight-list post call',
            'message': 'database queried'
        })
        # flight_details = []
        flight_details = {}
        for row in results:
            if utils.check_intersection(row['flight_bounding_box_3857'],
                                        spatial_query['polygon_coordinates']):
                # and (sq_start_date <= row['mission_start_time'] <=
                #      sq_end_date):
                # TODO: condition to check date
                flight_details[row['flight_id']] = utils.formatMetadata(row)
        response = {
            'flights': flight_details
        }
        logging.info({
            'service': 'flight-list post call',
            'message': 'processing complete'
        })
        return flask.Response(response=json.dumps(response), status=200,
                              mimetype='application/json')


@app.route('/set-grid', methods=['POST'])
def setGridBoundries():
    if flask.request.is_json:
        data = flask.request.get_json()

        client, db_collection = utils.connectDb()
        query = {'flight_id': data['flight_id']}
        result = db_collection.find(query)[0]
        # print(data)
        flight_data_dir = os.path.join(config['storage_path'],
                                       result.get('research_station',
                                                  'virtual'), 'flights',
                                       data['flight_id'])
        walkPattern = True if data['data_collection_method']['pattern'] == \
                              'dh' else False
        logging.info({
            'grid_id': 'feature not added',
            'service': 'set-grid',
            'message': 'data received'
        })
        # grids, features = main.defineGrids(data['coordinate_features'],
        #                                    data['data_collection_method'][
        #                                        'start_point'], walkPattern)
        features = data['coordinate_features']

        veg_index_data_dir = os.path.join(flight_data_dir, 'veg_indices')
        logging.info({
            'grid_id': 'feature not added',
            'service': 'set-grid',
            'message': 'accessing veg index files'
        })
        for filename in os.listdir(veg_index_data_dir):
            if '.tif' in filename:
                veg_index_type = filename.split('_')[0]
                veg_index_file = os.path.join(veg_index_data_dir, filename)
                features['features'] = main.getPlotIndices(features['features'],
                                                           veg_index_type,
                                                           veg_index_file)

        logging.info({
            'grid_id': 'feature not added',
            'service': 'set-grid',
            'message': 'accessing database for additional details'
        })
        flight_details = utils.formatMetadata(result)
        field_features = data['field_features']

        response_body = {
            'status': 'success',
            'flight_details': flight_details,
            'features': features,
            'grid_id': 'feature not added',
            'field_features': field_features
        }
        logging.info({
            'grid_id': 'feature not added',
            'service': 'set-grid',
            'message': 'processing complete'
        })
        return flask.Response(response=json.dumps(response_body), status=200,
                              mimetype='application/json')
    else:
        response_body = {
            'status': 'failed',
            'message': 'bad request! try again'
        }
        return flask.Response(response=json.dumps(response_body), status=400,
                              mimetype='application/json')


@app.route('/export-images', methods=['POST'])
def exportPlotImages():
    if not flask.request.is_json:
        return flask.jsonify({'status': 'failed', 'message': 'Bad request!'}), 400
    
    try:
        data = flask.request.get_json()

        if not data or 'flight_id' not in data or 'features' not in data:
            return flask.jsonify({'status': 'failed', 'message': 'Incomplete data: flight_id and features are required.'}), 400

        flight_id = data['flight_id']
        features = data['features']

        _, db_collection = utils.connectDb()
        query = {'flight_id': flight_id}
        result = db_collection.find(query)[0]

        cog_tif_path = os.path.join(config['storage_path'],
                               result.get('research_station',
                                          'virtual'), 'flights',
                                flight_id, 'odm_orthophoto', 'odm_orthophoto_cog.tif')    

        # Transformer for coordinate conversion (TODO: implement crs_to coordinate system)
        source_crs = result.get('orthophoto_source_crs', 'EPSG:32617')
        transformer = Transformer.from_crs('EPSG:4326', source_crs, always_xy=True)
        
        zip_buffer = io.BytesIO()

        with rasterio.open(cog_tif_path) as tif, zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for feature in features:
                image_name = feature['properties'].get('name', f'plot-{len(zipf.filelist)}') + '.png'
                coordinates = feature['geometry']['coordinates'][0]
                
                transformed_coordinates = [transformer.transform(lon, lat) for lon, lat in coordinates]
                polygon = Polygon(transformed_coordinates)
                geometry = [mapping(polygon)]

                masked_tif, _ = mask(tif, geometry, crop=True)

                if masked_tif.shape[0] == 4: #RGBA bands
                    # Transpose data from (bands, height, width) to (height, width, bands)
                    pil_data = np.transpose(masked_tif, (1, 2, 0))
                else:
                    # Handle first band only
                    pil_data = masked_tif[0]

                # Scale data to 0-255 if needed
                if pil_data.dtype != np.uint8:
                    pil_data = (pil_data / pil_data.max() * 255).astype(np.uint8)
                img = Image.fromarray(pil_data)
                
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='PNG', dpi=(300, 300), quality=100)
                zipf.writestr(image_name, img_buffer.getvalue())

        zip_buffer.seek(0)
        return flask.send_file(zip_buffer, as_attachment=True, download_name="plot_images.zip", mimetype="application/zip")

    except Exception as e:
        return flask.jsonify({'status': 'failed', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run()
