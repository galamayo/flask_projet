from flask import Flask, jsonify, request, Response
from datetime import datetime
from copy import deepcopy


app = Flask('RestAPI')


concerts = [{'id': 1, 'artist': 'Pink Floyd', 'venue': 'Werchter',
             'date': datetime.fromisoformat('2017-07-20T20:00:00-02:00')},
            {'id': 2, 'artist': 'Kraftwerk',  'venue': 'Domaine National de St Cloud',
             'date': datetime.fromisoformat('2022-09-26T15:00:00-02:00')}]
concerts_key = 3  # Sort of table autoincrement counter


def limit_offset(content_list, limit, offset):
    """
    :param content_list: the list on which limit and offset apply
    :param limit: limit the number of records returned
    :param offset: index of the 1st record returned
    :return: if limit or offset is not 0, return a subset of the list else the whole list
    """
    if limit or offset:
        return content_list[offset:offset + limit]
    return content_list


def reduce_fields(content_list, fields):
    """
    :param content_list: List of Dictionary
    :param fields: Comma separated list of dictionary key names to keep
    :return: Return the list of Dictionary with only the selected fields
    """
    if fields:
        fields = set(fields.split(','))
        return [{k: v for k, v in c.items() if k in fields} for c in content_list]
    return content_list


def encode_date(content_list, fields='date'):
    """
    :param content_list: List of Dictionary
    :param fields: Comma separated list of dictionary key to convert the datetime to iso format
    :return: For each record, encode the datetime field(s) into iso string(s)
    """
    assert fields != ''

    fields = fields.split(',')
    if content_list and all(field in content_list[0] for field in fields):
        content_list = deepcopy(content_list)
        for index in range(len(content_list)):
            for field in fields:
                content_list[index][field] = content_list[index][field].isoformat()
    return content_list


def content_index(content_list, field='id', value=None):
    """
    :param content_list: List of record
    :param field: field name to search on
    :param value: Value to search for
    :return: return the first found index of a record where record[field]==value
    """
    if content_list and field in content_list[0]:
        for index in range(len(content_list)):
            if content_list[index][field] == value:
                return index
    return None


@app.route('/concerts', methods=['POST'])
def post_concerts():
    """
    :return: On successful creation, return HTTP status 201, returning a Location header with a link to the
             newly-created resource with the 201 HTTP status.
             Else return an error message and HTTP status 400
    """
    global concerts
    global concerts_key

    if request.is_json:  # true if Content-Type == 'application/json'
        try:  # Try to read artist, venue and date
            artist = request.json['artist']
            venue = request.json['venue']
            dt = datetime.fromisoformat(request.json['date'])
        except KeyError:
            return jsonify({'error': 'Missing field(s)'}), 400
        except ValueError:
            return jsonify({'error': 'Wrong datetime format'}), 400

        try:  # Try to read id
            identity = int(request.json['id'])
            if content_index(concerts, 'id', identity):
                return jsonify({'error': 'Resource already exists'}), 400
            concerts_key = concerts_key if identity < concerts_key else identity+1
        except KeyError:  # Else generate a new key
            identity = concerts_key
            concerts_key += 1

        # Create and add a new concert
        concert = {'id': identity, 'artist': artist, 'venue': venue, 'date': dt}
        concerts.append(concert)

        # Return the response
        response = Response()
        response.headers['location'] = f'/concerts/{identity}'
        return response, 201
    else:
        return jsonify({'error': 'Incorrect Content-Type'}), 400


@app.route('/concerts/<int:identity>', methods=['POST'])
def post_concerts_id(identity):
    """
    :param identity: Id of a concert
    :return: If a resource with the id exist, return an error message and HTTP status 409
             Else return an error message and HTTP status 404
    """
    if content_index(concerts, 'id', identity):
        return jsonify({'error': 'Resource already exists'}), 409
    else:
        return jsonify({'error': 'Resource not found'}), 404


