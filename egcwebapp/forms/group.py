from wtforms import Form, StringField, validators, \
                    FieldList, FormField

from .tag import TagForm

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
