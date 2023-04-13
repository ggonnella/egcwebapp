from flask import Flask, render_template, request, redirect, \
                  url_for, abort, jsonify, send_from_directory
from egcwebapp.forms import DocumentForm, ExtractForm, UnitForm, \
                            AttributeForm, GroupForm, ModelForm, \
                            VruleForm, CruleForm
from egctools.egcdata import EGCData
from pathlib import Path
import os
import functools
from flask_navigation import Navigation

app = Flask(__name__)
nav = Navigation(app)
nav.Bar('top', [
    nav.Item('Load', 'load_egc_file'),
    nav.Item('Save', 'save_egc_file'),
    nav.Item('Documents', 'document_list'),
    nav.Item('Extracts', 'extract_list'),
    nav.Item('Groups', 'group_list'),
    nav.Item('Units', 'unit_list'),
    nav.Item('Models', 'model_list'),
    nav.Item('Attributes', 'attribute_list'),
    nav.Item('Value Exp.', 'vrule_list'),
    nav.Item('Comp. Exp.', 'crule_list'),
])
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

def require_egc_data(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if egc_data is None:
            return redirect(url_for('load_egc_file'))
        else:
            return func(*args, **kwargs)
    return wrapper

@app.route('/save_egc_file')
@require_egc_data
def save_egc_file():
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        os.path.basename(egc_data.file_path),
        mimetype='application/egc')

@app.route('/documents')
@require_egc_data
def document_list():
  documents = egc_data.get_records('D')
  return render_template('list_document.html', documents=documents,
      egc_data=egc_data)

@app.route('/extracts')
@require_egc_data
def extract_list():
  extracts = egc_data.get_records('S') + egc_data.get_records('T')
  return render_template('list_extract.html', extracts=extracts,
      egc_data=egc_data)

@app.route('/units')
@require_egc_data
def unit_list():
  units = egc_data.get_records('U')
  return render_template('list_unit.html', units=units, egc_data=egc_data)

@app.route('/attributes')
@require_egc_data
def attribute_list():
  attributes = egc_data.get_records('A')
  return render_template('list_attribute.html',
      attributes=attributes, egc_data=egc_data)

@app.route('/groups')
@require_egc_data
def group_list():
  groups = egc_data.get_records('G')
  return render_template('list_group.html', groups=groups, egc_data=egc_data)

@app.route('/models')
@require_egc_data
def model_list():
  models = egc_data.get_records('M')
  return render_template('list_model.html', models=models, egc_data=egc_data)

@app.route('/vrules')
@require_egc_data
def vrule_list():
  vrules = egc_data.get_records('V')
  return render_template('list_vrule.html', vrules=vrules, egc_data=egc_data)

@app.route('/crules')
@require_egc_data
def crule_list():
  crules = egc_data.get_records('C')
  return render_template('list_crule.html', crules=crules, egc_data=egc_data)

def add_tags_from_form_data(form_data, record):
  record["tags"] = {}
  for tag in form_data.tags.data:
    if tag != '' and tag["tagname"] != '':
      record["tags"][tag["tagname"]] = \
          {"value": tag["tagvalue"], "type": tag["tagtype"]}
  if len(record["tags"]) == 0:
    del record["tags"]
  if len(form_data.comment.data) > 0:
    record["comment"] = form_data.comment.data

def add_document_id_from_form(form, record_data):
  record_data["document_id"] = {
      "resource_prefix": "PMID",
      "item": form.document_id.data,
      "location": None,
      "term": None
  }

def document_from_form(form):
  record_data = {
      "record_type": "D",
      "link": form.link.data
  }
  add_document_id_from_form(form, record_data)
  add_tags_from_form_data(form, record_data)
  return record_data

def extract_from_form(form):
  record_data = {
      "record_type": form.record_type.data,
      "id": form.id.data,
  }
  add_document_id_from_form(form, record_data)
  if form.record_type.data == "T":
      record_data["table_ref"] = form.contents.data
  elif form.record_type.data == "S":
      record_data["text"] = form.contents.data
  add_tags_from_form_data(form, record_data)
  return record_data

