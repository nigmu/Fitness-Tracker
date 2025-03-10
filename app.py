from flask import Flask, render_template, request, jsonify
import csv
import os
from datetime import datetime

app = Flask(__name__)
# app.config['DATA_FOLDER'] = 'data'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['DATA_FOLDER'] = os.path.join(BASE_DIR, 'data')


def get_csv_path(table):
    return os.path.join(app.config['DATA_FOLDER'], f'{table}.csv')


# def read_csv_data(table):
#     path = get_csv_path(table)
#     with open(path, 'r') as f:
#         reader = csv.DictReader(f)
#         return list(reader)

def read_csv_data(table):
    path = get_csv_path(table)
    if not os.path.exists(path):
        return []
    
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        data = list(reader)

        # Convert numeric values where applicable
        for row in data:
            for key in row.keys():
                if key not in ['id', 'date']:
                    try:
                        row[key] = float(row[key]) if row[key] else None  # Convert to float if possible
                    except ValueError:
                        pass
        return data


# def write_csv_data(table, data):
#     path = get_csv_path(table)
#     fieldnames = ['id', 'date'] + [col for col in data[0].keys() if col not in ('id', 'date')] if data else ['id', 'date']
#     with open(path, 'w', newline='') as f:
#         writer = csv.DictWriter(f, fieldnames=fieldnames)
#         writer.writeheader()
#         writer.writerows(data)

def write_csv_data(table, data):
    path = get_csv_path(table)

    # Ensure 'data' directory exists before writing
    os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)

    fieldnames = ['id', 'date'] + [col for col in data[0].keys() if col not in ('id', 'date')] if data else ['id', 'date']
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


@app.route('/')
def index():
    return render_template('data.html', active_tab='data')

@app.route('/data')
def data_page():
    return render_template('data.html', active_tab='data')

@app.route('/statistics')
def statistics_page():
    return render_template('statistics.html', active_tab='statistics')


@app.route('/api/<table>/data', methods=['GET'])
def get_table_data(table):
    data = read_csv_data(table)
    return jsonify(data=data)

@app.route('/api/<table>/add-row', methods=['POST'])
def add_row(table):
    data = read_csv_data(table)
    new_id = len(data) + 1 if data else 1
    new_date = datetime.now().strftime('%Y-%m-%d')
    new_row = {'id': str(new_id), 'date': new_date}
    
    if data:
        for key in data[0].keys():
            if key not in new_row:
                new_row[key] = ''
    
    data.append(new_row)
    write_csv_data(table, data)
    return jsonify(success=True, new_row=new_row)

@app.route('/api/<table>/add-column', methods=['POST'])
def add_column(table):
    column_name = request.json.get('name')
    data = read_csv_data(table)
    
    if column_name in data[0].keys() if data else False:
        return jsonify(success=False, error="Column already exists")
    
    for row in data:
        row[column_name] = ''
    
    write_csv_data(table, data)
    return jsonify(success=True)

@app.route('/api/<table>/delete-column', methods=['POST'])
def delete_column(table):
    column_name = request.json.get('name')
    data = read_csv_data(table)
    
    if column_name not in data[0].keys():
        return jsonify(success=False, error="Column doesn't exist")
    
    for row in data:
        del row[column_name]
    
    write_csv_data(table, data)
    return jsonify(success=True)

# Add this new route for row deletion
@app.route('/api/<table>/delete-row', methods=['POST'])
def delete_row(table):
    row_id = request.json.get('row_id')
    data = read_csv_data(table)
    new_data = [row for row in data if row['id'] != row_id]
    
    # Renumber IDs sequentially
    for index, row in enumerate(new_data, 1):
        row['id'] = str(index)
    
    write_csv_data(table, new_data)
    return jsonify(success=True)

@app.route('/api/<table>/update-cell', methods=['POST'])
def update_cell(table):
    row_id = request.json.get('row_id')
    column = request.json.get('column')
    value = request.json.get('value')
    
    data = read_csv_data(table)
    
    for row in data:
        if row['id'] == row_id:
            if column in row:
                row[column] = value
                write_csv_data(table, data)
                return jsonify(success=True)
    
    return jsonify(success=False, error="Cell not found")

# Add new endpoint for statistics data
@app.route('/api/statistics')
def get_statistics():
    stats = {}
    for table in ['food', 'exercise', 'body']:
        data = read_csv_data(table)
        stats[table] = data
    return jsonify(stats)

if __name__ == '__main__':
    os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)
    # app.run(debug=True)
    app.run(debug=False, host='0.0.0.0')

    