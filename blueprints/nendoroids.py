from flask import Blueprint, jsonify, request
from controllers import FirestoreIO
import requests
from bs4 import BeautifulSoup

collection = 'nendoroids'

nendoroids_bp = Blueprint(collection, __name__)


@nendoroids_bp.route('')
def list():
    firestore_io = FirestoreIO()
    return jsonify(firestore_io.list(collection))


@nendoroids_bp.route('search')
def search():
    query = request.args['q']
    firestore_io = FirestoreIO()
    sorted = []
    all_nendoroids = firestore_io.list(collection)
    for n in all_nendoroids:
        if query.lower() in n['id'] or query.lower() in n['name'].lower():
            sorted.append(n)
    return jsonify(sorted)


@nendoroids_bp.route('/<doc_id>', methods=['PATCH'])
def patch(doc_id):
    firestore_io = FirestoreIO()
    return jsonify(firestore_io.update(collection, doc_id, request.get_json()))


@nendoroids_bp.route('/owned', methods=['GET'])
def get_owned():
    firestore_io = FirestoreIO()
    return jsonify(firestore_io.search(collection, 'owned', True))


@nendoroids_bp.route('/update')
def update():
    nendoroid_list = scrap_for_nendoroids()
    firestore_io = FirestoreIO()
    for n in nendoroid_list:
        doc = firestore_io.get(collection, n['id'])
        if not doc:
            firestore_io.insert(collection, n, n['id'])
            print(f"Added Nendoroid {n['id']} - {n['name']}")
        else:
            print(f"Nendoroid {n['id']} - {n['name']} already exists")
    return "done"


def scrap_for_nendoroids():
    pages = []
    r = requests.get('https://www.goodsmile.info/en/nendoroid000-100')
    soup = BeautifulSoup(r.text, 'html.parser')
    select_pages = soup.find(id='nendoroid_no')
    nendoroid_list = []
    for nc in select_pages.children:
        if nc == '\n':
            continue
        if 'value' not in nc.attrs:
            continue
        pages.append(nc.attrs['value'].replace('/en/nendoroid', ''))
    for p in pages:
        r = requests.get(f'https://www.goodsmile.info/en/nendoroid{p}')
        soup = BeautifulSoup(r.text, 'html.parser')
        nendoroids_cards = soup.findAll("div", {"class": "hitBox"})
        for nc in nendoroids_cards:
            link = nc.contents[1]
            nendoroid = {
                'link': link.attrs['href'],
                'owned': False
            }

            text = nc.text.replace('\n\n\n\n', '').split('\n\n')
            nendoroid['name'] = text[0]
            nendoroid['id'] = text[1].replace('\n', '').replace(' ', '')

            for c in link.children:
                if c == '\n':
                    continue
                if c.name == 'img':
                    nendoroid['img'] = f"https:{c.attrs['data-original']}"
                    break

            nendoroid_list.append(nendoroid)
    return nendoroid_list