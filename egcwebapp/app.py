from flask import Flask, render_template, request, redirect, \
                  url_for, abort, jsonify
from egcwebapp.forms import DocumentForm, ExtractForm, UnitForm, \
                            AttributeForm
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

  previous_page = request.args.get('previous_page')
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
    if previous_page:
      return redirect(url_for(previous_page))
    else:
      return redirect(url_for('extract_list'))
  return render_template('edit_extract.html', form=form,
           egc_data=egc_data, errors=form.errors,
           previous_page=previous_page)

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

@app.route('/units')
def unit_list():
    if egc_data is None:
        return redirect(url_for('load_egc_file'))
    else:
        units = egc_data.get_records('U')
        return render_template('unit_list.html', units=units, egc_data=egc_data)

@app.route('/units/create', methods=['GET', 'POST'])
def create_unit():
    if egc_data is None:
        return redirect(url_for('load_egc_file'))
    else:
        form = UnitForm(request.form, egc_data=egc_data)
        if request.method == 'POST' and form.validate():
            new_record = {
                "record_type": "U",
                "id": form.id.data,
                "type": form.type.data,
                "definition": form.definition.data,
                "symbol": form.symbol.data,
                "description": form.description.data
            }
            egc_data.create_record(new_record)
            return redirect(url_for('unit_list'))
        return render_template('create_unit.html', form=form, errors=form.errors, egc_data=egc_data)

@app.route('/units/<record_id>/edit', methods=['GET', 'POST'])
def edit_unit(record_id):
    if egc_data is None:
        return redirect(url_for('load_egc_file'))
    else:
        unit = egc_data.get_record_by_id(record_id)
        if unit is None:
            abort(404)

    previous_page = request.args.get('previous_page')
    form = UnitForm(request.form, egc_data=egc_data, old_id=record_id, data={
        "id": unit["id"],
        "type": unit["type"],
        "definition": unit["definition"],
        "symbol": unit["symbol"],
        "description": unit["description"]
    })

    if request.method == 'POST' and form.validate():
        updated_data = {
            "record_type": "U",
            "id": form.id.data,
            "type": form.type.data,
            "definition": form.definition.data,
            "symbol": form.symbol.data,
            "description": form.description.data
        }
        egc_data.update_record_by_id(record_id, updated_data)
        if previous_page:
          return redirect(url_for(previous_page))
        else:
          return redirect(url_for('unit_list'))

    return render_template('edit_unit.html', form=form, egc_data=egc_data,
        errors=form.errors, previous_page=previous_page)

@app.route('/units/<record_id>/delete', methods=['POST'])
def delete_unit(record_id):
    if egc_data is None:
        return redirect(url_for('load_egc_file'))
    else:
        previous_page = request.args.get('previous_page')
        egc_data.delete_record_by_id(record_id)
        if previous_page:
            return redirect(url_for(previous_page))
        else:
            return redirect(url_for('unit_list'))

@app.route('/api/json/units/<record_id>', methods=['GET'])
def get_unit_json(record_id):
    if egc_data is None:
        return redirect(url_for('load_egc_file'))
    else:
        unit = egc_data.get_record_by_id(record_id)
        if unit is None:
            return jsonify({ "error": "Unit not found" }), 404
        else:
            return jsonify(unit)

@app.route('/units/<record_id>')
def show_unit(record_id):
  if egc_data is None:
    return redirect(url_for('load_egc_file'))
  else:
    unit = egc_data.get_record_by_id(record_id)
    if unit is None:
        abort(404)
    return render_template('show_unit.html', unit=unit,
        egc_data=egc_data)

@app.route('/api/units/<record_id>', methods=['GET'])
def get_unit(record_id):
    if egc_data is None:
        return redirect(url_for('load_egc_file'))
    else:
        unit = egc_data.get_record_by_id(record_id)
        if unit is None:
            return render_template('error.html', message='Unit not found')
        else:
            return render_template('table_show_unit.html', unit=unit, egc_data=egc_data)

