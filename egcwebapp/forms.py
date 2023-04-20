from wtforms import Form, StringField, SelectField, TextAreaField, validators, \
                    FieldList, FormField
import json
import re
from jinja2 import Markup

class TagForm(Form):
    tagname = StringField('Name', render_kw={'size': 2})
    tagtype = SelectField('Type', choices=[('Z', 'String'), ('i', 'Integer'),
                                           ('f', 'Float'), ('J', 'JSON')], default='Z')
    tagvalue = StringField('Value', render_kw={'size': "80%"})

    def validate_value(self, field):
        if self.type.data == 'i':
            try:
                int(field.data)
            except ValueError:
                raise validators.ValidationError('Value must be an integer')
        elif self.type.data == 'f':
            try:
                float(field.data)
            except ValueError:
                raise validators.ValidationError('Value must be a float')
        elif self.type.data == 'J':
            try:
                json.loads(field.data)
            except ValueError:
                raise validators.ValidationError('Value must be a valid JSON')

    def validate(self):
      if self.tagname.data is None or self.tagname.data == '':
        if self.tagvalue.data != '':
          return validators.ValidationError('Tag name cannot be empty')
      else:
        if self.tagvalue.data == '':
          return validators.ValidationError('Tag value cannot be empty')
        if not re.match('^[a-zA-Z][a-zA-Z0-9_]*$', self.tagname.data):
          return validators.ValidationError('Tag name must start with a letter and contain only letters, numbers and underscores')
        if re.search('[\n\t]', self.tagname.data):
          return validators.ValidationError('Tag name cannot contain newlines or tabs')
      return True

    Script = Markup('''
      function updateTagNamesAndIds(container) {
        var tagInputs = container.querySelectorAll('.tag-entry');
        for (var i = 0; i < tagInputs.length; i++) {
          var input = tagInputs[i];
          if (input.id.includes('tagname')) {
            input.id = 'tags-' + i + '-tagname';
            input.name = 'tags-' + i + '-tagname';
          } else if (input.id.includes('tagtype')) {
            input.id = 'tags-' + i + '-tagtype';
            input.name = 'tags-' + i + '-tagtype';
          } else if (input.id.includes('tagvalue')) {
            input.id = 'tags-' + i + '-tagvalue';
            input.name = 'tags-' + i + '-tagvalue';
          }
        }
      }

      document.getElementById('add_tag_button').addEventListener('click', function() {
        const tagTemplate = document.querySelector('#tags-container .tag-entry').cloneNode(true);
        var tagIndex = document.querySelectorAll('#tags-container .tag-entry').length;
        tagTemplate.querySelectorAll('input').forEach(function(input) {
          input.value = '';
          if (input.id.includes('tagname')) {
            input.id = 'tags-' + tagIndex + '-tagname';
            input.name = 'tags-' + tagIndex + '-tagname';
          } else if (input.id.includes('tagtype')) {
            input.id = 'tags-' + tagIndex + '-tagtype';
            input.name = 'tags-' + tagIndex + '-tagtype';
          } else if (input.id.includes('tagvalue')) {
            input.id = 'tags-' + tagIndex + '-tagvalue';
            input.name = 'tags-' + tagIndex + '-tagvalue';
          }
        });
        document.getElementById('tags-container').appendChild(tagTemplate);
      });

      document.getElementById('tags-container').addEventListener('click', function(event) {
        if (event.target.classList.contains('btn-delete-tag')) {
          console.log('delete tag');
          const tagEntry = event.target.closest('.tag-entry');
          const tagTemplate = document.querySelector('#tags-container .tag-entry').cloneNode(true);
          tagTemplate.querySelectorAll('input').forEach(function(input) {
            input.value = '';
            if (input.id.includes('tagname')) {
              input.id = 'tags-0-tagname';
              input.name = 'tags-0-tagname';
            } else if (input.id.includes('tagtype')) {
              input.id = 'tags-0-tagtype';
              input.name = 'tags-0-tagtype';
            } else if (input.id.includes('tagvalue')) {
              input.id = 'tags-0-tagvalue';
              input.name = 'tags-0-tagvalue';
            }
          });
          tagEntry.querySelectorAll('input').forEach(function(input) {
            input.value = '';
          });
          tagEntry.remove();
          if (document.querySelectorAll('#tags-container .tag-entry').length === 0) {
            document.getElementById('tags-container').appendChild(tagTemplate);
          }
          updateTagNamesAndIds(document.getElementById('tags-container'));
        }
      });

      updateTagNamesAndIds(document.getElementById('tags-container'));
      ''')

    @staticmethod
    def tags_validator(tags_field):
      # check that (non-empty) tags all have different names
      tag_names = []
      for tag in tags_field:
        if tag.tagname.data != '':
          if tag.tagname.data in tag_names:
            raise validators.ValidationError('Tag names must be unique')
          else:
            tag_names.append(tag.tagname.data)

    @staticmethod
    def add_tags_from_form(form, record_data):
      record_data["tags"] = {}
      for tag in form.tags.data:
        if tag != '' and tag["tagname"] != '':
          record_data["tags"][tag["tagname"]] = \
              {"value": tag["tagvalue"], "type": tag["tagtype"]}
      if len(record_data["tags"]) == 0:
        del record_data["tags"]
      if len(form.comment.data) > 0:
        record_data["comment"] = form.comment.data

    @staticmethod
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

