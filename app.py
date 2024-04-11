import json
import flask
import os
from flask import Flask
from flask_cors import CORS
from datetime import datetime

import main
import utils
from config import config

app = Flask(__name__)
CORS(app)


@app.route('/ping', methods=['GET'])
def ping():
    response_body = {
        'status': 'healthy'
    }
    # utils.connectDb()
    return flask.Response(response=json.dumps(response_body), status=200,
                          mimetype='application/json')


@app.route('/flight_list', methods=['GET', 'POST'])
def loadFlightListSidebar():
    if flask.request.method == 'GET':
        client, db_collection = utils.connectDb()
        query = {'orthomosaic_url': {'$exists': True}}
        results = db_collection.find(query)

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
            # flight_details.append({
            #     'flight_id': row['flight_id'],
            #     'orthomosaic_url': row['orthomosaic_url'],
            #     'display_name': display_name,
            #     'mission_start_time': str(row['mission_start_time'])
            # })

        response = {
            'flights': flight_details
        }
        return flask.Response(response=json.dumps(response), status=200,
                              mimetype='application/json')
    else:
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
        # print(response)
        return flask.Response(response=json.dumps(response), status=200,
                              mimetype='application/json')


@app.route('/setGrid', methods=['POST'])
def setGridBoundries():
    if flask.request.is_json:
        data = flask.request.get_json()
        # print(data)
        flight_data_dir = os.path.join(config['storage_path'],
                                       data['flight_id'])
        walkPattern = True if data['data_collection_method']['pattern'] == \
                              'dh' else False
        grids, features = main.defineGrids(data['coordinate_features'],
                                           data['data_collection_method'][
                                               'start_point'], walkPattern)

        # Temporary variables
        # veg_index_data_dir = os.path.join(flight_data_dir, 'veg_indices')
        # for filename in os.listdir(veg_index_data_dir):
        #     if '.tif' in filename:
        #         veg_index_type = filename.split('_')[0]
        #         veg_index_file = os.path.join(veg_index_data_dir,filename)
        ndvi_image = os.path.join(config['storage_path'], 'ndvi_image.tif')
        lai_image = os.path.join(config['storage_path'], 'lai_image.tif')

        features['features'] = main.getPlotIndices(features['features'], 'ndvi',
                                                   ndvi_image)
        features['features'] = main.getPlotIndices(features['features'], 'lai',
                                                   lai_image)

        client, db_collection = utils.connectDb()
        query = {'flight_id': data['flight_id']}
        result = db_collection.find(query)[0]
        flight_details = {
            'flight_id': result['flight_id'],
            'orthomosaic_url': result['orthomosaic_url'],
            'display_name': result.get('display_name', 'Name not set'),
            'mission_start_time': str(result['mission_start_time'])
        }

        response_body = {
            'status': 'success',
            # 'grids': grids,
            'flight_details': flight_details,
            'features': features
        }
        print(response_body['features'])
        return flask.Response(response=json.dumps(response_body), status=200,
                              mimetype='application/json')
    else:
        response_body = {
            'status': 'failed',
            'message': 'bad request! try again'
        }
        return flask.Response(response=json.dumps(response_body), status=400,
                              mimetype='application/json')


if __name__ == '__main__':
    app.run()
