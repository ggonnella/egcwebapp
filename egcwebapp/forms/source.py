from wtforms import Form, StringField, validators
from jinja2 import Markup

class SourceForm(Form):
    source_id = StringField('Source ID')

    Script = Markup('''
      function updateSourceNamesAndIds(container) {
        var sourceInputs = container.querySelectorAll('.source-entry');
        for (var i = 0; i < sourceInputs.length; i++) {
          var input = sourceInputs[i];
          input.id = 'sources-' + i + '-source_id';
          input.name = 'sources-' + i + '-source_id';
        }
      }

      document.getElementById('add_source_button').addEventListener('click', function() {
        const sourceTemplate = document.querySelector('#sources-container .source-entry').cloneNode(true);
        var sourceIndex = document.querySelectorAll('#sources-container .source-entry').length;
        sourceTemplate.querySelectorAll('input').forEach(function(input) {
          input.value = '';
          input.id = 'sources-' + sourceIndex + '-source_id';
          input.name = 'sources-' + sourceIndex + '-source_id';
        });
        document.getElementById('sources-container').appendChild(sourceTemplate);
      });

      document.getElementById('sources-container').addEventListener('click', function(event) {
        if (event.target.classList.contains('btn-delete-source')) {
          console.log('delete source');
          const sourceEntry = event.target.closest('.source-entry');
          const sourceTemplate = document.querySelector('#sources-container .source-entry').cloneNode(true);
          sourceTemplate.querySelectorAll('input').forEach(function(input) {
            input.value = '';
            input.id = 'sources-0-source_id';
            input.name = 'sources-0-source_id';
          });
          sourceEntry.querySelectorAll('input').forEach(function(input) {
            input.value = '';
          });
          sourceEntry.remove();
          if (document.querySelectorAll('#sources-container .source-entry').length === 0) {
            document.getElementById('sources-container').appendChild(sourceTemplate);
          }
          updateSourceNamesAndIds(document.getElementById('sources-container'));
        }
      });

      updateSourceNamesAndIds(document.getElementById('sources-container'));
      ''')

    @staticmethod
    def sources_validator(egc_data, sources_field):
      sources = [s["source_id"] for s in sources_field.data if s['source_id']]
      if not sources:
        raise validators.ValidationError('At least one source is required')
      for source in sources:
        if not egc_data.id_exists(source):
          raise validators.ValidationError(\
              f"Document Extract '{source}' does not exist")
      return True

