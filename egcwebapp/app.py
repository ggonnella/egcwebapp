from flask import Flask, render_template, request, redirect, \
                  url_for, abort, jsonify
from egcwebapp.forms import DocumentForm, ExtractForm
from egctools.egcdata import EGCData
from pathlib import Path
import os

app = Flask(__name__)
egc_data = None
app.secret_key = 'secret_key'
app.config['UPLOAD_FOLDER'] = str(Path(app.instance_path) / 'uploads')
if os.environ.get('EGCWEBAPP') == 'development':
  app.debug = True
  this_dir = Path(__file__).parent
  egc_data = EGCData.from_file(str(this_dir.parent / "archaea.egc"))

# The following web routes are defined for each type of record:
#
# /<record_type>s                       table of all records of a given type
# C /<record_type>s/create              form to create a new record
# R /<record_type>s/<record_id>         page showing a single record
# U /<record_type>s/<record_id>/edit    page for editing a single record
# D /<record_type>s/<record_id>/delete  deletes a single record
#
# Furthermore, the following API routes are defined. The /api/json/<> routes
# return JSON data, while the /api/<> routes return HTML tables.
#
# /api/<record_type>s/<record_id>                        single record
# /api/<record_type>s/<record_id>/<ref_by_record_type>
#                     record from which the given record is referenced
# /api/json/<record_type>s/<record_id>                   single record
# /api/json/<record_type>s/<record_id>/<ref_by_record_type>
#                     record from which the given record is referenced

@app.route('/')
def index():
    return redirect(url_for('document_list'))

@app.route('/load_egc_file', methods=['GET', 'POST'])
def load_egc_file():
    global egc_data
    if request.method == 'POST':
        file = request.files['file']
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        egc_data = EGCData.from_file(file_path)
        return redirect(url_for('document_list'))
    return render_template('load_egc_file.html')

@app.route('/documents')
def document_list():
  if egc_data is None:
    return redirect(url_for('load_egc_file'))
  else:
    documents = egc_data.get_records('D')
    return render_template('document_list.html', documents=documents,
        egc_data=egc_data)

@app.route('/documents/create', methods=['GET', 'POST'])
def create_document():
  if egc_data is None:
    return redirect(url_for('load_egc_file'))
  else:
    form = DocumentForm(request.form, egc_data=egc_data)
    if request.method == 'POST' and form.validate():
        new_document = {
            "record_type": "D",
            "document_id": {
                "resource_prefix": "PMID",
                "item": form.document_id.data,
                "location": None,
                "term": None
            },
            "link": form.link.data
        }
        egc_data.create_record(new_document)
        return redirect(url_for('document_list'))
    return render_template('create_document.html', form=form,
        errors=form.errors, egc_data=egc_data)

@app.route('/documents/<record_id>/edit', methods=['GET', 'POST'])
def edit_document(record_id):
  if egc_data is None:
    return redirect(url_for('load_egc_file'))
  else:
    previous_page = request.args.get('previous_page')
    document = egc_data.get_record_by_id(record_id)
    if document is None:
        abort(404)
    form = DocumentForm(request.form,
        egc_data=egc_data, old_id = record_id,
        data={"document_id": document["document_id"]["item"],
              "link": document["link"]})
    if request.method == 'POST' and form.validate():
        updated_document = {
            "record_type": "D",
            "document_id": {
                "resource_prefix": "PMID",
                "item": form.document_id.data,
                "location": None,
                "term": None
            },
            "link": form.link.data
        }
        egc_data.update_record_by_id(record_id, updated_document)
        if previous_page:
          return redirect(url_for(previous_page))
        else:
          return redirect(url_for('document_list'))
    return render_template('edit_document.html', form=form,
        errors=form.errors, previous_page=previous_page,
        egc_data=egc_data)

@app.route('/documents/<record_id>/delete', methods=['POST'])
def delete_document(record_id):
  if egc_data is None:
    return redirect(url_for('load_egc_file'))
  else:
    previous_page = request.args.get('previous_page')
    egc_data.delete_record_by_id(record_id)
    if previous_page:
      return redirect(url_for(previous_page))
    else:
      return redirect(url_for('document_list'))

@app.route('/documents/<record_id>')
def show_document(record_id):
  if egc_data is None:
    return redirect(url_for('load_egc_file'))
  else:
    document = egc_data.get_record_by_id(record_id)
    if document is None:
        abort(404)
    return render_template('show_document.html', document=document,
        egc_data=egc_data)

