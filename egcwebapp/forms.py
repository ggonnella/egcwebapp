from wtforms import Form, StringField, SelectField, TextAreaField, validators, \
                    FieldList, FormField, Field
from wtforms.validators import ValidationError, Regexp
import json
import re
from jinja2 import Markup

class DocumentForm(Form):

    def validate_document_id(self, field):
      new_id = self.egc_data.compute_docid_from_pfx_and_item("PMID", field.data)
      if self.old_id != new_id:
        if not self.egc_data.is_unique_id(new_id):
          raise validators.ValidationError('Document ID already exists')

    document_id = StringField('Document ID',
        [validators.Length(min=1, max=50),
         validators.Regexp('[a-zA-Z0-9_]+'), validators.DataRequired()])
    link = StringField('Link',
        [validators.URL(), validators.DataRequired()])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.egc_data = kwargs.pop('egc_data')
        self.old_id = kwargs.pop('old_id', None)

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.egc_data = kwargs.pop('egc_data')
        self.old_id = kwargs.pop('old_id', None)

    def validate_id(self, field):
      new_id = field.data
      if self.old_id != new_id:
        if not self.egc_data.has_unique_id(new_id):
            raise validators.ValidationError('Record ID already exists')

    def validate_document_id(self, field):
        d_id = self.egc_data.compute_docid(field.data)
        if not self.egc_data.id_exists(d_id):
            raise validators.ValidationError('Document ID does not exist')

class UnitForm(Form):
  id = StringField('Record ID', [validators.Length(min=1, max=50),
                               validators.Regexp('[a-zA-Z0-9_]+'), validators.DataRequired()])
  type = StringField('Type', validators=[validators.DataRequired()])
  definition = StringField('Definition')
  symbol = StringField('Symbol')
  description = StringField('Description')

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

  def validate_id(self, field):
    new_id = field.data
    if self.old_id != new_id:
      if not self.egc_data.has_unique_id(new_id):
          raise validators.ValidationError('Record ID already exists')

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

  def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.egc_data = kwargs.pop('egc_data')
      self.old_id = kwargs.pop('old_id', None)
      self.script = Markup('''
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

class ModelForm(Form):
    unit_id = StringField('Unit ID', [validators.Length(min=1, max=50), validators.Regexp('[a-zA-Z0-9_]+'), validators.DataRequired()])
    resource_id = StringField('Resource ID', [validators.Length(min=1, max=50),
                               validators.Regexp('[a-zA-Z0-9_]+'), validators.DataRequired()])
    model_id = StringField('Model ID', [validators.Length(min=1, max=50), validators.DataRequired()])
    model_name = StringField('Model Name', [validators.Length(min=1, max=100), validators.DataRequired()])

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

class SourceForm(Form):
    source_id = StringField('Source ID', [validators.Length(min=1), validators.DataRequired()])

    def validate(self):
        rv = super().validate()
        if not rv:
            return False

        if not self.egc_data.id_exists(self.source_id.data):
            self.source_id.errors.append('Source ID "{}" does not exist'.format(self.source_id.data))
            return False

        return True

class ValueExpectationForm(Form):
    id = StringField('Expectation ID', [validators.Regexp('[a-zA-Z0-9_]+'), validators.DataRequired()])
    source = FieldList(FormField(SourceForm))
    attribute = StringField('Attribute', [validators.Length(min=1), validators.DataRequired()])
    group = StringField('Group', [validators.Length(min=1), validators.DataRequired()])
    operator = StringField('Operator', [validators.Length(min=1), validators.DataRequired()])
    reference = StringField('Reference', [validators.Length(min=1), validators.DataRequired()])
    tags = StringField('Tags')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.egc_data = kwargs.pop('egc_data')
        self.old_id = kwargs.pop('old_id', None)

    def validate_id(self, field):
      new_id = field.data
      if self.old_id != new_id:
        if not self.egc_data.is_unique_id(new_id):
            raise validators.ValidationError('Record ID already exists')

    def validate(self):
        rv = super().validate()
        if not rv:
            return False

        for source_form in self.source:
            if not source_form.validate():
                return False

        return True


class ComparativeExpectationForm(Form):
    id = StringField('Expectation ID', [validators.Regexp('[a-zA-Z0-9_]+'), validators.DataRequired()])
    source = FieldList(FormField(SourceForm))
    attribute = StringField('Attribute or Comparison', [validators.Length(min=1), validators.DataRequired()])
    group1 = StringField('Group 1', [validators.Length(min=1), validators.DataRequired()])
    operator = StringField('Operator', [validators.Length(min=1), validators.DataRequired()])
    group2 = StringField('Group 2', [validators.Length(min=1), validators.DataRequired()])
    tags = StringField('Tags')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.egc_data = kwargs.pop('egc_data')
        self.old_id = kwargs.pop('old_id', None)

    def validate_id(self, field):
      new_id = field.data
      if self.old_id != new_id:
        if not self.egc_data.is_unique_id(new_id):
            raise validators.ValidationError('Record ID already exists')

    def validate(self):
        rv = super().validate()
        if not rv:
            return False

        for source_form in self.source:
            if not source_form.validate():
                return False

        return True

class TagForm(Form):
    tagname = StringField('Name')
    tagtype = SelectField('Type', choices=[('Z', 'String'), ('i', 'Integer'),
                                           ('f', 'Float'), ('J', 'JSON')], default='Z')
    tagvalue = StringField('Value')

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

    OldScript = Markup('''
      document.getElementById('add_tag_button').addEventListener('click', function() {
        const tagTemplate = document.querySelector('#tags-container .tag-entry').cloneNode(true);
        document.getElementById('tags-container').appendChild(tagTemplate);
      });

      document.getElementById('tags-container').addEventListener('click', function(event) {
        if (event.target.classList.contains('btn-delete-tag')) {
          const tagEntry = event.target.closest('.tag-entry');
          tagEntry.remove();
        }
      });
      ''')

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
    # check that tags all have different names
    # skip empty names
    tag_names = []
    for tag in field:
      if tag.tagname.data != '':
        if tag.tagname.data in tag_names:
          raise validators.ValidationError('Tag names must be unique')
        else:
          tag_names.append(tag.tagname.data)
