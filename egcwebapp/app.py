from flask import Flask, render_template, request, redirect, url_for, abort
from egcwebapp.forms import DocumentForm, SnippetTableForm
from egcwebapp.egc_data import EGCData
from pathlib import Path
import os

app = Flask(__name__)
app.secret_key = 'secret_key'
app.config['UPLOAD_FOLDER'] = str(Path(app.instance_path) / 'uploads')
egc_data = None

@app.route('/')
def index():
    return redirect(url_for('document_list'))

@app.route('/load_egc_file', methods=['GET', 'POST'])
def load_egc_file():
    global egc_data
    if request.method == 'POST':
        file = request.files['file']
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        egc_data = EGCData.from_file(file_path)
        return redirect(url_for('document_list'))
    return render_template('load_egc_file.html')

@app.route('/documents')
def document_list():
  if egc_data is None:
    return redirect(url_for('load_egc_file'))
  else:
    documents = egc_data.get_documents()
    return render_template('document_list.html', documents=documents)

@app.route('/documents/create', methods=['GET', 'POST'])
def create_document():
  if egc_data is None:
    return redirect(url_for('load_egc_file'))
  else:
    form = DocumentForm(request.form, egc_data=egc_data)
    if request.method == 'POST' and form.validate():
        new_document = {
            "record_type": "D",
            "document_id": {
                "resource_prefix": "PMID",
                "item": form.document_id.data,
                "location": None,
                "term": None
            },
            "link": form.link.data
        }
        egc_data.create_document(new_document)
        return redirect(url_for('document_list'))
    return render_template('create_document.html', form=form,
        errors=form.errors)

@app.route('/documents/<document_id>/edit', methods=['GET', 'POST'])
def edit_document(document_id):
  if egc_data is None:
    return redirect(url_for('load_egc_file'))
  else:
    document = egc_data.get_document(document_id)
    if document is None:
        abort(404)
    form = DocumentForm(request.form,
        egc_data=egc_data, old_id = document_id,
        data={"document_id": document["document_id"]["item"],
              "link": document["link"]})
    if request.method == 'POST' and form.validate():
        updated_document = {
            "record_type": "D",
            "document_id": {
                "resource_prefix": "PMID",
                "item": form.document_id.data,
                "location": None,
                "term": None
            },
            "link": form.link.data
        }
        egc_data.update_document(document_id, updated_document)
        return redirect(url_for('document_list'))
    return render_template('edit_document.html', form=form,
        errors=form.errors)

@app.route('/documents/<document_id>/delete', methods=['POST'])
def delete_document(document_id):
  if egc_data is None:
    return redirect(url_for('load_egc_file'))
  else:
    egc_data.delete_document(document_id)
    return redirect(url_for('document_list'))

@app.route('/snippet_tables/create', methods=['GET', 'POST'])
def create_snippet_table():
  if egc_data is None:
    return redirect(url_for('load_egc_file'))
  else:
    form = SnippetTableForm(request.form)
    if request.method == 'POST' and form.validate():
        new_record = {
            "record_type": form.record_type.data,
            "id": form.id.data,
            "document_id": {
                "resource_prefix": "PMID",
                "item": form.document_id.data,
                "location": None,
                "term": None
            }
        }
        if form.record_type.data == "T":
            new_record["table_ref"] = form.contents.data
        elif form.record_type.data == "S":
            new_record["text"] = form.contents.data
        egc_data.create_snippet_table(new_record)
        return redirect(url_for('snippet_table_list'))
    return render_template('create_snippet_table.html', form=form)

@app.route('/snippet_tables/<record_id>/edit', methods=['GET', 'POST'])
def edit_snippet_table(record_id):
  if egc_data is None:
    return redirect(url_for('load_egc_file'))
  else:
    snippet_table = egc_data.get_snippet_table(record_id)
    if snippet_table is None:
        abort(404)

    form = SnippetTableForm(request.form, data={
        "record_type": snippet_table["record_type"],
        "document_id": snippet_table["document_id"]["item"],
        "id": snippet_table["id"],
        "contents": snippet_table.get("contents", ""),
    })
    if request.method == 'POST' and form.validate():
        updated_snippet_table = {
            "record_type": form.record_type.data,
            "id": form.id.data,
            "document_id": {
                "resource_prefix": "PMID",
                "item": form.document_id.data,
                "location": None,
                "term": None
            }}
        if form.record_type.data == "T":
            updated_snippet_table["table_ref"] = form.contents.data
        elif form.record_type.data == "S":
            updated_snippet_table["text"] = form.contents.data
        egc_data.update_snippet_table(record_id, updated_snippet_table)
        return redirect(url_for('snippet_table_list'))
    return render_template('edit_snippet_table.html', form=form)

@app.route('/snippet_tables/<record_id>/delete', methods=['POST'])
def delete_snippet_table(record_id):
  if egc_data is None:
    return redirect(url_for('load_egc_file'))
  else:
    egc_data.delete_snippet_table(record_id)
    return redirect(url_for('snippet_table_list'))

if __name__ == '__main__':
  app.run()
