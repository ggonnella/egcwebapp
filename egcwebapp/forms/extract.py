from wtforms import Form, StringField, SelectField, TextAreaField, validators, \
                    FieldList, FormField

from .document import DocumentForm
from .tag import TagForm

class ExtractForm(Form):
    id = StringField('Record ID',
        [validators.Length(min=1, max=50),
         validators.Regexp('[a-zA-Z0-9_]+'), validators.DataRequired()])
    record_type = SelectField('Record Type',
        choices=[('S', 'Snippet'), ('T', 'Table')],
        validators=[validators.DataRequired()])
    document_id = StringField('Document ID',
        [validators.Length(min=1, max=50),
         validators.Regexp('[a-zA-Z0-9_]+'), validators.DataRequired()])
    contents = TextAreaField('Text / Table Ref', render_kw={"rows": 10})
    tags = FieldList(FormField(TagForm), min_entries=1, label="Tags")
    comment = StringField('Comment')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.egc_data = kwargs.pop('egc_data')
        self.old_id = kwargs.pop('old_id', None)
        self.script = TagForm.Script

    @classmethod
    def from_record(cls, form, record, **kwargs):
      if record["record_type"] == "T":
          contents = record["table_ref"]
      elif record["record_type"] == "S":
          contents = record["text"]
      form_data = {
              "id": record["id"],
              "record_type": record["record_type"],
              "document_id": record["document_id"]["item"],
              "contents": contents,
            }
      TagForm.add_tags_to_form_data(record, form_data)
      kwargs["data"] = form_data
      return cls(form, **kwargs)

    def validate_id(self, field):
      new_id = field.data
      if self.old_id != new_id:
        if not self.egc_data.is_unique_id(new_id):
            raise validators.ValidationError('Record ID already exists')

    def validate_document_id(self, field):
        d_id = self.egc_data.compute_docid(field.data)
        if not self.egc_data.id_exists(d_id):
            raise validators.ValidationError('Document ID does not exist')

    def validate_tags(self, field):
      TagForm.tags_validator(field)

    def to_record(form):
      record_data = {
          "record_type": form.record_type.data,
          "id": form.id.data,
      }
      DocumentForm.add_document_id_from_form(form, record_data)
      if form.record_type.data == "T":
          record_data["table_ref"] = form.contents.data
      elif form.record_type.data == "S":
          record_data["text"] = form.contents.data
      TagForm.add_tags_from_form(form, record_data)
      return record_data

