import os
import uuid
import threading
import multiprocessing
import logging
import concurrent.futures
import rasterio
import numpy as np
from random import randrange

import utils


def line_intersection(l1, l2):
    line1 = (l1['Point 1'], l1['Point 2'])
    line2 = (l2['Point 1'], l2['Point 2'])

    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    # xdiff = (line1['1'][0] - line1['2'][0], line2['1'][0] - line2['2'][0])
    # ydiff = (line1['1'][1] - line1['2'][1], line2['1'][1] - line2['2'][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
        raise Exception('lines do not intersect')

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y


def defineGrids(data, walkStartPoint, walkPattern):
    logging.info({
        'grid_id': 'feature not added',
        'service': 'grid definition',
        'message': 'building grids from line information'
    })
    rows = len(data['horizontal']) + 1
    cols = len(data['vertical']) + 1
    # adding the bounding box lines to the horizontal and vertical grid lines
    data['horizontal'].insert(0, {
        'Point 1': data['box'][0],
        'Point 2': data['box'][1]
    })
    data['horizontal'].append({
        'Point 1': data['box'][3],
        'Point 2': data['box'][2]
    })

    data['vertical'].insert(0, {
        'Point 1': data['box'][0],
        'Point 2': data['box'][3]
    })
    data['vertical'].append({
        'Point 1': data['box'][1],
        'Point 2': data['box'][2]
    })

    grids = []
    plot_num = 1
    for index1 in range(1, len(data['horizontal'])):
        leftVL = data['vertical'][0]
        topHL = data['horizontal'][index1 - 1]
        tl = line_intersection(topHL, leftVL)
        bottomHL = data['horizontal'][index1]
        bl = line_intersection(bottomHL, leftVL)
        for index2 in range(1, len(data['vertical'])):
            leftVL = data['vertical'][index2 - 1]
            rightVL = data['vertical'][index2]
            tr = line_intersection(topHL, rightVL)
            br = line_intersection(bottomHL, rightVL)
            # TODO: should there be a calculation for top left and bottom
            #  left coordinates? (Intersect leftVL & topHL, leftVL & bottomHL)
            grids.append({
                'coordinates': {'tl': tl, 'bl': bl, 'tr': tr, 'br': br},
                'id': str(uuid.uuid4()),
                'plot_num': plot_num,
                'plot_name': f'Plot {plot_num}',
                'gli': randrange(10),
                'vari': randrange(100)
            })
            plot_num += 1
            tl = tr
            bl = br
    logging.info({
        'service': 'grid definition',
        'message': 'grids built'
    })
    grids = utils.modifyGridLayout(grids, rows, cols, walkStartPoint,
                                   walkPattern)

    order = {'tl': 0, 'tr': 1, 'br': 2, 'bl': 3}
    # order = {'tl': 3, 'tr': 0, 'br': 1, 'bl': 2}
    features = {
        'type': 'FeatureCollection',
        'features': []
    }
    for grid in grids:
        coordinates = []
        # for i in range(5):
        #     coordinates.append(grid['coordinates'])
        for k, v in grid['coordinates'].items():
            coordinates.insert(order[k], v)
        coordinates.append(coordinates[0])
        features['features'].append({
            'type': 'Feature',
            'id': grid['id'],
            'properties': {
                'name': grid['plot_name'],
                'plot_num': grid['plot_num']
            },
            'geometry': {
                'type': 'Polygon',
                'coordinates': [coordinates]
            }
        })
    logging.info({
        'grid_id': 'feature not added',
        'service': 'grid definition',
        'message': 'processing complete'
    })
    return grids, features


def getPlotIndices(plots, veg_index, image_path):
    windows = []
    logging.info({
        'grid_id': 'feature not added',
        'service': 'plot-index data',
        'message': f'processing started for {veg_index}'
    })
    try:
        with rasterio.open(image_path) as rasterio_dataset:
            for p in plots:
                plot = p['geometry']['coordinates'][0]
                xmin, ymax = plot[0]
                xmax, ymin = plot[2]
                window = rasterio_dataset.window(xmin, ymin, xmax, ymax)
                windows.append(window)

            # Read lock can be used if there is data error, else ideally
            # there should be no problems since all windows are different
            # regions

            read_lock = threading.Lock()
            results = []
            def process(window):
                with read_lock:
                    data = rasterio_dataset.read(1, window=window)
                    nodata_val = rasterio_dataset.nodata
                    if nodata_val is not None:
                        data = np.ma.masked_equal(data, nodata_val)
                    plot_mean_val = np.mean(data)
                    results.append(plot_mean_val)

            num_workers = multiprocessing.cpu_count()
            with concurrent.futures.ThreadPoolExecutor(
                    max_workers=num_workers) as executor:
                executor.map(process, windows)
            for p, val in zip(plots, results):
                p['properties'][veg_index] = val
    except Exception as e:
        logging.error({
            'grid_id': 'feature not added',
            'service': 'plot-index data',
            'message': e
        })
        return None
    logging.info({
        'grid_id': 'feature not added',
        'service': 'plot-index data',
        'message': f'processing complete for {veg_index}'
    })
    return plots

            # data = rasterio_dataset.read(1, window=window)
            # nodata_val = rasterio_dataset.nodata
            # if nodata_val is not None:
            #     data = np.ma.masked_equal(data, nodata_val)
            #
            # plot_mean_val = round(np.mean(data), 2)
            # p['properties'][veg_index] = plot_mean_val
    # print([x['properties']['ndvi'] for x in plots])