def unit_from_form(form):
  record_data = {
      "record_type": "U",
      "id": form.id.data,
      "type": form.type.data,
      "definition": form.definition.data,
      "symbol": form.symbol.data,
      "description": form.description.data
  }
  add_tags_from_form_data(form, record_data)
  return record_data

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
  add_tags_from_form_data(form, record_data)
  return record_data

def group_from_form(form):
  record_data = {
      "record_type": "G",
      "id": form.id.data,
      "type": form.type.data,
      "definition": form.definition.data,
      "description": form.description.data
  }
  add_tags_from_form_data(form, record_data)
  return record_data

def model_from_form(form):
  record_data = {
      "record_type": "M",
      "unit_id": form.unit_id.data,
      "resource_id": form.resource_id.data,
      "model_id": form.model_id.data,
      "model_name": form.model_name.data,
  }
  add_tags_from_form_data(form, record_data)
  return record_data

def vrule_from_form(form):
  record_data = {
      "record_type": "V",
      "id": form.id.data,
      "attribute": form.attribute.data,
      "group": {"id": form.group.data},
      "operator": form.operator.data,
      "reference": form.reference.data,
  }
  if len(form.sources.data) > 1:
    record_data["source"] = [s["source_id"] for s in form.sources.data]
  else:
    record_data["source"] = form.sources.data[0]["source_id"]
  if form.group_portion.data:
    record_data["group"]["portion"] = form.group_portion.data
  add_tags_from_form_data(form, record_data)
  return record_data

def crule_from_form(form):
  record_data = {
      "record_type": "C",
      "id": form.id.data,
      "group1": {"id": form.group1.data},
      "operator": form.operator.data,
      "group2": {"id": form.group2.data},
  }
  if len(form.sources.data) > 1:
    record_data["source"] = [s["source_id"] for s in form.sources.data]
  else:
    record_data["source"] = form.sources.data[0]["source_id"]
  if form.vs_attribute.data:
    record_data["attribute"] = {"id1": form.attribute.data,
                                "id2": form.vs_attribute.data}
  else:
    record_data["attribute"] = form.attribute.data
  if form.group1_portion.data:
    record_data["group1"]["portion"] = form.group1_portion.data
  if form.group2_portion.data:
    record_data["group2"]["portion"] = form.group2_portion.data
  add_tags_from_form_data(form, record_data)
  return record_data

@app.route('/documents/create', methods=['GET', 'POST'])
@require_egc_data
def create_document():
  form = DocumentForm(request.form, egc_data=egc_data)
  if request.method == 'POST' and form.validate():
    new_document = document_from_form(form)
    egc_data.create_record(new_document)
    return redirect(url_for('document_list'))
  return render_template('record_form.html', form=form,
      errors=form.errors, egc_data=egc_data, title_label="Create Document")

@app.route('/extracts/create', methods=['GET', 'POST'])
@require_egc_data
def create_extract():
  form = ExtractForm(request.form, egc_data=egc_data)
  if request.method == 'POST' and form.validate():
      new_record = extract_from_form(form)
      egc_data.create_record(new_record)
      return redirect(url_for('extract_list'))
  return render_template('record_form.html', form=form,
      errors=form.errors, egc_data=egc_data,
      title_label="Create Document Extract")

@app.route('/units/create', methods=['GET', 'POST'])
@require_egc_data
def create_unit():
  form = UnitForm(request.form, egc_data=egc_data)
  if request.method == 'POST' and form.validate():
      new_record = unit_from_form(form)
      egc_data.create_record(new_record)
      return redirect(url_for('unit_list'))
  return render_template('record_form.html', form=form, errors=form.errors,
      egc_data=egc_data, title_label="Create Unit")

@app.route('/attributes/create', methods=['GET', 'POST'])
@require_egc_data
def create_attribute():
  form = AttributeForm(request.form, egc_data=egc_data)
  if request.method == 'POST' and form.validate():
      new_record = attribute_from_form(form)
      egc_data.create_record(new_record)
      return redirect(url_for('attribute_list'))
  return render_template('record_form.html', form=form,
      errors=form.errors, egc_data=egc_data, title_label="Create Attribute")