class DocumentForm(Form):

    document_id = StringField('Document ID',
        [validators.Length(min=1, max=50),
         validators.Regexp('[a-zA-Z0-9_]+'), validators.DataRequired()])
    link = StringField('Link',
        [validators.URL(), validators.DataRequired()])
    tags = FieldList(FormField(TagForm), min_entries=1, label="Tags")
    comment = StringField('Comment')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.egc_data = kwargs.pop('egc_data')
        self.old_id = kwargs.pop('old_id', None)
        self.script = TagForm.Script

    @classmethod
    def from_record(cls, form, record, **kwargs):
      form_data={"document_id": record["document_id"]["item"],
          "link": record["link"]}
      TagForm.add_tags_to_form_data(record, form_data)
      kwargs["data"] = form_data
      return cls(form, **kwargs)

    def validate_document_id(self, field):
      new_id = self.egc_data.compute_docid_from_pfx_and_item("PMID", field.data)
      if self.old_id != new_id:
        if not self.egc_data.is_unique_id(new_id):
          raise validators.ValidationError('Document ID already exists')

    def validate_tags(self, field):
      TagForm.tags_validator(field)

    @staticmethod
    def add_document_id_from_form(form, record_data):
      record_data["document_id"] = {
          "resource_prefix": "PMID",
          "item": form.document_id.data,
          "location": None,
          "term": None
      }

    def to_record(form):
      record_data = {
          "record_type": "D",
          "link": form.link.data
      }
      DocumentForm.add_document_id_from_form(form, record_data)
      TagForm.add_tags_from_form(form, record_data)
      return record_data

