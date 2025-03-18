import os
import sys
import logging
import pymongo
from logging.handlers import TimedRotatingFileHandler
from shapely.geometry import Polygon
from datetime import datetime
from zoneinfo import ZoneInfo
from config import config


def est_time(*args):
    """Convert current time to US Eastern Time"""
    return datetime.now(ZoneInfo("America/New_York")).timetuple()

def setup_logging():
    # Configure the log file path
    log_file = config['main_log_file']
    log_folder = os.path.split(log_file)[0]
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    # Get the root logger and configure it
    root_logger = logging.getLogger()
    root_logger.handlers = []  # Remove existing handlers
    root_logger.setLevel(logging.DEBUG)

    # Console handler (will go to gunicorn error log)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # File handler
    file_handler = TimedRotatingFileHandler(log_file, when='D', interval=30)
    file_handler.setLevel(logging.INFO)
    
    # Formatters
    logging.Formatter.converter = est_time
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S %Z'
    )
    
    # Apply formatters
    console_handler.setFormatter(detailed_formatter)
    file_handler.setFormatter(detailed_formatter)
    
    # Add handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

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

def formatMetadata(row):
    return {
        'flight_id': row['flight_id'],
        'cog_path': row['cog_path'],
        'mission_start_time': str(row['mission_start_time']),
        'research_station': row.get('research_station', 'virtual'),
        'camera_make': row['camera_make'],
        'camera_model': row['camera_model'],
        'file_type': row['file_type'],
        'comments': row['comments'] if len(row['comments']) <= 256 else f"{row['comments'][:254]}..",
        'pilot_name': row['pilot_name'],
        'cloudiness': row['cloudiness'],
        'display_name': row.get('display_name', 'Name not set'),
    }