@app.route('/groups/create', methods=['GET', 'POST'])
@require_egc_data
def create_group():
  form = GroupForm(request.form, egc_data=egc_data)
  if request.method == 'POST' and form.validate():
      new_record = group_from_form(form)
      egc_data.create_record(new_record)
      return redirect(url_for('group_list'))
  return render_template('record_form.html', form=form,
      errors=form.errors, egc_data=egc_data, title_label="Create Group")

@app.route('/models/create', methods=['GET', 'POST'])
@require_egc_data
def create_model():
  form = ModelForm(request.form, egc_data=egc_data)
  if request.method == 'POST' and form.validate():
      new_record = model_from_form(form)
      egc_data.create_record(new_record)
      return redirect(url_for('model_list'))
  return render_template('record_form.html', form=form,
      errors=form.errors, egc_data=egc_data, title_label="Create Model")

@app.route('/vrules/create', methods=['GET', 'POST'])
@require_egc_data
def create_vrule():
  form = VruleForm(request.form, egc_data=egc_data)
  if request.method == 'POST' and form.validate():
      new_record = vrule_from_form(form)
      egc_data.create_record(new_record)
      return redirect(url_for('vrule_list'))
  return render_template('record_form.html', form=form,
      errors=form.errors, egc_data=egc_data,
      title_label="Create Value Expectation Rule")

@app.route('/crules/create', methods=['GET', 'POST'])
@require_egc_data
def create_crule():
  form = CruleForm(request.form, egc_data=egc_data)
  if request.method == 'POST' and form.validate():
      new_record = crule_from_form(form)
      egc_data.create_record(new_record)
      return redirect(url_for('crule_list'))
  return render_template('record_form.html', form=form,
      errors=form.errors, egc_data=egc_data,
      title_label="Create Comparative Expectation Rule")

def add_tags_to_form_data(record, form_data):
  if "tags" in record:
    form_data["tags"] = []
    for tag_name, tag_type_value in record["tags"].items():
      form_data["tags"].append({
        "tagname": tag_name,
        "tagtype": tag_type_value["type"],
        "tagvalue": tag_type_value["value"]
      })
  if "comment" in record and record["comment"]:
    form_data["comment"] = record["comment"]

def document_to_form(document):
  data={"document_id": document["document_id"]["item"],
        "link": document["link"]}
  add_tags_to_form_data(document, data)
  return data

@app.route('/documents/<record_id>/edit', methods=['GET', 'POST'])
@require_egc_data
def edit_document(record_id):
    previous_page = request.args.get('previous_page') or 'document_list'
    document = egc_data.get_record_by_id(record_id) or abort(404)
    form = DocumentForm(request.form,
        egc_data=egc_data, old_id = record_id, data=document_to_form(document))
    if request.method == 'POST' and form.validate():
        egc_data.update_record_by_id(record_id, document_from_form(form))
        return redirect(url_for(previous_page))
    return render_template('record_form.html', form=form,
        errors=form.errors, previous_page=previous_page,
        egc_data=egc_data, title_label="Edit Document")

def extract_to_form(extract):
  if extract["record_type"] == "T":
      contents = extract["table_ref"]
  elif extract["record_type"] == "S":
      contents = extract["text"]
  form_data = {
          "id": extract["id"],
          "record_type": extract["record_type"],
          "document_id": extract["document_id"]["item"],
          "contents": contents,
        }
  add_tags_to_form_data(extract, form_data)
  return form_data

@app.route('/extracts/<record_id>/edit', methods=['GET', 'POST'])
@require_egc_data
def edit_extract(record_id):
  extract = egc_data.get_record_by_id(record_id) or abort(404)
  form = ExtractForm(request.form, egc_data=egc_data, old_id = record_id,
                     data=extract_to_form(extract))
  previous_page = request.args.get('previous_page') or 'extract_list'
  if request.method == 'POST' and form.validate():
    egc_data.update_record_by_id(record_id, extract_from_form(form))
    return redirect(url_for(previous_page))
  return render_template('record_form.html', form=form, egc_data=egc_data,
      errors=form.errors, previous_page=previous_page,
      title_label="Edit Extract")

def unit_to_form(unit):
  form_data = {
      "id": unit["id"],
      "type": unit["type"],
      "definition": unit["definition"],
      "symbol": unit["symbol"],
      "description": unit["description"]
  }
  add_tags_to_form_data(unit, form_data)
  return form_data

