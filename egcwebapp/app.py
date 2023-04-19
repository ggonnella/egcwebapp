from flask import Flask, render_template, request, redirect, \
                  url_for, abort, jsonify, send_from_directory
from egcwebapp.forms import DocumentForm, ExtractForm, UnitForm, \
                            AttributeForm, GroupForm, ModelForm, \
                            VruleForm, CruleForm
from egctools.egcdata import EGCData
from pathlib import Path
import os
import re
import functools
import urllib.parse
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

def break_string(string, goal_length, min_length=None, breaking_chars=" ,"):
    """Breaks a string into pieces of a desired length.

    The function tries to break the string into pieces of length
    `goal_length`, where the break can only happen at one of the
    characters contained in the string `breaking_chars`.

    If there is no such character at the desired breaking position,
    it can take one between the position `min_length` and the
    and `goal_length` of the remaining string.

    If also in that region there is none, then take the first available
    breaking point after position `goal_length` (or leave the remaining string
    unbroken if there are no further breaking characters).

    Args:
        string (str):                   The string to be broken into pieces.
        goal_length (int):              The desired length of the pieces.
        min_length (int):               The minimum length of the pieces.
                                        (default: 90% of `goal_length`)
        breaking_chars (str, optional): The characters at which the string
                                        can be broken (default: " ,").

    Returns:
        list: A list of the broken pieces of the original string.
              The breaking character is included in the piece before the break.

    Examples:
        >>> break_string("This is a very long string that needs a break.", 20)
        ['This is a very long ', 'string that needs a ', 'break.']

        >>> break_string("This is a test string", 10, breaking_chars="-")
        ['This is a test string']
    """
    # Check if string is already shorter than goal length
    if len(string) <= goal_length:
        return [string]

    if min_length is None:
      min_length = int(goal_length * 0.9)

    # Find the first breaking character at the goal length
    if string[goal_length] in breaking_chars:
        return [string[:goal_length+1]] + break_string(string[goal_length+1:],
                goal_length, min_length, breaking_chars)

    # Find the last breaking character before the deviation range
    last_break = -1
    for i in range(min_length, goal_length):
        if i >= 0 and string[i] in breaking_chars:
            last_break = i

    # Find the first breaking character after the goal length
    first_break = -1
    for i in range(goal_length+1, len(string)):
        if string[i] in breaking_chars:
            first_break = i
            break

    # Choose the preferred breaking position based on priority
    if last_break >= 0:
        return [string[:last_break+1]] + break_string(string[last_break+1:],
                goal_length, min_length, breaking_chars)
    elif first_break > 0:
        return [string[:first_break+1]] + break_string(string[first_break+1:],
                goal_length, min_length, breaking_chars)
    else:
        return [string]