@app.route('/api/units/<record_id>/attributes', methods=['GET'])
def get_unit_attributes(record_id):
    if egc_data is None:
        return redirect(url_for('load_egc_file'))
    else:
        attributes = egc_data.ref_by('U', record_id, 'A')
        return render_template('attribute_sub_list.html', attributes=attributes,
            egc_data=egc_data, parent_id=record_id)

@app.route('/api/json/units/<record_id>/attributes', methods=['GET'])
def get_unit_attributes_json(record_id):
    if egc_data is None:
        return redirect(url_for('load_egc_file'))
    else:
        attributes = egc_data.ref_by('U', record_id, 'A')
        return jsonify(attributes)

@app.route('/attributes')
def attribute_list():
    if egc_data is None:
        return redirect(url_for('load_egc_file'))
    else:
        attributes = egc_data.get_records('A')
        return render_template('attribute_list.html',
            attributes=attributes, egc_data=egc_data)

def attribute_from_form(form):
  record_data = {
      "record_type": "A",
      "id": form.id.data,
      "unit_id": form.unit_id.data,
  }
  if form.mode_type.data == "measurement_mode_simple":
      record_data["mode"] = form.mode.data
  elif form.mode_type.data == "measurement_mode_relative":
      record_data["mode"] = {
          "mode": form.mode.data,
          "reference": form.reference.data,
      }
  elif form.mode_type.data == "measurement_mode_w_location":
      record_data["mode"] = {
          "mode": form.mode.data,
          "location_type": form.location_type.data,
          "location_label": form.location_label.data,
      }
  elif form.mode_type.data == "measurement_mode_relative_w_location":
      record_data["mode"] = {
          "mode": form.mode.data,
          "reference": form.reference.data,
          "location_type": form.location_type.data,
          "location_label": form.location_label.data,
      }
  return record_data

def form_data_from_attribute(attribute):
  attribute_data={
    "id": attribute["id"],
    "unit_id": attribute["unit_id"],
    "mode_type": "measurement_mode_simple",
  }
  if isinstance(attribute["mode"], dict):
    attribute_data["mode"] = attribute["mode"]["mode"]
    if "reference" in attribute["mode"]:
      attribute_data["reference"] = attribute["mode"]["reference"]
      attribute_data["mode_type"] = "measurement_mode_relative"
    if "location_type" in attribute["mode"]:
      attribute_data["location_type"] = attribute["mode"]["location_type"]
      if attribute_data["mode_type"] == "measurement_mode_relative":
        attribute_data["mode_type"] = "measurement_mode_relative_w_location"
      else:
        attribute_data["mode_type"] = "measurement_mode_w_location"
    if "location_label" in attribute["mode"]:
      attribute_data["location_label"] = attribute["mode"]["location_label"]
  else:
    attribute_data["mode"] = attribute["mode"]
  return attribute_data

@app.route('/attributes/create', methods=['GET', 'POST'])
def create_attribute():
    if egc_data is None:
        return redirect(url_for('load_egc_file'))
    else:
        form = AttributeForm(request.form, egc_data=egc_data)
        if request.method == 'POST' and form.validate():
            new_record = attribute_from_form(form)
            egc_data.create_record(new_record)
            return redirect(url_for('attribute_list'))
        return render_template('create_attribute.html', form=form,
            errors=form.errors, egc_data=egc_data)

@app.route('/attributes/<record_id>/edit', methods=['GET', 'POST'])
def edit_attribute(record_id):
    if egc_data is None:
        return redirect(url_for('load_egc_file'))
    else:
        attribute = egc_data.get_record_by_id(record_id)
        if attribute is None:
            abort(404)

    attribute_data = form_data_from_attribute(attribute)
    form = AttributeForm(request.form, egc_data=egc_data, old_id=record_id,
        data=attribute_data)

    if request.method == 'POST' and form.validate():
        updated_data = attribute_from_form(form)
        egc_data.update_record_by_id(record_id, updated_data)
        return redirect(url_for('attribute_list'))

    return render_template('edit_attribute.html', form=form, egc_data=egc_data,
                           errors=form.errors)