@app.route('/units/<record_id>/edit', methods=['GET', 'POST'])
@require_egc_data
def edit_unit(record_id):
  unit = egc_data.get_record_by_id(record_id) or abort(404)
  form = UnitForm(request.form, egc_data=egc_data, old_id=record_id,
                  data=unit_to_form(unit))
  previous_page = request.args.get('previous_page') or 'unit_list'
  if request.method == 'POST' and form.validate():
      updated_data = unit_from_form(form)
      egc_data.update_record_by_id(record_id, updated_data)
      return redirect(url_for(previous_page))
  return render_template('record_form.html', form=form, egc_data=egc_data,
      errors=form.errors, previous_page=previous_page,
      title_label="Edit Unit")

def attribute_to_form(attribute):
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
  add_tags_to_form_data(attribute, attribute_data)
  return attribute_data

@app.route('/attributes/<record_id>/edit', methods=['GET', 'POST'])
@require_egc_data
def edit_attribute(record_id):
  attribute = egc_data.get_record_by_id(record_id) or abort(404)
  previous_page = request.args.get('previous_page') or 'attribute_list'
  form = AttributeForm(request.form, egc_data=egc_data, old_id=record_id,
      data=attribute_to_form(attribute))
  if request.method == 'POST' and form.validate():
      egc_data.update_record_by_id(record_id, attribute_from_form(form))
      return redirect(url_for(previous_page))
  return render_template('record_form.html', form=form, egc_data=egc_data,
                         errors=form.errors, previous_page=previous_page,
                         title_label="Edit Attribute")

def group_to_form(group):
  group_data = {
      "id": group["id"],
      "name": group["name"],
      "type": group["type"],
      "definition": group["definition"],
  }
  add_tags_to_form_data(group, group_data)
  return group_data

@app.route('/groups/<record_id>/edit', methods=['GET', 'POST'])
@require_egc_data
def edit_group(record_id):
  group = egc_data.get_record_by_id(record_id) or abort(404)
  previous_page = request.args.get('previous_page') or 'group_list'
  form = GroupForm(request.form, egc_data=egc_data, old_id=record_id,
      data=group_to_form(group))
  if request.method == 'POST' and form.validate():
      egc_data.update_record_by_id(record_id, group_from_form(form))
      return redirect(url_for(previous_page))
  return render_template('record_form.html', form=form, egc_data=egc_data,
                         errors=form.errors, previous_page=previous_page,
                         title_label="Edit Group")

def model_to_form(model):
  model_data = {
      "unit_id": model["unit_id"],
      "resource_id": model["resource_id"],
      "model_id": model["model_id"],
      "mode_name": model["model_name"],
  }
  add_tags_to_form_data(model, model_data)
  return model_data

@app.route('/models/<record_id>/edit', methods=['GET', 'POST'])
@require_egc_data
def edit_model(record_id):
  model = egc_data.get_record_by_id(record_id) or abort(404)
  previous_page = request.args.get('previous_page') or 'model_list'
  form = ModelForm(request.form, egc_data=egc_data, old_id=record_id,
      data=model_to_form(model))
  if request.method == 'POST' and form.validate():
      egc_data.update_record_by_id(record_id, model_from_form(form))
      return redirect(url_for(previous_page))
  return render_template('record_form.html', form=form, egc_data=egc_data,
                         errors=form.errors, previous_page=previous_page,
                         title_label="Edit Model")

def vrule_to_form(record):
  record_data = {
    "id": record["id"],
    "attribute": record["attribute"],
    "group": record["group"]["id"],
    "operator": record["operator"],
    "reference": record["reference"],
  }
  if isinstance(record["source"], list):
    record_data["sources"] = [{"source_id": s} for s in record["source"]]
  else:
    record_data["sources"] = [{"source_id": record["source"]}]
  if "portion" in record["group"]:
    record_data["group_portion"] = record["group"]["portion"]
  add_tags_to_form_data(record, record_data)
  return record_data