class ExtractForm(Form):
    id = StringField('Record ID',
        [validators.Length(min=1, max=50),
         validators.Regexp('[a-zA-Z0-9_]+'), validators.DataRequired()])
    record_type = SelectField('Record Type',
        choices=[('S', 'Snippet'), ('T', 'Table')],
        validators=[validators.DataRequired()])
    document_id = StringField('Document ID',
        [validators.Length(min=1, max=50),
         validators.Regexp('[a-zA-Z0-9_]+'), validators.DataRequired()])
    contents = TextAreaField('Text / Table Ref', render_kw={"rows": 10})
    tags = FieldList(FormField(TagForm), min_entries=1, label="Tags")
    comment = StringField('Comment')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.egc_data = kwargs.pop('egc_data')
        self.old_id = kwargs.pop('old_id', None)
        self.script = TagForm.Script

    @classmethod
    def from_record(cls, form, record, **kwargs):
      if record["record_type"] == "T":
          contents = record["table_ref"]
      elif record["record_type"] == "S":
          contents = record["text"]
      form_data = {
              "id": record["id"],
              "record_type": record["record_type"],
              "document_id": record["document_id"]["item"],
              "contents": contents,
            }
      TagForm.add_tags_to_form_data(record, form_data)
      kwargs["data"] = form_data
      return cls(form, **kwargs)

    def validate_id(self, field):
      new_id = field.data
      if self.old_id != new_id:
        if not self.egc_data.is_unique_id(new_id):
            raise validators.ValidationError('Record ID already exists')

    def validate_document_id(self, field):
        d_id = self.egc_data.compute_docid(field.data)
        if not self.egc_data.id_exists(d_id):
            raise validators.ValidationError('Document ID does not exist')

    def validate_tags(self, field):
      TagForm.tags_validator(field)

    def to_record(form):
      record_data = {
          "record_type": form.record_type.data,
          "id": form.id.data,
      }
      DocumentForm.add_document_id_from_form(form, record_data)
      if form.record_type.data == "T":
          record_data["table_ref"] = form.contents.data
      elif form.record_type.data == "S":
          record_data["text"] = form.contents.data
      TagForm.add_tags_from_form(form, record_data)
      return record_data

class UnitForm(Form):
  id = StringField('Record ID', [validators.Length(min=1, max=50),
                               validators.Regexp('[a-zA-Z0-9_]+'), validators.DataRequired()])
  type = StringField('Type', validators=[validators.DataRequired()])
  definition = StringField('Definition')
  symbol = StringField('Symbol')
  description = StringField('Description')
  tags = FieldList(FormField(TagForm), min_entries=1, label="Tags")
  comment = StringField('Comment')

  def to_record(form):
    record_data = {
        "record_type": "U",
        "id": form.id.data,
        "type": form.type.data,
        "definition": form.definition.data,
        "symbol": form.symbol.data,
        "description": form.description.data
    }
    TagForm.add_tags_from_form(form, record_data)
    return record_data

  @classmethod
  def from_record(cls, form, record, **kwargs):
    form_data = {
        "id": record["id"],
        "type": record["type"],
        "definition": record["definition"],
        "symbol": record["symbol"],
        "description": record["description"]
    }
    TagForm.add_tags_to_form_data(record, form_data)
    kwargs["data"] = form_data
    return cls(form, **kwargs)

  def validate(self):
    if not super().validate():
      return False
    if not any([self.definition.data, self.symbol.data, self.description.data]):
      msg = 'At least one of definition, symbol, or description must be present'
      self.definition.errors.append(msg)
      self.symbol.errors.append(msg)
      self.description.errors.append(msg)
      return False
    return True

  def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.egc_data = kwargs.pop('egc_data')
      self.old_id = kwargs.pop('old_id', None)
      self.script = TagForm.Script

  def validate_id(self, field):
    new_id = field.data
    if self.old_id != new_id:
      if not self.egc_data.is_unique_id(new_id):
          raise validators.ValidationError('Record ID already exists')

  def validate_tags(self, field):
    TagForm.tags_validator(field)