@app.route('/attributes/<record_id>/delete', methods=['POST'])
def delete_attribute(record_id):
    if egc_data is None:
        return redirect(url_for('load_egc_file'))
    else:
        egc_data.delete_record_by_id(record_id)
        return redirect(url_for('attribute_list'))

@app.route('/api/json/attributes/<record_id>', methods=['GET'])
def get_attribute_json(record_id):
    if egc_data is None:
        return redirect(url_for('load_egc_file'))
    else:
        attribute = egc_data.get_record_by_id(record_id)
        if attribute is None:
            return jsonify({"error": "Attribute not found"}), 404
        else:
            return jsonify(attribute)

@app.route('/api/attributes/<record_id>', methods=['GET'])
def get_attribute(record_id):
    if egc_data is None:
        return redirect(url_for('load_egc_file'))
    else:
        attribute = egc_data.get_record_by_id(record_id)
        if attribute is None:
            return render_template('error.html', message='Attribute not found')
        else:
            return render_template('table_show_attribute.html',
                attribute=attribute, egc_data=egc_data)

@app.route('/groups')
def group_list():
    if egc_data is None:
        return redirect(url_for('load_egc_file'))
    else:
        groups = egc_data.get_records('G')
        return render_template('group_list.html', groups=groups, egc_data=egc_data)

@app.route('/groups/create', methods=['GET', 'POST'])
def create_group():
    if egc_data is None:
        return redirect(url_for('load_egc_file'))
    else:
        form = GroupForm(request.form, egc_data=egc_data)
        if request.method == 'POST' and form.validate():
            new_record = {
                "record_type": "G",
                "id": form.id.data,
                "name": form.name.data,
                "type": form.type.data,
                "definition": form.definition.data,
                "tags": form.tags.data
            }
            egc_data.create_record(new_record)
            return redirect(url_for('group_list'))
        return render_template('create_group.html', form=form, errors=form.errors, egc_data=egc_data)

@app.route('/groups/<record_id>/edit', methods=['GET', 'POST'])
def edit_group(record_id):
    if egc_data is None:
        return redirect(url_for('load_egc_file'))
    else:
        group = egc_data.get_record_by_id(record_id)
        if group is None:
            abort(404)

    group_data = {
        "id": group["id"],
        "name": group["name"],
        "type": group["type"],
        "definition": group["definition"],
        "tags": group["tags"]
    }
    
    form = GroupForm(request.form, egc_data=egc_data, old_id=record_id,
        data=group_data)

    if request.method == 'POST' and form.validate():
        updated_data = {
            "record_type": "G",
            "id": form.id.data,
            "name": form.name.data,
            "type": form.type.data,
            "definition": form.definition.data,
            "tags": form.tags.data
        }
        egc_data.update_record_by_id(record_id, updated_data)
        return redirect(url_for('group_list'))

    return render_template('edit_group.html', form=form, egc_data=egc_data, errors=form.errors)

@app.route('/groups/<record_id>/delete', methods=['POST'])
def delete_group(record_id):
    if egc_data is None:
        return redirect(url_for('load_egc_file'))
    else:
        egc_data.delete_record_by_id(record_id)
        return redirect(url_for('group_list'))

@app.route('/api/json/groups/<record_id>', methods=['GET'])
def get_group_json(record_id):
    if egc_data is None:
        return redirect(url_for('load_egc_file'))
    else:
        group = egc_data.get_record_by_id(record_id)
        if group is None:
            return jsonify({"error": "Group not found"}), 404
        else:
            return jsonify(group)

@app.route('/api/groups/<record_id>', methods=['GET'])
def get_group(record_id):
    if egc_data is None:
        return redirect(url_for('load_egc_file'))
    else:
        group = egc_data.get_record_by_id(record_id)
        if group is None:
            return render_template('error.html', message='Group not found')
        else:
            return render_template('table_show_group.html',
                group=group, egc_data=egc_data)


if __name__ == '__main__':
  app.run()
