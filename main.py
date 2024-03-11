import uuid
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

    grids = utils.modifyGridLayout(grids, rows, cols, walkStartPoint, walkPattern)

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
                'name': grid['plot_name']
            },
            'geometry': {
                'type': 'Polygon',
                'coordinates': [coordinates]
            }
        })
    return grids, features
