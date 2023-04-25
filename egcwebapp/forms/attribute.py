from wtforms import Form, StringField, SelectField, validators, \
                    FieldList, FormField
from jinja2 import Markup

from .tag import TagForm

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