class AttributeForm(Form):
  id = StringField('Attribute ID', [validators.Length(min=1, max=50),
                             validators.Regexp('[a-zA-Z0-9_]+'),
                             validators.DataRequired()])
  unit_id = StringField('Unit ID', [validators.Length(min=1, max=50),
                             validators.Regexp('[a-zA-Z0-9_]+'),
                             validators.DataRequired()])
  mode = StringField('Mode', [validators.Length(min=1, max=50),
                              validators.Regexp('[a-zA-Z0-9_]+'),
                              validators.DataRequired()])
  mode_type = SelectField('Measurement Mode Type',
                choices=[('measurement_mode_simple', 'Simple'),
                         ('measurement_mode_relative', 'Relative'),
                         ('measurement_mode_w_location', 'With Location'),
                         ('measurement_mode_relative_w_location',
                            'Relative with Location')],
                validators=[validators.DataRequired()])

  hidden = {'style': 'display: none'}
  reference = StringField('Reference', render_kw=hidden)
  location_type = StringField('Location Type', render_kw=hidden)
  location_label = StringField('Location Label', render_kw=hidden)
  tags = FieldList(FormField(TagForm), min_entries=1, label="Tags")
  comment = StringField('Comment')

  def to_record(form):
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
    TagForm.add_tags_from_form(form, record_data)
    return record_data

  Script = Markup('''
      const modeTypeField = document.getElementById("mode_type");
      const referenceFieldWrapper =
        document.getElementById("reference-wrapper");
      const referenceField = document.getElementById("reference");
      const locationTypeFieldWrapper =
        document.getElementById("location_type-wrapper");
      const locationTypeField =
        document.getElementById("location_type");
      const locationLabelFieldWrapper =
        document.getElementById("location_label-wrapper");
      const locationLabelField =
        document.getElementById("location_label");

      function toggleFieldVisibility() {
        if (modeTypeField.value === 'measurement_mode_relative' ||
            modeTypeField.value === 'measurement_mode_relative_w_location') {
          referenceFieldWrapper.style.display = 'block';
          referenceField.style.display = 'block';
        } else {
          referenceFieldWrapper.style.display = 'none';
          referenceField.style.display = 'none';
        }
        if (modeTypeField.value === 'measurement_mode_w_location' ||
            modeTypeField.value === 'measurement_mode_relative_w_location') {
          locationLabelFieldWrapper.style.display = 'block';
          locationLabelField.style.display = 'block';
          locationTypeFieldWrapper.style.display = 'block';
          locationTypeField.style.display = 'block';
        } else {
          locationLabelFieldWrapper.style.display = 'none';
          locationLabelField.style.display = 'none';
          locationTypeFieldWrapper.style.display = 'none';
          locationTypeField.style.display = 'none';
        }
      }

      modeTypeField.addEventListener('change', toggleFieldVisibility);
      document.addEventListener('DOMContentLoaded', toggleFieldVisibility);
    ''')

  def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.egc_data = kwargs.pop('egc_data')
      self.old_id = kwargs.pop('old_id', None)
      self.script = AttributeForm.Script
      self.script += TagForm.Script

  @classmethod
  def from_record(cls, form, record, **kwargs):
    form_data={
      "id": record["id"],
      "unit_id": record["unit_id"],
      "mode_type": "measurement_mode_simple",
    }
    if isinstance(record["mode"], dict):
      form_data["mode"] = record["mode"]["mode"]
      if "reference" in record["mode"]:
        form_data["reference"] = record["mode"]["reference"]
        form_data["mode_type"] = "measurement_mode_relative"
      if "location_type" in record["mode"]:
        form_data["location_type"] = record["mode"]["location_type"]
        if form_data["mode_type"] == "measurement_mode_relative":
          form_data["mode_type"] = \
              "measurement_mode_relative_w_location"
        else:
          form_data["mode_type"] = "measurement_mode_w_location"
      if "location_label" in record["mode"]:
        form_data["location_label"] = \
            record["mode"]["location_label"]
    else:
      form_data["mode"] = record["mode"]
    TagForm.add_tags_to_form_data(record, form_data)
    kwargs["data"] = form_data
    return cls(form, **kwargs)

  def validate_id(self, field):
    new_id = field.data
    if self.old_id != new_id:
      if not self.egc_data.is_unique_id(new_id):
          raise validators.ValidationError('Record ID already exists')

  def validate_unit_id(self, field):
      if not self.egc_data.id_exists(field.data):
          raise validators.ValidationError('Unit does not exist')

  def validate_location_type(self, field):
      if self.mode_type.data in ['measurement_mode_w_location',
            'measurement_mode_relative_w_location'] and not field.data:
          raise validators.ValidationError(
              'Location Type is required for this type of measurement mode')

  def validate_location_label(self, field):
      if self.mode_type.data in ['measurement_mode_w_location',
            'measurement_mode_relative_w_location'] and not field.data:
          raise validators.ValidationError(
              'Location Label is required for this type of measurement mode')

  def validate_reference(self, field):
      if self.mode_type.data in ['measurement_mode_relative',
                                 'measurement_mode_relative_w_location']:
        if not field.data:
          raise validators.ValidationError(
              'Reference is required for this type of measurement mode')
        if not self.egc_data.id_exists(field.data):
          raise validators.ValidationError('Unit does not exist')

  def validate_tags(self, field):
    TagForm.tags_validator(field)

