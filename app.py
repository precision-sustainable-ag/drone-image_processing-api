import json
import flask
import os
import logging
from flask import Flask
from flask_cors import CORS
from datetime import datetime

import main
import utils
from config import config
# import sentry_sdk

app = Flask(__name__)
CORS(app)


# sentry_sdk.init(
# dsn="http://349d2009f4a4516e69f08acbd4baf4b8@20.169.137.216//4",
# traces_sample_rate=1.0,debug=True,environment='test'
# )
@app.route('/ping', methods=['GET'])
def ping():
    response_body = {
        'status': 'healthy'
    }
    # utils.connectDb()
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
        query = {'orthomosaic_url': {'$exists': True}}
        results = db_collection.find(query)
        logging.info({
            'service': 'flight-list get call',
            'message': 'database queried'
        })
        # flight_details = []
        flight_details = {}
        for row in results:
            display_name = row.get('display_name', 'Name not set')

            flight_details[row['flight_id']] = {
                'flight_id': row['flight_id'],
                'orthomosaic_url': row['orthomosaic_url'],
                'display_name': display_name,
                'mission_start_time': str(row['mission_start_time'])
            }
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
                {'orthomosaic_url': {'$exists': True}},
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
            # print(utils.check_intersection(row['flight_bounding_box_3857'],
            #                             spatial_query['polygon_coordinates']))
            if utils.check_intersection(row['flight_bounding_box_3857'],
                                        spatial_query['polygon_coordinates']):
                # and (sq_start_date <= row['mission_start_time'] <=
                #      sq_end_date):
                # TODO: condition to check date
                display_name = row.get('display_name', 'Name not set')
                flight_details[row['flight_id']] = {
                    'flight_id': row['flight_id'],
                    'orthomosaic_url': row['orthomosaic_url'],
                    'display_name': display_name,
                    'mission_start_time': str(row['mission_start_time'])
                }
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
        # print(data)
        flight_data_dir = os.path.join(config['storage_path'],
                                       data['flight_id'])
        walkPattern = True if data['data_collection_method']['pattern'] == \
                              'dh' else False
        logging.info({
            'grid_id': 'feature not added',
            'service': 'set-grid',
            'message': 'data received'
        })
        grids, features = main.defineGrids(data['coordinate_features'],
                                           data['data_collection_method'][
                                               'start_point'], walkPattern)

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

        client, db_collection = utils.connectDb()
        query = {'flight_id': data['flight_id']}
        result = db_collection.find(query)[0]
        logging.info({
            'grid_id': 'feature not added',
            'service': 'set-grid',
            'message': 'accessing database for additional details'
        })
        flight_details = {
            'flight_id': result['flight_id'],
            'orthomosaic_url': result['orthomosaic_url'],
            'display_name': result.get('display_name', 'Name not set'),
            'mission_start_time': str(result['mission_start_time']),
        }
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


@app.route('/export-data', methods=['POST'])
def exportData():
    if flask.request.is_json:
        data = flask.request.get_json()

        #TODO add/subtract/update information according to need
        body = [{"studyName": data["flight_details"]["display_name"],
                 "additionalInfo": {"features": data["features"],
                                    "flight_id": data["flight_details"]["flight_id"],
                                    "mission_start_time": data["flight_details"]["mission_start_time"]},
                 "commonCropName": data["field_features"]["crop_type"],
                 "contacts": [{"name": data["field_features"]["lead_scientist"],}],
                 }]

        curl_request = ( f"curl --include \\\n"
            f"     --request POST \\\n"
            f"     --header \"Content-Type: application/json\" \\\n"
            f"     --data-binary '{json.dumps(body, indent = 2)}' \\\n"
            f"'https://<your-brapi-instance>/brapi/v2/studies'"
        )

        return flask.Response(response=json.dumps(curl_request), status=200, mimetype='application/json')

    else:
        response_body = {
            'status': 'failed',
            'message': 'bad request! try again'
        }
        return flask.Response(response=json.dumps(response_body), status=400,
                              mimetype='application/json')


if __name__ == '__main__':
    utils.setup_logging()
    app.run()
