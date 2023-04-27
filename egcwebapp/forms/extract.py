from wtforms import Form, StringField, SelectField, TextAreaField, validators, \
                    FieldList, FormField, BooleanField

from .document import DocumentForm
from .tag import TagForm

class ExtractForm(Form):
    id = StringField('Record ID',
        [validators.Length(min=1, max=50),
         validators.Regexp('[a-zA-Z0-9_]+'), validators.DataRequired()])
    auto_id = BooleanField('Auto-generate ID', default=False)
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
        if self.auto_id.data:
          self.id.render_kw = {'readonly': True}
          self.id.data = 'auto_generated'

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
      if self.auto_id.data:
        return True
      new_id = field.data
      if self.old_id != new_id:
        if self.egc_data.id_exists(new_id):
            raise validators.ValidationError('Record ID already exists')

    def auto_generate_id(self):
      if self.auto_id.data:
        record_type = self.record_type.data
        existing_ids = self.egc_data.find_all_ids(record_type)
        i = 1
        while True:
          new_id = record_type + str(i)
          if new_id == self.old_id or new_id not in existing_ids:
            self.id.data = new_id
            break
          i += 1

    def validate_document_id(self, field):
        d_id = self.egc_data.compose_id("D", "PMID", field.data)
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

