from wtforms import Form, StringField, validators, \
                    FieldList, FormField, BooleanField
from .tag import TagForm
from egctools import id_generator

class GroupForm(Form):
  id = StringField('Group ID', [validators.Regexp('[a-zA-Z0-9_]+'),
    validators.DataRequired()])
  auto_id = BooleanField('Auto-generate ID', default=False)
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
      if self.auto_id.data:
        self.id.render_kw = {'readonly': True}
        self.id.data = 'auto_generated'

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
    if self.auto_id.data:
      return True
    new_id = field.data
    if self.old_id != new_id:
      if self.egc_data.id_exists(new_id):
        raise validators.ValidationError('Record ID already exists')

  def auto_generate_id(self):
    if self.auto_id.data:
      self.id.data = id_generator.generate_G_id(\
          self.egc_data, self.name.data, self.type.data, self.old_id)

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
