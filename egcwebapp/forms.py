from wtforms import Form, StringField, SelectField, validators

class DocumentForm(Form):

    def validate_document_id(self, field):
      if self.old_id != field.data:
         if not self.egc_data.is_unique_document(field.data):
             raise validators.ValidationError('Document ID already exists')

    document_id = StringField('Document ID',
        [validators.Length(min=1, max=50), validators.DataRequired()])
    link = StringField('Link',
        [validators.URL(), validators.DataRequired()])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.old_id = kwargs.pop('old_id', None)
        self.egc_data = kwargs.pop('egc_data', None)

class SnippetTableForm(Form):
    record_id = StringField('Record ID',
        [validators.Length(min=1, max=50), validators.DataRequired()])
    record_type = SelectField('Record Type',
        choices=[('S', 'Snippet'), ('T', 'Table')],
        validators=[validators.DataRequired()])
    document_id = StringField('Document ID',
        [validators.Length(min=1, max=50), validators.DataRequired()])
    content = StringField('Text / Table Ref')

    def __init__(self, egc_data=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.egc_data = egc_data

    def validate_record_id(self, field):
        if self.egc_data and not self.egc_data.is_unique_id(field.data):
            raise validators.ValidationError('Record ID already exists')

    def validate_document_id(self, field):
        if self.egc_data and not self.egc_data.is_unique_document(field.data):
            raise validators.ValidationError('Document ID already exists')

