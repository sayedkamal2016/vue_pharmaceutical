import os
import jsonify
import json
import uuid
from datetime import datetime
from flask import Flask, request, g, abort, send_from_directory, send_file
from werkzeug.utils import secure_filename
from flask_cors import CORS, cross_origin
from mongoengine import *
connect(
    db="vue_inventory"
)
def new_drug_uid():
    return ("drg-"+str(uuid.uuid4()).replace('-','')).upper()
def new_stock_uid():
    return ("stk-"+str(uuid.uuid4()).replace('-','')).upper()
def new_transaction_uid():
    return ("trn-"+str(uuid.uuid4()).replace('-','')).upper()

class drug(Document):
    meta = {'collection': 'drugs'}
    drug_uid = StringField(required=True, max_length=50, default=new_drug_uid(), primary_key=True)
    name = StringField(required=True, max_length=250, unique=True)
    dosage = StringField(required=True, max_length=250)
    nafdac = StringField(required=True, max_length=10)


class stock(Document):
    meta = {'collection': 'stocks'}
    stock_uid = StringField(required=True, max_length=50, default=new_stock_uid(), primary_key=True)
    stock_item = StringField(required=True, max_length=50)
    total_qty = IntField(required=True)
    avail_qty = IntField(required=True)
    purchased = StringField(required=True,default=datetime.utcnow().strftime("%Y/%m/%d"))
    man_date = StringField(required=True)
    exp_date = StringField(required=True)
    cost_price = FloatField(required=True)
    selling_price = FloatField(required=True)
    availabilty = BooleanField(required=True, default=True)

class transaction_item(EmbeddedDocument):
    trans_item_uid = StringField(required=True, max_length=50)
    stock_uid = StringField(required=True, max_length=50)
    qty = IntField(required=True)
    cost = FloatField(required=True)
    sub_total = FloatField(required=True)

class transaction(Document):
    meta = {'collection': 'transactions'}
    trans_uid = StringField(required=True, max_length=50, default=new_transaction_uid(), primary_key=True)
    by = StringField(required=True, max_length=50)
    addr = StringField(required=True, max_length=50)
    items = ListField(EmbeddedDocumentField(transaction_item), default=list)
    total = FloatField(required=True)
    purchased = StringField(required=True,default=datetime.utcnow().strftime("%Y/%m/%d"))

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config["DEBUG"] = True
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
cors = CORS(app, support_credentials=True, resources=r'/*')