@app.route('/api/json/documents/<record_id>', methods=['GET'])
def get_document_json(record_id):
  if egc_data is None:
    return redirect(url_for('load_egc_file'))
  else:
    document = egc_data.get_record_by_id(record_id)
    return jsonify(document)

@app.route('/api/documents/<record_id>', methods=['GET'])
def get_document(record_id):
  if egc_data is None:
    return redirect(url_for('load_egc_file'))
  else:
    document = egc_data.get_record_by_id(record_id)
    return render_template('table_show_document.html', document=document,
            egc_data=egc_data)

@app.route('/api/json/documents/<record_id>/extracts', methods=['GET'])
def get_document_extracts_json(record_id):
  if egc_data is None:
    return redirect(url_for('load_egc_file'))
  else:
    extracts = egc_data.ref_by('D', record_id, 'S') + \
               egc_data.ref_by('D', record_id, 'T')
    return jsonify(extracts)

@app.route('/api/documents/<record_id>/extracts', methods=['GET'])
def get_document_extracts(record_id):
  if egc_data is None:
    return redirect(url_for('load_egc_file'))
  else:
    extracts = egc_data.ref_by('D', record_id, 'S') + \
               egc_data.ref_by('D', record_id, 'T')
    return render_template('extract_sub_list.html', extracts=extracts,
        egc_data=egc_data, parent_id=record_id)

@app.route('/extracts')
def extract_list():
  if egc_data is None:
    return redirect(url_for('load_egc_file'))
  else:
    extracts = egc_data.get_records('S') + egc_data.get_records('T')
    return render_template('extract_list.html', extracts=extracts,
        egc_data=egc_data)

@app.route('/extracts/create', methods=['GET', 'POST'])
def create_extract():
  if egc_data is None:
    return redirect(url_for('load_egc_file'))
  else:
    form = ExtractForm(request.form, egc_data=egc_data)
    if request.method == 'POST' and form.validate():
        new_record = {
            "record_type": form.record_type.data,
            "id": form.id.data,
            "document_id": {
                "resource_prefix": "PMID",
                "item": form.document_id.data,
                "location": None,
                "term": None
            }
        }
        if form.record_type.data == "T":
            new_record["table_ref"] = form.contents.data
        elif form.record_type.data == "S":
            new_record["text"] = form.contents.data
        egc_data.create_record(new_record)
        return redirect(url_for('extract_list'))
    return render_template('create_extract.html', form=form,
        errors=form.errors, egc_data=egc_data)

@app.route('/extracts/<record_id>/edit', methods=['GET', 'POST'])
def edit_extract(record_id):
  if egc_data is None:
    return redirect(url_for('load_egc_file'))
  else:
    extract = egc_data.get_record_by_id(record_id)
    if extract is None:
        abort(404)

  if extract["record_type"] == "T":
      contents = extract["table_ref"]
  elif extract["record_type"] == "S":
      contents = extract["text"]
  form = ExtractForm(request.form,
        egc_data=egc_data, old_id = record_id,
        data={
          "id": extract["id"],
          "record_type": extract["record_type"],
          "document_id": extract["document_id"]["item"],
          "contents": contents,
        })
  if request.method == 'POST' and form.validate():
    updated_data = {
        "record_type": form.record_type.data,
        "id": form.id.data,
        "document_id": {
            "resource_prefix": "PMID",
            "item": form.document_id.data,
            "location": None,
            "term": None
        }}
    if form.record_type.data == "T":
        updated_data["table_ref"] = form.contents.data
    elif form.record_type.data == "S":
        updated_data["text"] = form.contents.data
    egc_data.update_record_by_id(record_id, updated_data)
    return redirect(url_for('extract_list'))
  return render_template('edit_extract.html', form=form,
           egc_data=egc_data)

@app.route('/extracts/<record_id>/delete', methods=['POST'])
def delete_extract(record_id):
  if egc_data is None:
    return redirect(url_for('load_egc_file'))
  else:
    previous_page = request.args.get('previous_page')
    egc_data.delete_record_by_id(record_id)
    if previous_page:
      return redirect(url_for(previous_page))
    else:
      return redirect(url_for('extract_list'))

if __name__ == '__main__':
  app.run()
