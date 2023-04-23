from wtforms import Form, StringField, validators, \
                    FieldList, FormField

from .tag import TagForm
from .source import SourceForm

class CruleForm(Form):
    id = StringField('Expectation ID', [validators.Regexp('[a-zA-Z0-9_]+'), validators.DataRequired()])
    sources = FieldList(FormField(SourceForm), min_entries=1, label="Sources")
    attribute = StringField('Attribute', [validators.Length(min=1), validators.DataRequired()])
    vs_attribute = StringField('vs. Attribute')
    group1 = StringField('Group 1', [validators.Length(min=1), validators.DataRequired()])
    group1_portion = StringField('Group 1 Portion')
    operator = StringField('Operator', [validators.Length(min=1), validators.DataRequired()])
    group2 = StringField('Group 2', [validators.Length(min=1), validators.DataRequired()])
    group2_portion = StringField('Group 2 Portion')
    tags = FieldList(FormField(TagForm), min_entries=1, label="Tags")
    comment = StringField('Comment')

    def to_record(form):
      record_data = {
          "record_type": "C",
          "id": form.id.data,
          "group1": {"id": form.group1.data},
          "operator": form.operator.data,
          "group2": {"id": form.group2.data},
      }
      if len(form.sources.data) > 1:
        record_data["source"] = [s["source_id"] for s in form.sources.data]
      else:
        record_data["source"] = form.sources.data[0]["source_id"]
      if form.vs_attribute.data:
        record_data["attribute"] = {"id1": form.attribute.data,
                                    "id2": form.vs_attribute.data}
      else:
        record_data["attribute"] = form.attribute.data
      if form.group1_portion.data:
        record_data["group1"]["portion"] = form.group1_portion.data
      if form.group2_portion.data:
        record_data["group2"]["portion"] = form.group2_portion.data
      TagForm.add_tags_from_form(form, record_data)
      return record_data

    @classmethod
    def from_record(cls, form, record, **kwargs):
      form_data = {
        "id": record["id"],
        "group1": record["group1"]["id"],
        "operator": record["operator"],
        "group2": record["group2"]["id"],
      }
      if isinstance(record["source"], list):
        form_data["sources"] = \
            [{"source_id": s} for s in record["source"]]
      else:
        form_data["sources"] = [{"source_id": record["source"]}]
      if isinstance(record["attribute"], dict):
        form_data["attribute"] = record["attribute"]["id1"]
        form_data["vs_attribute"] = record["attribute"]["id2"]
      else:
        form_data["attribute"] = record["attribute"]
        form_data["vs_attribute"] = None
      if "portion" in record["group1"]:
        form_data["group1_portion"] = record["group1"]["portion"]
      if "portion" in record["group2"]:
        form_data["group2_portion"] = record["group2"]["portion"]
      TagForm.add_tags_to_form_data(record, form_data)
      kwargs["data"] = form_data
      return cls(form, **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.egc_data = kwargs.pop('egc_data')
        self.old_id = kwargs.pop('old_id', None)
        self.script = TagForm.Script + SourceForm.Script

    def validate_id(self, field):
      new_id = field.data
      if self.old_id != new_id:
        if self.old_id:
          if self.egc_data.is_ref_by(self.old_id):
              raise validators.ValidationError('Record ID cannot be changed '+\
                  f'since the old ID ({self.old_id}) '+\
                  'is referenced by other records')
        if not self.egc_data.is_unique_id(new_id):
            raise validators.ValidationError('Record ID already exists')

    def validate_attribute(self, field):
        if not self.egc_data.id_exists(field.data):
            raise validators.ValidationError('Attribute does not exist')

    def validate_vs_attribute(self, field):
        if field.data:
          if not self.egc_data.id_exists(field.data):
              raise validators.ValidationError('Attribute does not exist')

    def validate_group1(self, field):
        if not self.egc_data.id_exists(field.data):
            raise validators.ValidationError('Group does not exist')

    def validate_group2(self, field):
        if not self.egc_data.id_exists(field.data):
            raise validators.ValidationError('Group does not exist')

    def validate_sources(self, field):
      SourceForm.sources_validator(self.egc_data, field)

    def validate_tags(self, field):
      TagForm.tags_validator(field)