class ModelForm(Form):
    unit_id = StringField('Unit ID', [validators.Length(min=1, max=50), validators.Regexp('[a-zA-Z0-9_]+'), validators.DataRequired()])
    resource_id = StringField('Resource ID', [validators.Length(min=1, max=50),
                               validators.Regexp('[a-zA-Z0-9_]+'), validators.DataRequired()])
    model_id = StringField('Model ID', [validators.Length(min=1, max=50), validators.DataRequired()])
    model_name = StringField('Model Name', [validators.Length(min=1, max=100), validators.DataRequired()])
    tags = FieldList(FormField(TagForm), min_entries=1, label="Tags")
    comment = StringField('Comment')

    def validate(self):
      if not super().validate():
        return False
      new_id = self.egc_data.compute_modelid_from_data(self.unit_id.data, self.resource_id.data, self.model_id.data)
      if self.old_id != new_id:
        if not self.egc_data.has_unique_id(new_id):
          raise validators.ValidationError('Record already exists')
      return True

    def validate_unit_id(self, field):
        if not self.egc_data.id_exists(field.data):
            raise validators.ValidationError('Unit does not exist')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.egc_data = kwargs.pop('egc_data')
        self.old_id = kwargs.pop('old_id', None)
        self.script = TagForm.Script

    @classmethod
    def from_record(cls, form, record, **kwargs):
      form_data = {
          "unit_id": record["unit_id"],
          "resource_id": record["resource_id"],
          "model_id": record["model_id"],
          "mode_name": record["model_name"],
      }
      TagForm.add_tags_to_form_data(record, form_data)
      kwargs["data"] = form_data
      return cls(form, **kwargs)

    def to_record(form):
      record_data = {
          "record_type": "M",
          "unit_id": form.unit_id.data,
          "resource_id": form.resource_id.data,
          "model_id": form.model_id.data,
          "model_name": form.model_name.data,
      }
      TagForm.add_tags_from_form(form, record_data)
      return record_data

class SourceForm(Form):
    source_id = StringField('Source ID')

    Script = Markup('''
      function updateSourceNamesAndIds(container) {
        var sourceInputs = container.querySelectorAll('.source-entry');
        for (var i = 0; i < sourceInputs.length; i++) {
          var input = sourceInputs[i];
          input.id = 'sources-' + i + '-source_id';
          input.name = 'sources-' + i + '-source_id';
        }
      }

      document.getElementById('add_source_button').addEventListener('click', function() {
        const sourceTemplate = document.querySelector('#sources-container .source-entry').cloneNode(true);
        var sourceIndex = document.querySelectorAll('#sources-container .source-entry').length;
        sourceTemplate.querySelectorAll('input').forEach(function(input) {
          input.value = '';
          input.id = 'sources-' + sourceIndex + '-source_id';
          input.name = 'sources-' + sourceIndex + '-source_id';
        });
        document.getElementById('sources-container').appendChild(sourceTemplate);
      });

      document.getElementById('sources-container').addEventListener('click', function(event) {
        if (event.target.classList.contains('btn-delete-source')) {
          console.log('delete source');
          const sourceEntry = event.target.closest('.source-entry');
          const sourceTemplate = document.querySelector('#sources-container .source-entry').cloneNode(true);
          sourceTemplate.querySelectorAll('input').forEach(function(input) {
            input.value = '';
            input.id = 'sources-0-source_id';
            input.name = 'sources-0-source_id';
          });
          sourceEntry.querySelectorAll('input').forEach(function(input) {
            input.value = '';
          });
          sourceEntry.remove();
          if (document.querySelectorAll('#sources-container .source-entry').length === 0) {
            document.getElementById('sources-container').appendChild(sourceTemplate);
          }
          updateSourceNamesAndIds(document.getElementById('sources-container'));
        }
      });

      updateSourceNamesAndIds(document.getElementById('sources-container'));
      ''')

    @staticmethod
    def sources_validator(egc_data, sources_field):
      for source in sources_field:
        if source.data["source_id"] != '':
          if not egc_data.id_exists(source.data["source_id"]):
            raise validators.ValidationError(\
                'Document Extract ID "{}" does not exist'.\
                  format(source.data["source_id"]))
      return True

