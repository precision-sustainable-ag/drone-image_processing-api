import pymongo
from config import config
from shapely.geometry import Polygon


def connectDb():
    database_details = config['database_details']
    client = pymongo.MongoClient(database_details['host'],
                                 username=database_details['username'],
                                 password=database_details['password'],
                                 authMechanism='SCRAM-SHA-256')
    collection = client[database_details['database']][database_details[
        'collection']]
    return client, collection


def check_intersection(source, spatialQuery):
    p1 = Polygon(source)
    for query in spatialQuery:
        p2 = Polygon(query)
        if p2.intersects(p1):
            return True
    return False


def modifyGridLayout(grid, rows, cols, start_point, deadheaded=True):
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

    elif start_point == 'tr' and deadheaded:
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
    elif start_point == 'tr' and not deadheaded:
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