@app.context_processor
def my_context_processor():

    DOI_URL = "https://doi.org/"
    GEONAMES_URL = "https://www.geonames.org/"
    OBO_URL = "http://purl.obolibrary.org/obo/"
    MICRO_URL = "https://www.ebi.ac.uk/ols4/ontologies/micro/classes/"+\
        "http%253A%252F%252Fpurl.obolibrary.org%252Fobo%252FMICRO_"
    WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/"
    WIKTIONARY_URL = "https://en.wiktionary.org/wiki/"
    INTERPRO_URL="https://www.ebi.ac.uk/interpro/entry/InterPro/"
    PFAM_URL="https://www.ebi.ac.uk/interpro/entry/pfam/"
    PFAM_CLAN_URL="https://www.ebi.ac.uk/interpro/set/pfam/"
    TC_URL="https://www.tcdb.org/search/result.php?tc="
    EC_URL="https://enzyme.expasy.org/EC/"
    GO_URL="https://www.ebi.ac.uk/QuickGO/term/GO:"
    SO_URL="http://www.sequenceontology.org/browser/current_release/term/"
    KEGG_URL="https://www.genome.jp/entry/"
    BRENDA_EC_URL="https://www.brenda-enzymes.org/enzyme.php?ecno="
    COG_URL="https://www.ncbi.nlm.nih.gov/research/cog/cog/"
    COG_CAT_URL="https://www.ncbi.nlm.nih.gov/research/cog/cogcategory/"
    ARCOG_URL="http://eggnog6.embl.de/search/ogs/"
    PMID_URL="https://www.ncbi.nlm.nih.gov/pubmed/"
    CDD_URL="https://www.ncbi.nlm.nih.gov/Structure/cdd/"
    TAXID_URL="https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id="
    SNOMED_URL="https://snomedbrowser.com/Codes/Details/"
    BACDIVE_URL="https://bacdive.dsmz.de/strain/"
    HTTP_URL="http:"
    HTTPS_URL="https:"
    INTERRIDGE_URL="https://vents-data.interridge.org/ventfield/"
    PROSITE_URL="https://prosite.expasy.org/"
    PIRSF_URL="https://www.ebi.ac.uk/interpro/entry/pirsf/"
    TIGRFAMS_URL="https://www.ncbi.nlm.nih.gov/genome/annotation_prok/evidence/"
    SFLD_URL="https://www.ebi.ac.uk/interpro/entry/sfld/"
    SMART_URL="https://www.ebi.ac.uk/interpro/entry/smart/"
    HAMAP_URL="https://hamap.expasy.org/rule/"
    UNIPROTKB_QUERY_URL="https://www.uniprot.org/uniprotkb?query="

    def link_external_resource(resource, item, text=None):
      if text is None:
        text = item
      url = None
      if resource == "geonames":
          url = GEONAMES_URL + item
      elif resource in ["ENVO", "UBERON", "RO", "CHEBI", "OMP", "NCIT", "OHMI"]:
          url = OBO_URL + resource + "_" + item
      elif resource == "MICRO":
          url = MICRO_URL + item
      elif resource == "GO":
          url = GO_URL + item
      elif resource == "Wikipedia":
          url = WIKIPEDIA_URL + item
      elif resource == "Wiktionary":
          url = WIKTIONARY_URL + item
      elif resource == "taxid":
          url = TAXID_URL + item
      elif resource == "pmid" or resource == "PMID":
          url = PMID_URL + item
      elif resource == "sctid":
          url = SNOMED_URL + item
      elif resource == "bacdive":
          url = BACDIVE_URL + item
      elif resource == "interridge":
          url = INTERRIDGE_URL + item
      elif resource == "doi" or resource == "DOI":
          url = DOI_URL + item
      elif resource == "http":
          url = HTTP_URL + item
      elif resource == "https":
          url = HTTPS_URL + item
      elif resource == 'InterPro':
        url = INTERPRO_URL + item
      elif resource == 'TC':
        url = TC_URL + item
      elif resource == 'Pfam':
        url = PFAM_URL + item
      elif resource == 'Pfam_clan':
        url = PFAM_CLAN_URL + item
      elif resource == 'CDD':
        url = CDD_URL + item
      elif resource == 'EC':
        url = EC_URL + item
      elif resource == 'BRENDA_EC':
        url = BRENDA_EC_URL + item
      elif resource == 'SO':
        url = SO_URL + item
      elif resource == 'KEGG':
        url = KEGG_URL + item
      elif resource == 'COG_category':
        url = COG_CAT_URL + item
      elif resource == 'COG':
        url = COG_URL + item
      elif resource == 'arCOG':
        url = ARCOG_URL + item
      elif resource == 'PROSITE':
        url = PROSITE_URL + item
      elif resource == 'PIRSF':
        url = PIRSF_URL + item
      elif resource == 'TIGRFAMs':
        url = TIGRFAMS_URL + item
      elif resource == 'SFLD':
        url = SFLD_URL + item
      elif resource == 'SMART':
        url = SMART_URL + item
      elif resource == 'HAMAP':
        url = HAMAP_URL + item
      if url:
        return f"<a href='{url}' target='_blank'>{text}</a>"
      else:
        return None

    def linked_tag_value(tag_type, tag_value):
      if tag_type in ["XD", "XR"]:
        linked = []
        for value_part in tag_value.split(";"):
          m = re.match(r"^(.+):([^!#]+)([!#].*)?$", value_part)
          link = None
          if m:
            resource = m.group(1)
            item = m.group(2)
            link = link_external_resource(resource, item, value_part)
          if link:
            linked.append(link)
          else:
            linked.append(value_part)
        return ";".join(linked)
      else:
        return tag_value

    def linked_model_id(resource_id, model_id):
      link = link_external_resource(resource_id, model_id)
      if link:
        return link
      else:
        return model_id

    def uniprotkb_link(query):
      url = UNIPROTKB_QUERY_URL + query
      return f"<small>[&rightarrow;&nbsp;<a href='{url}' "+\
             "style='text-decoration: none' "+\
             "target='_blank'>UniProtKB</a>]</small>"

    def linked_unit_symbol(unit_type, symbol):
      if unit_type in ["specific_gene", "specific_protein", "function",
      "set:protein_complex"]:
        if symbol == ".":
          return symbol
        symq = urllib.parse.quote(symbol, safe='')
        query= f"query=(gene:{symq})%20OR%20(protein_name:{symq})"
        return symbol + " " + uniprotkb_link(query)
      else:
        return symbol

    def linked_unit_description(unit_type, description):
      if unit_type in ["specific_gene", "specific_protein", "function",
      "set:protein_complex"]:
        if description == ".":
          return description
        desq = description.replace("[", "(").replace("]", ")")
        desq = urllib.parse.quote(desq, safe='')
        return description + " " + uniprotkb_link(desq)
      else:
        return description

    def linked_group_definition(group_type, group_definition, parent_id):
        m = re.match(r"^(.+):([^!#]+)([!#].*)?$", group_definition)
        if m:
          group_definition_prefix = m.group(1)
          group_definition_id = m.group(2)
          link = link_external_resource(group_definition_prefix,
                                        group_definition_id,
                                        group_definition)
          if link:
            return link
        rel_groups = []
        definition_pieces = break_string(group_definition, 12, 8)
        output = []
        for group_definition in definition_pieces:
          if group_type == 'combined' or group_type == 'inverted':
              rel_groups = re.findall(r"[a-zA-Z0-9_]+", group_definition)
          else:
              m = re.match(r'^derived:([a-zA-Z0-9_]+):.*', group_definition)
              if m:
                  rel_groups = [m.group(1)]

          for rel_group in rel_groups:
              rendered_template = render_template('related_record_link.html',
                  related_type='group', related_id=rel_group,
                  parent_id=parent_id, prev='list_group')
              group_definition = re.sub(r'\b' + re.escape(rel_group) + r'\b',
                  rendered_template, group_definition)
          group_definition = '<span class="related_link">' +\
                            group_definition + '</span>'
          output.append(group_definition)

        return "<br/>".join(output)

    def linked_unit_definition(unit_type, unit_definition, parent_id):
        if unit_definition == ".":
          return unit_definition
        if unit_type == 'family_or_domain:InterPro':
          return link_external_resource('InterPro', unit_definition)
        elif unit_type == 'family_or_domain:TC':
          return link_external_resource('TC', unit_definition)
        elif unit_type == 'family_or_domain:Pfam':
          return link_external_resource('Pfam', unit_definition)
        elif unit_type == 'family_or_domain:Pfam_clan':
          return link_external_resource('Pfam_clan', unit_definition)
        elif unit_type == 'family_or_domain:CDD':
          return link_external_resource('CDD', unit_definition)
        elif unit_type == 'function:EC':
          return link_external_resource('EC', unit_definition)
        elif unit_type == 'function:BRENDA_EC':
          return link_external_resource('BRENDA_EC', unit_definition)
        elif unit_type == 'function:GO':
          return link_external_resource('GO', unit_definition)
        elif unit_type == 'ortholog_groups_category:COG_category':
          return link_external_resource('COG_category', unit_definition)
        elif unit_type == 'ortholog_group:COG':
          return link_external_resource('COG', unit_definition)
        elif unit_type == 'ortholog_group:arCOG':
          return link_external_resource('arCOG', unit_definition)
        elif (unit_type == 'feature_type' or unit_type == 'amino_acid') and \
            unit_definition.startswith('SO:'):
          return link_external_resource('SO',
                unit_definition[3:], unit_definition)
        elif unit_type == 'set:metabolic_pathway' \
            and unit_definition.startswith('KEGG:'):
          return link_external_resource('KEGG',
                unit_definition[5:], unit_definition)
        m = re.match(r"^ref:(.+):(.*)$", unit_definition)
        if m:
          return "ref:" + link_external_resource(m.group(1), m.group(2),
              unit_definition[4:])
        if unit_type.startswith("set:+"):
          definition_parts = unit_definition.split(",")
          output_parts = [linked_unit_definition("set:" +\
              unit_type[5:], part, parent_id) for part in definition_parts]
          return ",".join(output_parts)
        unit_definition_pieces = break_string(unit_definition, 15)
        output = []
        for unit_definition in unit_definition_pieces:
          rel_units = []
          if unit_type.startswith('homolog_'):
              m = re.match(r'^homolog:([a-zA-Z0-9_]+)', unit_definition)
              if m:
                  rel_units = [m.group(1)]
          elif unit_type == 'set!:arrangement':
              parts = unit_definition.split(',')
              rel_units = []
              for part in parts:
                  m = re.match(r'^([a-zA-Z0-9_]+)$', part)
                  if m:
                      rel_units.append(m.group(1))
          elif unit_type.startswith('*') or unit_type.startswith('set!:'):
              rel_units = re.findall(r"[a-zA-Z0-9_]+", unit_definition)
          elif unit_definition.startswith('derived:'):
              m = re.match(r'^derived:([a-zA-Z0-9_]+):.*', unit_definition)
              if m:
                rel_units = [m.group(1)]

          for rel_unit in rel_units:
              rendered_template = render_template('related_record_link.html',
                  related_type='unit', related_id=rel_unit, prev='list_unit',
                  noclass=True, parent_id=parent_id)
              unit_definition = re.sub(r'\b' + re.escape(rel_unit) + r'\b',
                  rendered_template, unit_definition)
          unit_definition = '<span class="related_link">' +\
                            unit_definition + '</span>'
          output.append(unit_definition)

        return "<br/>".join(output)

    return {'linked_group_definition': linked_group_definition,
            'linked_unit_definition': linked_unit_definition,
            'linked_tag_value': linked_tag_value,
            'linked_model_id': linked_model_id,
            'linked_unit_symbol': linked_unit_symbol,
            'linked_unit_description': linked_unit_description,
           }

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
      "name": form.name.data,
      "type": form.type.data,
      "definition": form.definition.data,
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

@app.route('/api/groups/<record_id>/groups', methods=['GET'])
@require_egc_data
def get_group_groups(record_id):
  if not egc_data.id_exists(record_id):
    abort(404)
  groups = egc_data.ref_by('G', record_id, 'G')
  return render_template('datatable_group.html', groups=groups,
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