class VruleForm(Form):
    id = StringField('Expectation ID', [validators.Regexp('[a-zA-Z0-9_]+'), validators.DataRequired()])
    sources = FieldList(FormField(SourceForm), min_entries=1, label="Sources")
    attribute = StringField('Attribute', [validators.Length(min=1), validators.DataRequired()])
    group = StringField('Group', [validators.Length(min=1), validators.DataRequired()])
    group_portion = StringField('Group Portion')
    operator = StringField('Operator', [validators.Length(min=1), validators.DataRequired()])
    reference = StringField('Reference', [validators.Length(min=1), validators.DataRequired()])
    tags = FieldList(FormField(TagForm), min_entries=1, label="Tags")
    comment = StringField('Comment')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.egc_data = kwargs.pop('egc_data')
        self.old_id = kwargs.pop('old_id', None)
        self.script = TagForm.Script + SourceForm.Script

    @classmethod
    def from_record(cls, form, record, **kwargs):
      form_data = {
        "id": record["id"],
        "attribute": record["attribute"],
        "group": record["group"]["id"],
        "operator": record["operator"],
        "reference": record["reference"],
      }
      if isinstance(record["source"], list):
        form_data["sources"] = \
            [{"source_id": s} for s in record["source"]]
      else:
        form_data["sources"] = [{"source_id": record["source"]}]
      if "portion" in record["group"]:
        form_data["group_portion"] = record["group"]["portion"]
      TagForm.add_tags_to_form_data(record, form_data)
      kwargs["data"] = form_data
      return cls(form, **kwargs)

    def to_record(form):
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
      TagForm.add_tags_from_form(form, record_data)
      return record_data

    def validate_id(self, field):
      new_id = field.data
      if self.old_id != new_id:
        if not self.egc_data.is_unique_id(new_id):
            raise validators.ValidationError('Record ID already exists')

    def validate_attribute(self, field):
        if not self.egc_data.id_exists(field.data):
            raise validators.ValidationError('Attribute does not exist')

    def validate_group(self, field):
        if not self.egc_data.id_exists(field.data):
            raise validators.ValidationError('Group does not exist')

    def validate_sources(self, field):
      SourceForm.sources_validator(self.egc_data, field)

    def validate_tags(self, field):
      TagForm.tags_validator(field)

