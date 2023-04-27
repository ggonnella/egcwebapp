from wtforms import Form, StringField, validators, \
                    FieldList, FormField

from .tag import TagForm

class ModelForm(Form):
    unit_id = StringField('Unit ID', [validators.Length(min=1, max=50),
      validators.Regexp('[a-zA-Z0-9_]+'), validators.DataRequired()])
    resource_id = StringField('Resource ID', [validators.Length(min=1, max=50),
                               validators.Regexp('[a-zA-Z0-9_]+'),
                               validators.DataRequired()])
    model_id = StringField('Model ID', [validators.Length(min=1, max=50),
      validators.DataRequired()])
    model_name = StringField('Model Name', [validators.Length(min=1, max=100),
      validators.DataRequired()])
    tags = FieldList(FormField(TagForm), min_entries=1, label="Tags")
    comment = StringField('Comment')

    def validate(self):
      if not super().validate():
        return False
      new_id = self.egc_data.compose_id("M", self.unit_id.data,
          self.resource_id.data, self.model_id.data)
      if self.old_id != new_id:
        if self.egc_data.id_exists(new_id):
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
          "model_name": record["model_name"],
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