@app.route('/vrules/<record_id>/edit', methods=['GET', 'POST'])
@require_egc_data
def edit_vrule(record_id):
  vrule = egc_data.get_record_by_id(record_id) or abort(404)
  previous_page = request.args.get('previous_page') or 'vrule_list'
  form = VruleForm(request.form, egc_data=egc_data, old_id=record_id,
      data=vrule_to_form(vrule))
  if request.method == 'POST' and form.validate():
      egc_data.update_record_by_id(record_id, vrule_from_form(form))
      return redirect(url_for(previous_page))
  return render_template('record_form.html', form=form, egc_data=egc_data,
                         errors=form.errors, previous_page=previous_page,
                         title_label="Edit Value Expectation Rule")

def crule_to_form(record):
  record_data = {
    "id": record["id"],
    "group1": record["group1"]["id"],
    "operator": record["operator"],
    "group2": record["group2"]["id"],
  }
  if isinstance(record["source"], list):
    record_data["sources"] = [{"source_id": s} for s in record["source"]]
  else:
    record_data["sources"] = [{"source_id": record["source"]}]
  if isinstance(record["attribute"], dict):
    record_data["attribute"] = record["attribute"]["id1"]
    record_data["vs_attribute"] = record["attribute"]["id2"]
  else:
    record_data["attribute"] = record["attribute"]
    record_data["vs_attribute"] = None
  if "portion" in record["group1"]:
    record_data["group1_portion"] = record["group1"]["portion"]
  if "portion" in record["group2"]:
    record_data["group2_portion"] = record["group2"]["portion"]
  add_tags_to_form_data(record, record_data)
  return record_data

@app.route('/crules/<record_id>/edit', methods=['GET', 'POST'])
@require_egc_data
def edit_crule(record_id):
  crule = egc_data.get_record_by_id(record_id) or abort(404)
  previous_page = request.args.get('previous_page') or 'crule_list'
  form = CruleForm(request.form, egc_data=egc_data, old_id=record_id,
      data=crule_to_form(crule))
  if request.method == 'POST' and form.validate():
      egc_data.update_record_by_id(record_id, crule_from_form(form))
      return redirect(url_for(previous_page))
  return render_template('record_form.html', form=form, egc_data=egc_data,
                         errors=form.errors, previous_page=previous_page,
                         title_label="Edit Comparative Expectation Rule")

@app.route('/documents/<record_id>/delete', methods=['POST'])
@require_egc_data
def delete_document(record_id):
    egc_data.delete_record_by_id(record_id)
    previous_page = request.args.get('previous_page') or 'document_list'
    return redirect(url_for(previous_page))

@app.route('/extracts/<record_id>/delete', methods=['POST'])
@require_egc_data
def delete_extract(record_id):
    egc_data.delete_record_by_id(record_id)
    previous_page = request.args.get('previous_page') or 'extract_list'
    return redirect(url_for(previous_page))

@app.route('/units/<record_id>/delete', methods=['POST'])
@require_egc_data
def delete_unit(record_id):
    egc_data.delete_record_by_id(record_id)
    previous_page = request.args.get('previous_page') or 'unit_list'
    return redirect(url_for(previous_page))

@app.route('/attributes/<record_id>/delete', methods=['POST'])
@require_egc_data
def delete_attribute(record_id):
    egc_data.delete_record_by_id(record_id)
    previous_page = request.args.get('previous_page') or 'attribute_list'
    return redirect(url_for(previous_page))

@app.route('/groups/<record_id>/delete', methods=['POST'])
@require_egc_data
def delete_group(record_id):
    egc_data.delete_record_by_id(record_id)
    previous_page = request.args.get('previous_page') or 'group_list'
    return redirect(url_for(previous_page))

@app.route('/models/<record_id>/delete', methods=['POST'])
@require_egc_data
def delete_model(record_id):
    egc_data.delete_record_by_id(record_id)
    previous_page = request.args.get('previous_page') or 'model_list'
    return redirect(url_for(previous_page))

@app.route('/vrules/<record_id>/delete', methods=['POST'])
@require_egc_data
def delete_vrule(record_id):
    egc_data.delete_record_by_id(record_id)
    previous_page = request.args.get('previous_page') or 'vrule_list'
    return redirect(url_for(previous_page))

