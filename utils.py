import os
import pymongo
import logging
from logging.handlers import TimedRotatingFileHandler
from shapely.geometry import Polygon
from config import config


def setup_logging():
    log_file = config['log_file']
    log_folder = os.path.split(log_file)[0]
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
    file_handler = TimedRotatingFileHandler(log_file, when='D', interval=30)

    # Set the log level and formatter
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # Add the file handler to the root logger
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger().addHandler(file_handler)


def connectDb():
    try:
        database_details = config['database_details']
        client = pymongo.MongoClient(database_details['host'],
                                     username=database_details['username'],
                                     password=database_details['password'],
                                     authSource=database_details['auth_source'],
                                     authMechanism=database_details['auth_mechanism'])
        collection = client[database_details['database']][database_details[
            'collection']]
        logging.info({
            'service': 'database connection',
            'message': 'connection started'
        })
    except Exception as e:
        logging.error({
            'service': 'database connection',
            'message': e
        })
        return None, None
    return client, collection


def check_intersection(source, spatialQuery):
    logging.info({
        'service': 'check-intersection',
        'message': 'spatial query coordinates received'
    })
    p1 = Polygon(source)
    for query in spatialQuery:
        p2 = Polygon(query)
        if p2.intersects(p1):
            return True
    return False


def modifyGridLayout(grid, rows, cols, start_point, deadheaded=True):
    logging.info({
        'grid_id': 'feature not added',
        'service': 'modify grid',
        'message': 'modifying plot grid layout according to walk pattern'
    })
    modified_layout = []
    count = 0
    if start_point == 'tl' and deadheaded:
        return grid
    elif start_point == 'tl' and not deadheaded:
        for i in range(rows):
            if i % 2 == 0:
                modified_layout.extend(grid[count:count + cols])
                count += cols
            else:
                current_row = grid[count:count + cols]
                plot_numbers = reversed([x['plot_num'] for x in current_row])
                for grid, number in zip(current_row, plot_numbers):
                    grid['plot_num'] = number
                    grid['plot_name'] = f'Plot {number}'
                modified_layout.extend(current_row)
                count += cols

    elif start_point == 'tr' and not deadheaded:
        for i in range(rows):
            if i % 2 != 0:
                modified_layout.extend(grid[count:count + cols])
                count += cols
            else:
                current_row = grid[count:count + cols]
                plot_numbers = reversed([x['plot_num'] for x in current_row])
                for plot, number in zip(current_row, plot_numbers):
                    plot['plot_num'] = number
                    plot['plot_name'] = f'Plot {number}'
                modified_layout.extend(current_row)
                count += cols
    elif start_point == 'tr' and deadheaded:
        for i in range(rows):
            current_row = grid[count: (count + cols)]
            plot_numbers = reversed([x['plot_num'] for x in current_row])
            for plot, number in zip(current_row, plot_numbers):
                plot['plot_num'] = number
                plot['plot_name'] = f'Plot {number}'
            modified_layout.extend(current_row)
            count += cols

    elif start_point == 'bl' and deadheaded:
        for i in reversed(range(rows)):
            current_row = grid[i * cols: (i + 1) * cols]
            for plot in current_row:
                plot['plot_num'] = count + 1
                plot['plot_name'] = f'Plot {count + 1}'
                count += 1
            modified_layout.extend(current_row)
    elif start_point == 'bl' and not deadheaded:
        for i in reversed(range(rows)):
            current_row = grid[i * cols: (i + 1) * cols]
            if (rows - i) % 2 == 0:
                current_row = current_row[::-1]
            for plot in current_row:
                plot['plot_num'] = count + 1
                plot['plot_name'] = f'Plot {count + 1}'
                count += 1
            modified_layout.extend(current_row)

    elif start_point == 'br' and deadheaded:
        for i in reversed(range(rows)):
            current_row = grid[i * cols: (i + 1) * cols]
            current_row = current_row[::-1]
            for plot in current_row:
                plot['plot_num'] = count + 1
                plot['plot_name'] = f'Plot {count + 1}'
                count += 1
            modified_layout.extend(current_row)

    elif start_point == 'br' and not deadheaded:
        for i in reversed(range(rows)):
            current_row = grid[i * cols: (i + 1) * cols]
            if (rows - i) % 2 != 0:
                current_row = current_row[::-1]
            for plot in current_row:
                plot['plot_num'] = count + 1
                plot['plot_name'] = f'Plot {count + 1}'
                count += 1
            modified_layout.extend(current_row)
    return modified_layout
