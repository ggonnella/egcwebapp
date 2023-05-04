from wtforms import Form, StringField, SelectField, validators
import json
import re
from jinja2 import Markup

class TagForm(Form):
    tagname = StringField('Name', render_kw={'size': 2})
    tagtype = SelectField('Type', choices=[('Z', 'String'), ('i', 'Integer'),
                                           ('f', 'Float'), ('J', 'JSON')], default='Z')
    tagvalue = StringField('Value', render_kw={'size': "80%"})

    def validate_value(self, field):
        if self.type.data == 'i':
            try:
                int(field.data)
            except ValueError:
                raise validators.ValidationError('Value must be an integer')
        elif self.type.data == 'f':
            try:
                float(field.data)
            except ValueError:
                raise validators.ValidationError('Value must be a float')
        elif self.type.data == 'J':
            try:
                json.loads(field.data)
            except ValueError:
                raise validators.ValidationError('Value must be a valid JSON')

    def validate(self):
      if self.tagname.data is None or self.tagname.data == '':
        if self.tagvalue.data != '':
          return validators.ValidationError('Tag name cannot be empty')
      else:
        if self.tagvalue.data == '':
          return validators.ValidationError('Tag value cannot be empty')
        if not re.match('^[a-zA-Z][a-zA-Z0-9_]*$', self.tagname.data):
          return validators.ValidationError('Tag name must start with a letter and contain only letters, numbers and underscores')
        if re.search('[\n\t]', self.tagname.data):
          return validators.ValidationError('Tag name cannot contain newlines or tabs')
      return True

    Script = Markup('''
      function updateTagNamesAndIds(container) {
        var tagInputs = container.querySelectorAll('.tag-entry');
        for (var i = 0; i < tagInputs.length; i++) {
          var input = tagInputs[i];
          if (input.id.includes('tagname')) {
            input.id = 'tags-' + i + '-tagname';
            input.name = 'tags-' + i + '-tagname';
          } else if (input.id.includes('tagtype')) {
            input.id = 'tags-' + i + '-tagtype';
            input.name = 'tags-' + i + '-tagtype';
          } else if (input.id.includes('tagvalue')) {
            input.id = 'tags-' + i + '-tagvalue';
            input.name = 'tags-' + i + '-tagvalue';
          }
        }
      }

      document.getElementById('add_tag_button').addEventListener('click', function() {
        const tagTemplate = document.querySelector('#tags-container .tag-entry').cloneNode(true);
        var tagIndex = document.querySelectorAll('#tags-container .tag-entry').length;
        tagTemplate.querySelectorAll('input').forEach(function(input) {
          input.value = '';
          if (input.id.includes('tagname')) {
            input.id = 'tags-' + tagIndex + '-tagname';
            input.name = 'tags-' + tagIndex + '-tagname';
          } else if (input.id.includes('tagtype')) {
            input.id = 'tags-' + tagIndex + '-tagtype';
            input.name = 'tags-' + tagIndex + '-tagtype';
          } else if (input.id.includes('tagvalue')) {
            input.id = 'tags-' + tagIndex + '-tagvalue';
            input.name = 'tags-' + tagIndex + '-tagvalue';
          }
        });
        document.getElementById('tags-container').appendChild(tagTemplate);
      });

      document.getElementById('tags-container').addEventListener('click', function(event) {
        if (event.target.classList.contains('btn-delete-tag')) {
          console.log('delete tag');
          const tagEntry = event.target.closest('.tag-entry');
          const tagTemplate = document.querySelector('#tags-container .tag-entry').cloneNode(true);
          tagTemplate.querySelectorAll('input').forEach(function(input) {
            input.value = '';
            if (input.id.includes('tagname')) {
              input.id = 'tags-0-tagname';
              input.name = 'tags-0-tagname';
            } else if (input.id.includes('tagtype')) {
              input.id = 'tags-0-tagtype';
              input.name = 'tags-0-tagtype';
            } else if (input.id.includes('tagvalue')) {
              input.id = 'tags-0-tagvalue';
              input.name = 'tags-0-tagvalue';
            }
          });
          tagEntry.querySelectorAll('input').forEach(function(input) {
            input.value = '';
          });
          tagEntry.remove();
          if (document.querySelectorAll('#tags-container .tag-entry').length === 0) {
            document.getElementById('tags-container').appendChild(tagTemplate);
          }
          updateTagNamesAndIds(document.getElementById('tags-container'));
        }
      });

      updateTagNamesAndIds(document.getElementById('tags-container'));
      ''')

    @staticmethod
    def tags_validator(tags_field):
      # check that (non-empty) tags all have different names
      tag_names = []
      for tag in tags_field:
        if tag.tagname.data != '':
          if tag.tagname.data in tag_names:
            raise validators.ValidationError('Tag names must be unique')
          else:
            tag_names.append(tag.tagname.data)

    @staticmethod
    def add_tags_from_form(form, record_data):
      record_data["tags"] = {}
      for tag in form.tags.data:
        if tag and tag["tagname"]:
          record_data["tags"][tag["tagname"]] = \
              {"value": tag["tagvalue"], "type": tag["tagtype"]}
      if len(record_data["tags"]) == 0:
        del record_data["tags"]
      if len(form.comment.data) > 0:
        record_data["comment"] = form.comment.data

    @staticmethod
    def add_tags_to_form_data(record, form_data):
      form_data["tags"] = []
      if "tags" in record:
        for tag_name, tag_type_value in record["tags"].items():
            form_data["tags"].append({
              "tagname": tag_name,
              "tagtype": tag_type_value["type"],
              "tagvalue": tag_type_value["value"]
            })
      if "comment" in record and record["comment"]:
        form_data["comment"] = record["comment"]
      else:
        form_data["comment"] = ""