@app.route('/crules/<record_id>/delete', methods=['POST'])
@require_egc_data
def delete_crule(record_id):
    egc_data.delete_record_by_id(record_id)
    previous_page = request.args.get('previous_page') or 'crule_list'
    return redirect(url_for(previous_page))

@app.route('/documents/<record_id>')
@require_egc_data
def show_document(record_id):
    document = egc_data.get_record_by_id(record_id) or abort(404)
    return render_template('show_document.html', document=document,
        egc_data=egc_data)

@app.route('/extracts/<record_id>')
@require_egc_data
def show_extract(record_id):
    extract = egc_data.get_record_by_id(record_id) or abort(404)
    return render_template('show_extract.html', extract=extract,
        egc_data=egc_data)

@app.route('/units/<record_id>')
@require_egc_data
def show_unit(record_id):
  unit = egc_data.get_record_by_id(record_id) or abort(404)
  return render_template('show_unit.html', unit=unit, egc_data=egc_data)

@app.route('/attributes/<record_id>')
@require_egc_data
def show_attribute(record_id):
  attribute = egc_data.get_record_by_id(record_id) or abort(404)
  return render_template('show_attribute.html', attribute=attribute,
      egc_data=egc_data)

@app.route('/groups/<record_id>')
@require_egc_data
def show_group(record_id):
  group = egc_data.get_record_by_id(record_id) or abort(404)
  return render_template('show_group.html', group=group, egc_data=egc_data)

@app.route('/models/<record_id>')
@require_egc_data
def show_model(record_id):
  model = egc_data.get_record_by_id(record_id) or abort(404)
  return render_template('show_model.html', model=model, egc_data=egc_data)

@app.route('/vrules/<record_id>')
@require_egc_data
def show_vrule(record_id):
  vrule = egc_data.get_record_by_id(record_id) or abort(404)
  return render_template('show_vrule.html', vrule=vrule, egc_data=egc_data)

@app.route('/crules/<record_id>')
@require_egc_data
def show_crule(record_id):
  crule = egc_data.get_record_by_id(record_id) or abort(404)
  return render_template('show_crule.html', crule=crule, egc_data=egc_data)

@app.route('/api/documents/<record_id>', methods=['GET'])
@require_egc_data
def get_document(record_id):
    document = egc_data.get_record_by_id(record_id) or abort(404)
    return render_template('table_document.html', document=document,
            egc_data=egc_data)

@app.route('/api/extracts/<record_id>', methods=['GET'])
@require_egc_data
def get_extract(record_id):
    extract = egc_data.get_record_by_id(record_id) or abort(404)
    return render_template('table_extract.html', extract=extract,
            egc_data=egc_data)

@app.route('/api/units/<record_id>', methods=['GET'])
def get_unit(record_id):
  unit = egc_data.get_record_by_id(record_id) or abort(404)
  return render_template('table_unit.html', unit=unit, egc_data=egc_data)

@app.route('/api/attributes/<record_id>', methods=['GET'])
@require_egc_data
def get_attribute(record_id):
  attribute = egc_data.get_record_by_id(record_id) or abort(404)
  return render_template('table_attribute.html',
                          attribute=attribute, egc_data=egc_data)

@app.route('/api/groups/<record_id>', methods=['GET'])
@require_egc_data
def get_group(record_id):
  group = egc_data.get_record_by_id(record_id) or abort(404)
  return render_template('table_group.html',
      group=group, egc_data=egc_data)

@app.route('/api/models/<record_id>', methods=['GET'])
@require_egc_data
def get_model(record_id):
  model = egc_data.get_record_by_id(record_id) or abort(404)
  return render_template('table_model.html',
      model=model, egc_data=egc_data)

@app.route('/api/vrules/<record_id>', methods=['GET'])
@require_egc_data
def get_vrule(record_id):
  vrule = egc_data.get_record_by_id(record_id) or abort(404)
  return render_template('table_vrule.html',
      vrule=vrule, egc_data=egc_data)

@app.route('/api/crules/<record_id>', methods=['GET'])
@require_egc_data
def get_crule(record_id):
  crule = egc_data.get_record_by_id(record_id) or abort(404)
  return render_template('table_crule.html',
      crule=crule, egc_data=egc_data)

