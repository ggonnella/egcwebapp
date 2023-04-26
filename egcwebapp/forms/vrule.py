from wtforms import Form, StringField, validators, FieldList, FormField
from .tag import TagForm
from .source import SourceForm

class VruleForm(Form):
    id = StringField('Expectation ID', [validators.Regexp('[a-zA-Z0-9_]+'),
      validators.DataRequired()])
    sources = FieldList(FormField(SourceForm), min_entries=1, label="Sources")
    attribute = StringField('Attribute', [validators.Length(min=1),
      validators.DataRequired()])
    group = StringField('Group', [validators.Length(min=1),
      validators.DataRequired()])
    group_portion = StringField('Group Portion')
    operator = StringField('Operator', [validators.Length(min=1),
      validators.DataRequired()])
    reference = StringField('Reference', [validators.Length(min=1),
      validators.DataRequired()])
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
        record_data["source"] = [s["source_id"] \
            for s in form.sources.data if s["source_id"]]
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

    def auto_generate_id(self):
      if self.auto_id.data:
        existing_ids = self.egc_data.get_record_ids("V")
        i = 1
        while True:
          new_id = "V" + str(i)
          if new_id == self.old_id or new_id not in existing_ids:
            self.id.data = new_id
            break
          i += 1

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