class CruleForm(Form):
    id = StringField('Expectation ID', [validators.Regexp('[a-zA-Z0-9_]+'), validators.DataRequired()])
    sources = FieldList(FormField(SourceForm), min_entries=1, label="Sources")
    attribute = StringField('Attribute', [validators.Length(min=1), validators.DataRequired()])
    vs_attribute = StringField('vs. Attribute')
    group1 = StringField('Group 1', [validators.Length(min=1), validators.DataRequired()])
    group1_portion = StringField('Group 1 Portion')
    operator = StringField('Operator', [validators.Length(min=1), validators.DataRequired()])
    group2 = StringField('Group 2', [validators.Length(min=1), validators.DataRequired()])
    group2_portion = StringField('Group 2 Portion')
    tags = FieldList(FormField(TagForm), min_entries=1, label="Tags")
    comment = StringField('Comment')

    def to_record(form):
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
      TagForm.add_tags_from_form(form, record_data)
      return record_data

    @classmethod
    def from_record(cls, form, record, **kwargs):
      form_data = {
        "id": record["id"],
        "group1": record["group1"]["id"],
        "operator": record["operator"],
        "group2": record["group2"]["id"],
      }
      if isinstance(record["source"], list):
        form_data["sources"] = \
            [{"source_id": s} for s in record["source"]]
      else:
        form_data["sources"] = [{"source_id": record["source"]}]
      if isinstance(record["attribute"], dict):
        form_data["attribute"] = record["attribute"]["id1"]
        form_data["vs_attribute"] = record["attribute"]["id2"]
      else:
        form_data["attribute"] = record["attribute"]
        form_data["vs_attribute"] = None
      if "portion" in record["group1"]:
        form_data["group1_portion"] = record["group1"]["portion"]
      if "portion" in record["group2"]:
        form_data["group2_portion"] = record["group2"]["portion"]
      TagForm.add_tags_to_form_data(record, form_data)
      kwargs["data"] = form_data
      return cls(form, **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.egc_data = kwargs.pop('egc_data')
        self.old_id = kwargs.pop('old_id', None)
        self.script = TagForm.Script + SourceForm.Script

    def validate_id(self, field):
      new_id = field.data
      if self.old_id != new_id:
        if not self.egc_data.is_unique_id(new_id):
            raise validators.ValidationError('Record ID already exists')

    def validate_attribute(self, field):
        if not self.egc_data.id_exists(field.data):
            raise validators.ValidationError('Attribute does not exist')

    def validate_vs_attribute(self, field):
        if field.data:
          if not self.egc_data.id_exists(field.data):
              raise validators.ValidationError('Attribute does not exist')

    def validate_group1(self, field):
        if not self.egc_data.id_exists(field.data):
            raise validators.ValidationError('Group does not exist')

    def validate_group2(self, field):
        if not self.egc_data.id_exists(field.data):
            raise validators.ValidationError('Group does not exist')

    def validate_sources(self, field):
      SourceForm.sources_validator(self.egc_data, field)

    def validate_tags(self, field):
      TagForm.tags_validator(field)

class GroupForm(Form):
  id = StringField('Group ID', [validators.Regexp('[a-zA-Z0-9_]+'),
    validators.DataRequired()])
  name = StringField('Group Name', [validators.Length(min=1, max=50),
    validators.DataRequired()])
  type = StringField('Group Type', [validators.Length(min=1, max=50),
    validators.DataRequired()])
  definition = StringField('Group Definition', [validators.Length(min=1),
    validators.DataRequired()])
  tags = FieldList(FormField(TagForm), min_entries=1, label="Tags")
  comment = StringField('Comment')

  def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.egc_data = kwargs.pop('egc_data')
      self.old_id = kwargs.pop('old_id', None)
      self.script = TagForm.Script

  @classmethod
  def from_record(cls, form, record, **kwargs):
    form_data = {
        "id": record["id"],
        "name": record["name"],
        "type": record["type"],
        "definition": record["definition"],
    }
    TagForm.add_tags_to_form_data(record, form_data)
    kwargs["data"] = form_data
    return cls(form, **kwargs)

  def validate_id(self, field):
    new_id = field.data
    if self.old_id != new_id:
      if not self.egc_data.is_unique_id(new_id):
          raise validators.ValidationError('Record ID already exists')

  def validate_tags(self, field):
    TagForm.tags_validator(field)

  def to_record(form):
    record_data = {
        "record_type": "G",
        "id": form.id.data,
        "name": form.name.data,
        "type": form.type.data,
        "definition": form.definition.data,
    }
    TagForm.add_tags_from_form(form, record_data)
    return record_data
