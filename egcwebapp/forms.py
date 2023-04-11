from wtforms import Form, StringField, SelectField, validators

class DocumentForm(Form):

    def validate_document_id(self, field):
      new_id = self.egc_data.compute_docid_from_pfx_and_item("PMID", field.data)
      if self.old_id != new_id:
        if not self.egc_data.is_unique_id(new_id):
          raise validators.ValidationError('Document ID already exists')

    document_id = StringField('Document ID',
        [validators.Length(min=1, max=50), validators.DataRequired()])
    link = StringField('Link',
        [validators.URL(), validators.DataRequired()])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.egc_data = kwargs.pop('egc_data')
        self.old_id = kwargs.pop('old_id', None)

class ExtractForm(Form):
    record_id = StringField('Record ID',
        [validators.Length(min=1, max=50), validators.DataRequired()])
    record_type = SelectField('Record Type',
        choices=[('S', 'Snippet'), ('T', 'Table')],
        validators=[validators.DataRequired()])
    document_id = StringField('Document ID',
        [validators.Length(min=1, max=50), validators.DataRequired()])
    content = StringField('Text / Table Ref')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.egc_data = kwargs.pop('egc_data')
        self.old_id = kwargs.pop('old_id', None)

    def validate_record_id(self, field):
        if not self.egc_data.has_unique_id(field.data):
            raise validators.ValidationError('Record ID already exists')

    def validate_document_id(self, field):
        d_record_id = self.egc_data.compute_docid(field.data)
        if not self.egc_data.id_exists(d_record_id):
            raise validators.ValidationError('Document ID does not exist')

