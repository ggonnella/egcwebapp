from wtforms import Form, StringField, validators, \
                    FieldList, FormField
from .tag import TagForm

class DocumentForm(Form):

    document_id = StringField('Document ID',
        [validators.Length(min=1, max=50),
         validators.Regexp('[a-zA-Z0-9_]+'), validators.DataRequired()])
    link = StringField('Link',
        [validators.URL(), validators.DataRequired()])
    tags = FieldList(FormField(TagForm), min_entries=1, label="Tags")
    comment = StringField('Comment')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.egc_data = kwargs.pop('egc_data')
        self.old_id = kwargs.pop('old_id', None)
        self.script = TagForm.Script

    @classmethod
    def from_record(cls, form, record, **kwargs):
      form_data={"document_id": record["document_id"]["item"],
          "link": record["link"]}
      TagForm.add_tags_to_form_data(record, form_data)
      kwargs["data"] = form_data
      return cls(form, **kwargs)

    def validate_document_id(self, field):
      new_id = self.egc_data.compose_id("D", "PMID", field.data)
      if self.old_id != new_id:
        if self.egc_data.id_exists(new_id):
          raise validators.ValidationError('Document ID already exists')

    def validate_tags(self, field):
      TagForm.tags_validator(field)

    @staticmethod
    def add_document_id_from_form(form, record_data):
      record_data["document_id"] = {
          "resource_prefix": "PMID",
          "item": form.document_id.data,
          "location": None,
          "term": None
      }

    def to_record(form):
      record_data = {
          "record_type": "D",
          "link": form.link.data
      }
      DocumentForm.add_document_id_from_form(form, record_data)
      TagForm.add_tags_from_form(form, record_data)
      return record_data