@app.route('/concerts', methods=['GET'])
def get_concerts():
    """
    :return: Return the list of concerts, optional pagination and fields restrictions available
             /concerts?limit=10&offset=10
             /concerts?fields=id,artist
    """
    limit = int(request.args.get('limit') or 0)
    offset = int(request.args.get('offset') or 0)
    fields = request.args.get('fields')

    concerts_temp = limit_offset(concerts, limit, offset)
    concerts_temp = reduce_fields(concerts_temp, fields)
    concerts_temp = encode_date(concerts_temp, 'date')

    return jsonify(concerts_temp), 200


@app.route('/concerts/<int:identity>', methods=['GET'])
def get_concerts_id(identity):
    """
    :param identity: Id of a concert
    :return: If identity is found, return a single concert and HTTP status 200, optional fields restrictions available
             else return an error message and HTTP status 404
    """
    fields = request.args.get('fields')

    index = content_index(concerts, 'id', identity)
    if index:
        concert_temp = [concerts[index]]
        concert_temp = reduce_fields(concert_temp, fields)
        concert_temp = encode_date(concert_temp, 'date')

        return jsonify(concert_temp[0])
    else:
        return jsonify({'error': 'Resource not found'}), 404


@app.route('/concerts', methods=['PUT'])
def put_concerts():
    """
    :return: An error message and HTTP status 405
    """
    return jsonify({'error': 'Method Not Allowed'}), 405


@app.route('/concerts/<int:identity>', methods=['PUT'])
def put_concerts_id(identity):
    """
    :param identity: Id of a concert
    :return: If identity is found, update the selected concert with a new record and return an HTTP status 204
             else create aa new concert an return an HTTP status 201
    """
    global concerts
    global concerts_key

    if request.is_json:  # true if Content-Type == 'application/json'
        try:  # Try to read artist, venue and date
            artist = request.json['artist']
            venue = request.json['venue']
            dt = datetime.fromisoformat(request.json['date'])
        except KeyError:
            return jsonify({'error': 'Missing field(s)'}), 400

        # Concert
        concert = {'id': identity, 'artist': artist, 'venue': venue, 'date': dt}

        index = content_index(concerts, 'id', identity)
        if index:  # Update an existing concert
            concerts[index] = concert
            return '', 204
        else:  # Create a new concert
            concerts_key = concerts_key if identity < concerts_key else identity+1
            concerts.append(concert)
            return '', 201
    else:
        return jsonify({'error': 'Incorrect Content-Type or no JSON payload'}), 400


@app.route('/concerts', methods=['PATCH'])
def patch_concerts():
    """
    :return: An error message and HTTP status 405
    """
    return jsonify({'error': 'Method Not Allowed'}), 405


@app.route('/concerts/<int:identity>', methods=['PATCH'])
def patch_concerts_id(identity):
    """
    :param identity: Id of a concert
    :return: If identity is found, update the selected concert fields and return an HTTP status 204
             else return an error message and HTTP status 404
    """
    global concerts
    global concerts_key

    if request.is_json:  # true if Content-Type == 'application/json'
        index = content_index(concerts, 'id', identity)
        if index:  # Update an existing concert
            for key in ['artist', 'venue']:
                if key in request.json:
                    concerts[index][key] = request.json[key]
            if 'date' in request.json:
                concerts[index]['date'] = datetime.fromisoformat(request.json['date'])

            return '', 204
        else:
            return jsonify({'error': 'Resource not found'}), 404
    else:
        return jsonify({'error': 'Incorrect Content-Type'}), 400


@app.route('/concerts', methods=['DELETE'])
def del_concerts():
    """
    :return: An error message and HTTP status 405
    """
    return jsonify({'error': 'Method Not Allowed'}), 405


@app.route('/concerts/<int:identity>', methods=['DELETE'])
def del_concerts_id(identity):
    """
    :param identity: Id of a concert
    :return: If identity is found, delete the concert and return the deleted concert content and an HTTP status 200
             else return an error message and HTTP status 404
    """
    global concerts
    global concerts_key

    index = content_index(concerts, 'id', identity)
    if index:
        concert_temp = [concerts[index]]
        concert_temp = encode_date(concert_temp, 'date')

        del concerts[index]

        return jsonify(concert_temp[0]), 200
    else:
        return jsonify({'error': 'Resource not found'}), 404


if __name__ == '__main__':
    app.run(port=8080, debug=True)