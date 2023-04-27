from wtforms import Form, StringField, validators, \
                    FieldList, FormField, BooleanField
from .tag import TagForm
from egctools import id_generator

class UnitForm(Form):
  id = StringField('Record ID', [validators.Length(min=1, max=50),
                               validators.Regexp('[a-zA-Z0-9_]+'),
                               validators.DataRequired()])
  auto_id = BooleanField('Auto-generate ID', default=False)
  type = StringField('Type', validators=[validators.DataRequired()])
  definition = StringField('Definition', validators = [validators.DataRequired()])
  symbol = StringField('Symbol', validators=[validators.DataRequired()])
  description = StringField('Description', validators=[validators.DataRequired()])
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
    if all(x == "." for x in \
        [self.definition.data, self.symbol.data, self.description.data]):
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
      if self.auto_id.data:
        self.id.render_kw = {'readonly': True}
        self.id.data = 'auto_generated'

  def validate_id(self, field):
    if self.auto_id.data:
      return True
    new_id = field.data
    if self.old_id != new_id:
      if self.egc_data.id_exists(new_id):
        raise validators.ValidationError('Record ID already exists')

  def auto_generate_id(self):
    if self.auto_id.data:
      self.id.data = id_generator.generate_U_id(\
          self.egc_data, self.type.data, self.symbol.data,
          self.definition.data, self.description.data, self.old_id)

  def validate_tags(self, field):
    TagForm.tags_validator(field)