def allowed_image_ext(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/v1/drug/create', methods=['POST'])
def newDrug():
    new_drug = drug(
        drug_uid = new_drug_uid(),
        name = request.form['name'],
        dosage = request.form['dosage'],
        nafdac = request.form['nafdac']
    )
    new_drug.save()
    request_response = {'status': 'success','drug_id_created': str(new_drug.pk)}
    return json.dumps(request_response),201

@app.route('/api/v1/drug/find', methods=['GET'])
def findDrug():
    drug_name = request.args.get('drug_name')
    drug_id = request.args.get('drug_id')
    result_limit = request.args.get('result_limit')
    if result_limit:
        result_limit = int(result_limit)
    else:
        result_limit = 25

    if drug_name:
        try:
            print("drug_name: "+drug_name)
            selected_drug = drug.objects(name__icontains=drug_name).limit(result_limit)
            return selected_drug.to_json(), 200
        except DoesNotExist:
            err_res ={"message": "No such Drug!"}
            return json.dumps(err_res), 200

    elif drug_id:
        try:
            print("drug_id: "+drug_id)
            selected_drug = drug.objects(pk=drug_id).get()
            return selected_drug.to_json(), 200
        except DoesNotExist:
            err_res ={"message": "No such Drug!"}
            return json.dumps(err_res), 200
    else:
        try:
            selected_drug = drug.objects({}).limit(result_limit)
            return selected_drug.to_json(), 200
        except DoesNotExist:
            err_res ={"message": "No such Drug!"}
            return json.dumps(err_res), 200


@app.route('/api/v1/stock/create', methods=['POST'])
def newStock():
    incoming_request_data = request.form
    new_stock = stock(
        stock_uid = new_stock_uid(),
        stock_item = incoming_request_data['stock_item_uid'],
        total_qty = incoming_request_data['total_qty'],
        avail_qty = incoming_request_data['avail_qty'],
        man_date = incoming_request_data['man_date'],
        exp_date = incoming_request_data['exp_date'],
        cost_price = incoming_request_data['cost_price'],
        selling_price = incoming_request_data['selling_price']
    )
    new_stock.save()
    request_response = {'status': 'success','stock_id_created': str(new_stock.pk)}
    return json.dumps(request_response),201

@app.route('/api/v1/stock/find', methods=['GET'])
def findStock():
    purchased_date = request.args.get('purchased_date')
    stock_id = request.args.get('stock_id')
    stock_item_id = request.args.get('stock_item_id')
    result_limit = request.args.get('result_limit')
    if result_limit:
        result_limit = int(result_limit)
    else:
        result_limit = 25
    if purchased_date:
        try:
            selected_stock = stock.objects(purchased__gte=purchased_date).limit(result_limit)
            return selected_stock.to_json(), 200
        except DoesNotExist:
            err_res ={"message": "No such Stock!"}
            return json.dumps(err_res), 200
    elif stock_id:
        try:
            selected_stock = stock.objects(pk=stock_id)
            selected_stk = selected_stock.to_json()
            for i in selected_stk:
                for key in i:
                    if key=="exp_date" or key=="man_date" or key=="purchased":
                        print("key Matched: "+ key)
                        selected_stk[i][key] = datetime.utcfromtimestamp(i[key]['$date']*1000).strftime('%Y/%m/%d')

                    else:
                        print("no key Matched!")

            return json.dumps(selected_stk), 200
        except DoesNotExist:
            err_res ={"message": "No such Stock matching id"}
            return json.dumps(err_res), 200
    elif stock_item_id:
        try:
            selected_stock = stock.objects(stock_item=stock_item_id)
            return selected_stock.to_json(), 200
        except DoesNotExist:
            err_res ={"message": "No such Stock!"}
            return json.dumps(err_res), 200
    else:
        selected_stock = stock.objects({}).limit(result_limit)
        return selected_stock.to_json(), 200

@app.route('/api/v1/transaction/create', methods=['POST'])
def newTransaction():
    incoming_request_data = request.get_json()
    new_trans_total = 0
    new_trans_qty = 0
    new_trans = transaction(
        trans_uid = new_transaction_uid(),
        total = 0,
        qty = 0,
        cost = 0.0
    )
    new_trans.save()
    for item in incoming_request_data['items']:
        trans_item = transaction_item(
        trans_item_uid = item['uid'],
        qty = item['qty'],
        cost = item['cost'],
        sub_total = item['qty']*item['cost']
        )
        new_trans_total += item['qty']*item['cost']
        new_trans_qty += item['qty']
        new_trans.items.append(trans_item)
        new_trans.save()
        request_response = {'status': 'success','trans_id_created': str(new_trans.pk)}
        return json.dumps(request_response),201

@app.route('/api/v1/transaction/find', methods=['GET'])
def findTransaction():
    purchased_date = request.args.get('purchased_date')
    if purchased_date:
        selected_trans = transaction.objects(purchased__gte=purchased_date).get()
        return selected_trans.to_json(), 200
    else:
        selected_trans = transaction.objects({}).get()
        return selected_trans.to_json(), 200


@app.route("/api/v1/get_image/<image_name>",  methods=['GET','POST'])
def serveDrugImage(image_name):
    try:
        return send_from_directory(target, filename=image_name, as_attachment=True)
    except FileNotFoundError:
        abort(404)

if __name__ =='__main__':
    app.run()