@app.route('/api/documents/<record_id>/extracts', methods=['GET'])
@require_egc_data
def get_document_extracts(record_id):
  if not egc_data.id_exists(record_id):
    abort(404)
  extracts = egc_data.ref_by('D', record_id, 'S') + \
             egc_data.ref_by('D', record_id, 'T')
  return render_template('datatable_extract.html', extracts=extracts,
      egc_data=egc_data, parent_id=record_id)

@app.route('/api/units/<record_id>/attributes', methods=['GET'])
@require_egc_data
def get_unit_attributes(record_id):
  if not egc_data.id_exists(record_id):
    abort(404)
  attributes = egc_data.ref_by('U', record_id, 'A')
  return render_template('datatable_attribute.html', attributes=attributes,
      egc_data=egc_data, parent_id=record_id)

@app.route('/api/units/<record_id>/units', methods=['GET'])
@require_egc_data
def get_unit_units(record_id):
  if not egc_data.id_exists(record_id):
    abort(404)
  units = egc_data.ref_by('U', record_id, 'U')
  return render_template('datatable_unit.html', units=units,
      egc_data=egc_data, parent_id=record_id)

@app.route('/api/units/<record_id>/models', methods=['GET'])
@require_egc_data
def get_unit_models(record_id):
  if not egc_data.id_exists(record_id):
    abort(404)
  models = egc_data.ref_by('U', record_id, 'M')
  return render_template('datatable_model.html', models=models,
      egc_data=egc_data, parent_id=record_id)

@app.route('/api/attributes/<record_id>/vrules', methods=['GET'])
@require_egc_data
def get_attribute_vrules(record_id):
  if not egc_data.id_exists(record_id):
    abort(404)
  vrules = egc_data.ref_by('A', record_id, 'V')
  return render_template('datatable_vrule.html', vrules=vrules,
      egc_data=egc_data, parent_id=record_id)

@app.route('/api/attributes/<record_id>/crules', methods=['GET'])
@require_egc_data
def get_attribute_crules(record_id):
  if not egc_data.id_exists(record_id):
    abort(404)
  crules = egc_data.ref_by('A', record_id, 'C')
  return render_template('datatable_crule.html', crules=crules,
      egc_data=egc_data, parent_id=record_id)

@app.route('/api/groups/<record_id>/vrules', methods=['GET'])
@require_egc_data
def get_group_vrules(record_id):
  if not egc_data.id_exists(record_id):
    abort(404)
  vrules = egc_data.ref_by('G', record_id, 'V')
  return render_template('datatable_vrule.html', vrules=vrules,
      egc_data=egc_data, parent_id=record_id)

@app.route('/api/groups/<record_id>/crules', methods=['GET'])
@require_egc_data
def get_group_crules(record_id):
  if not egc_data.id_exists(record_id):
    abort(404)
  crules = egc_data.ref_by('G', record_id, 'C')
  return render_template('datatable_crule.html', crules=crules,
      egc_data=egc_data, parent_id=record_id)

@app.route('/api/extracts/<record_id>/vrules', methods=['GET'])
@require_egc_data
def get_extract_vrules(record_id):
  if not egc_data.id_exists(record_id):
    abort(404)
  extract = egc_data.get_record_by_id(record_id)
  if extract["record_type"] == 'S':
    vrules = egc_data.ref_by('S', record_id, 'V')
  elif extract["record_type"] == 'T':
    vrules = egc_data.ref_by('T', record_id, 'V')
  return render_template('datatable_vrule.html', vrules=vrules,
      egc_data=egc_data, parent_id=record_id)

@app.route('/api/extracts/<record_id>/crules', methods=['GET'])
@require_egc_data
def get_extract_crules(record_id):
  if not egc_data.id_exists(record_id):
    abort(404)
  extract = egc_data.get_record_by_id(record_id)
  if extract["record_type"] == 'S':
    crules = egc_data.ref_by('S', record_id, 'C')
  elif extract["record_type"] == 'T':
    crules = egc_data.ref_by('T', record_id, 'C')
  return render_template('datatable_crule.html', crules=crules,
      egc_data=egc_data, parent_id=record_id)

if __name__ == '__main__':
  app.run()
