from wtforms import Form, StringField, validators, SelectField, \
                    FieldList, FormField, BooleanField
from .tag import TagForm
from egctools import id_generator


class InlineSelectField(SelectField):
    def __init__(self, label=None, validators=None, **kwargs):
        super(InlineSelectField, self).__init__(label, validators, **kwargs)
        self.inline = True

class InlineStringField(StringField):
    def __init__(self, label=None, validators=None, **kwargs):
        super(InlineStringField, self).__init__(label, validators, **kwargs)
        self.inline = True

class UnitForm(Form):
  id = StringField('Record ID', [validators.Length(min=1, max=50),
                               validators.Regexp('[a-zA-Z0-9_]+'),
                               validators.DataRequired()])
  auto_id = BooleanField('Auto-generate ID', default=False)
  type = InlineStringField('Type', validators=[
        validators.DataRequired(), validators.Regexp('[a-zA-Z0-9_]+')],
      render_kw={"style": "display: inline-block; "+\
                          "width: 32%; margin-right: 5px;"})
  kind = InlineSelectField('Type Kind', choices=[('category', 'Category'),
    ('single', 'Single'), ('multiple', 'Multiple'), ('named_set', 'Named Set'),
    ('defined_set', 'Defined Set')],
      render_kw={"style": "display: inline-block; "+\
                          "width: 12%; margin-right: 5px;"})
  resource = InlineStringField('Type Resource ID',
      render_kw={"style": "display: inline-block; width: 31%; "+\
                          "margin-bottom:20px;"})
  definition = StringField('Definition',
      validators = [validators.DataRequired()])
  symbol = StringField('Symbol', validators=[validators.DataRequired()])
  description = StringField('Description',
      validators=[validators.DataRequired()])
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
    if form.kind.data == "named_set":
      record_data["type"] = f"set:{form.type.data}"
    elif form.kind.data == "category":
      record_data["type"] = f"*{form.type.data}"
    elif form.kind.data == "multiple":
      record_data["type"] = f"set:+{form.type.data}"
    elif form.kind.data == "defined_set":
      record_data["type"] = f"set!:{form.type.data}"
    if form.resource.data:
      record_data["type"] = f"{record_data['type']}:{form.resource.data}"
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
    if form_data["type"].startswith("set:+"):
      form_data["kind"] = "multiple"
      form_data["type"] = form_data["type"][5:]
    elif form_data["type"].startswith("set!:"):
      form_data["kind"] = "defined_set"
      form_data["type"] = form_data["type"][5:]
    elif form_data["type"].startswith("set:"):
      form_data["kind"] = "named_set"
      form_data["type"] = form_data["type"][4:]
    elif form_data["type"].startswith("*"):
      form_data["kind"] = "category"
      form_data["type"] = form_data["type"][1:]
    else:
      form_data["kind"] = "single"
    if ":" in form_data["type"]:
      form_data["type"], form_data["resource"] = form_data["type"].split(":", 1)
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

  def validate_definition(self, field):
    if self.type.data == "set!:arrangement":
      if not self.egc_data.validate_fardes(field.data):
        raise validators.ValidationError(\
            'Invalid arrangement definition format')
    return True

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

