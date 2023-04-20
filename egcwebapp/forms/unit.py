from wtforms import Form, StringField, validators, \
                    FieldList, FormField

from .tag import TagForm

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

