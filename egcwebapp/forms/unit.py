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

class InlineBooleanField(BooleanField):
    def __init__(self, label=None, validators=None, **kwargs):
        super(InlineBooleanField, self).__init__(label, validators, **kwargs)
        self.type = "BooleanField"
        self.inline = True

class UnitForm(Form):
  id = StringField('Record ID', [validators.Length(min=1, max=50),
                               validators.Regexp('[a-zA-Z0-9_]+'),
                               validators.DataRequired()])
  auto_id = BooleanField('Auto-generate ID', default=False)
  kind = InlineSelectField('Type Kind', choices=[
    ('simple', 'Simple'),
    ('category', 'Category'),
    ('set', 'Set')],
      render_kw={"style": "display: inline-block; "+\
                          "width: 10%; margin-right: 5px;"},
    default='simple')
  base_type = InlineStringField('Type', validators=[
        validators.DataRequired(), validators.Regexp('[a-zA-Z0-9_]+')],
      render_kw={"style": "display: inline-block; "+\
                          "width: 20%; margin-right: 4px;"})
  enumerating = InlineBooleanField('Enumerating',
      render_kw={"style": "display: inline-block; vertical-align: middle; "+\
                          "width: 2%; margin-right: 4px;"})
  multi = InlineBooleanField('Composed',
      render_kw={"style": "display: inline-block; vertical-align: middle; "+\
                          "width: 2%; margin-right: 4px;"})
  resource = InlineStringField('Resource ID',
      render_kw={"style": "display: inline-block; width: 20%; "+\
                          "margin-bottom:20px;"})
  definition = StringField('Definition',
      validators = [validators.DataRequired()])
  symbol = StringField('Symbol', validators=[validators.DataRequired()])
  description = StringField('Description',
      validators=[validators.DataRequired()])
  tags = FieldList(FormField(TagForm), min_entries=1, label="Tags")
  comment = StringField('Comment')

  def to_record(form):
    form.enumerating.data = True if form.enumerating.raw_data else False
    form.multi.data = True if form.multi.raw_data else False
    record_data = {
        "record_type": "U",
        "id": form.id.data,
        "type":
          {
            "kind": form.kind.data,
            "base_type": form.base_type.data,
            "enumerating": form.enumerating.data,
            "multi": form.multi.data,
          },
        "definition": form.definition.data,
        "symbol": form.symbol.data,
        "description": form.description.data
    }
    if form.resource.data:
      record_data["type"]["resource"] = form.resource.data
    TagForm.add_tags_from_form(form, record_data)
    return record_data

  @classmethod
  def from_record(cls, form, record, **kwargs):
    form_data = {
        "id": record["id"],
        "base_type": record["type"]["base_type"],
        "kind": record["type"]["kind"],
        "enumerating": record["type"]["enumerating"],
        "multi": record["type"]["multi"],
        "resource": record["type"].get("resource", ""),
        "definition": record["definition"],
        "symbol": record["symbol"],
        "description": record["description"]
    }
    TagForm.add_tags_to_form_data(record, form_data)
    kwargs["data"] = form_data
    return cls(form, **kwargs)

  def validate_enumerating(self, field):
    if self.enumerating.raw_data:
      if self.kind.data == "simple":
        raise validators.ValidationError(\
            'Enumerating is not allowed for simple units')

  def validate_multi(self, field):
    if self.multi.raw_data:
      if self.kind.data == "simple":
        raise validators.ValidationError(\
            'The multi flag is not allowed for simple units')

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
      if "data" in kwargs:
        self.enumerating.data = kwargs["data"]["enumerating"]
        self.multi.data = kwargs["data"]["multi"]

  def validate_definition(self, field):
    if self.enumerating.raw_data:
      if self.base_type.data == "arrangement":
        if not self.egc_data.validate_fardes(field.data):
          raise validators.ValidationError(\
              'Invalid arrangement definition format')
      else:
        for unit_id in field.data.split(","):
          if not self.egc_data.id_exists(unit_id):
            raise validators.ValidationError(\
                'Unit ID {} does not exist'.format(unit_id))
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
          self.egc_data, self.base_type.data, self.symbol.data,
          self.definition.data, self.description.data, self.old_id)

  def validate_tags(self, field):
    TagForm.tags_validator(field)

