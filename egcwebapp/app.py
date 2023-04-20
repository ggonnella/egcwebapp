from flask import Flask, render_template, request, redirect, \
                  url_for, abort, send_from_directory
import egcwebapp.forms
from egctools.egcdata import EGCData
from pathlib import Path
import os
import functools
from egcwebapp.nav import configure_nav

def create_app():
  app = Flask(__name__)
  configure_nav(app)
  egc_data = None
  app.secret_key = 'secret_key'
  app.config['UPLOAD_FOLDER'] = str(Path(app.instance_path) / 'uploads')
  if os.environ.get('EGCWEBAPP') == 'development':
    app.debug = True
    this_dir = Path(__file__).parent
    egc_data = EGCData.from_file(str(this_dir.parent / "development.egc"))

  from egcwebapp.context import processors
  app.context_processor(functools.partial(processors, egc_data=egc_data))

  # The following web routes are defined for each type of record:
  #
  # /<record_type>s                       table of all records of a given type
  # C /<record_type>s/create              form to create a new record
  # R /<record_type>s/<record_id>         page showing a single record
  # U /<record_type>s/<record_id>/edit    page for editing a single record
  # D /<record_type>s/<record_id>/delete  deletes a single record
  #

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

  def require_egc_data(func):
      @functools.wraps(func)
      def wrapper(*args, **kwargs):
          if egc_data is None:
              return redirect(url_for('load_egc_file'))
          else:
              return func(*args, **kwargs)
      return wrapper

  @app.route('/save_egc_file')
  @require_egc_data
  def save_egc_file():
      return send_from_directory(
          app.config['UPLOAD_FOLDER'],
          os.path.basename(egc_data.file_path),
          mimetype='application/egc')

  record_kind_info = {
      'document': {"title": 'Document',
                   "record_types": ['D'],
                   "ref_by_kinds": ['extract']},
      'extract': {"title": 'Document Extract',
                  "record_types": ['S', 'T'],
                  "ref_by_kinds": ['crule', 'vrule']},
      'unit': {"title": "Unit",
               "record_types": ['U'],
               "ref_by_kinds": ['unit', 'attribute', 'model']},
      'attribute': {"title": "Attribute",
                    "record_types": ['A'],
                    "ref_by_kinds": ['vrule', 'crule']},
      'group': {"title": "Group",
                "record_types": ['G'],
                "ref_by_kinds": ['group', 'vrule', 'crule']},
      'model': {"title": "Model",
                "record_types": ['M'],
                "ref_by_kinds": []},
      'vrule': {"title": "Value Expectation Rule",
                "record_types": ['V'],
                "ref_by_kinds": []},
      'crule': {"title": "Comparative Expectation Rule",
                "record_types": ['C'],
                "ref_by_kinds": []},
  }

  record_kinds = list(record_kind_info.keys())

  def list_route(record_kind):
    def route_function():
      records = []
      for record_type in record_kind_info[record_kind]["record_types"]:
        records.extend(egc_data.get_records(record_type))
      return render_template(f'list_{record_kind}.html',
              **{record_kind+"s": records, 'egc_data': egc_data})

    route_function.__name__ = f"{record_kind}_list"
    route_function = app.route(f"/{record_kind}s",
        methods=["GET"])(require_egc_data(route_function))
    return route_function

  def create_route(record_kind):
    def route_function():
        prev = request.args.get('previous_page') or f'{record_kind}_list'
        form_class = getattr(egcwebapp.forms,
                             f"{record_kind.capitalize()}Form")
        form = form_class(request.form, egc_data=egc_data)
        if request.method == "POST" and form.validate():
            new_record = form.to_record()
            egc_data.create_record(new_record)
            return redirect(url_for(prev))
        title_label = record_kind_info[record_kind]["title"]
        return render_template("record_form.html", form=form, egc_data=egc_data,
            errors=form.errors, previous_page=prev,
            title_label=f"Create {title_label}",
        )

    route_function.__name__ = f"create_{record_kind}"
    route_function = app.route(f"/{record_kind}s/create",
        methods=["GET", "POST"])(require_egc_data(route_function))
    return route_function

  def edit_record_route(record_kind):
    def route_function(record_id):
        record = egc_data.get_record_by_id(record_id) or abort(404)
        prev = request.args.get('previous_page') or f'{record_kind}_list'
        form_class = getattr(egcwebapp.forms,
                             f"{record_kind.capitalize()}Form")
        form = form_class.from_record(request.form, record,
                          egc_data=egc_data, old_id=record_id)
        if request.method == 'POST' and form.validate():
            updated_data = form.to_record()
            egc_data.update_record_by_id(record_id, updated_data)
            return redirect(url_for(prev))
        title_label = record_kind_info[record_kind]["title"]
        return render_template('record_form.html', form=form, egc_data=egc_data,
                    errors=form.errors, previous_page=prev,
                    title_label=f'Edit {title_label}')

    route_function.__name__ = f'edit_{record_kind}'
    route_function = app.route(f'/{record_kind}s/<record_id>/edit',
        methods=['GET', 'POST'])(require_egc_data(route_function))
    return route_function

  def delete_record_route(record_kind):
    def route_function(record_id):
      egc_data.delete_record_by_id(record_id)
      previous_page = request.args.get('previous_page') or record_kind + '_list'
      return redirect(url_for(previous_page))

    route_function.__name__ = f'delete_{record_kind}'
    route_function = app.route(f'/{record_kind}s/<record_id>/delete', \
        methods=['POST'])(require_egc_data(route_function))
    return route_function

  def show_record_route(record_kind):
    def route_function(record_id):
        record = egc_data.get_record_by_id(record_id) or abort(404)
        return render_template(f'show_{record_kind}.html',
            **{record_kind: record, 'egc_data': egc_data})

    route_function.__name__ = f'show_{record_kind}'
    route_function = app.route(f'/{record_kind}s/<record_id>', \
        methods=['GET'])(require_egc_data(route_function))
    return route_function

  def get_record_route(record_kind):
    def route_function(record_id):
        record = egc_data.get_record_by_id(record_id) or abort(404)
        return render_template(f'table_{record_kind}.html',
            **{record_kind: record, 'egc_data': egc_data})

    route_function.__name__ = f'get_{record_kind}'
    route_function = app.route(f'/api/{record_kind}s/<record_id>', \
        methods=['GET'])(require_egc_data(route_function))
    return route_function

  def get_ref_route(record_kind):
      def route_function(ancestor_ids, record_id):
          record = egc_data.get_record_by_id(record_id) or abort(404)
          return render_template(f'datatable_{record_kind}.html',
              **{record_kind+"s": [record], 'egc_data': egc_data,
                 'ancestor_ids': ancestor_ids.split(',')})

      route_function.__name__ = f'get_ref_{record_kind}'
      route_function = app.route(\
          f'/api/ref/<ancestor_ids>/{record_kind}s/<record_id>',
          methods=['GET'])(require_egc_data(route_function))
      return route_function

  def get_refby_route(ref_by_kind, ref_from_kind):
    def route_function(ancestor_ids):
      ref_by_id = ancestor_ids.split(',')[-1]
      ref_by_record = egc_data.get_record_by_id(ref_by_id) or abort(404)
      ref_by_rt = ref_by_record['record_type']
      ref_from_records = []
      for ref_from_rt in record_kind_info[ref_from_kind]["record_types"]:
        ref_from_records.extend(\
            egc_data.ref_by(ref_by_rt, ref_by_id, ref_from_rt))
      return render_template(f'datatable_{ref_from_kind}.html',
          **{ref_from_kind+"s": ref_from_records, 'egc_data': egc_data,
             'ancestor_ids': ancestor_ids.split(',')})

    route_function.__name__ = f'get_{ref_by_kind}_{ref_from_kind}s'
    route_function = \
      app.route(f'/api/{ref_by_kind}s/<ancestor_ids>/{ref_from_kind}s', \
        methods=['GET'])(require_egc_data(route_function))
    return route_function

  for record_kind in record_kinds:
      list_route(record_kind)
      create_route(record_kind)
      edit_record_route(record_kind)
      delete_record_route(record_kind)
      show_record_route(record_kind)
      get_record_route(record_kind)
      get_ref_route(record_kind)
      for ref_by_kind in record_kind_info[record_kind]["ref_by_kinds"]:
          get_refby_route(ref_by_kind, record_kind)

  return app

if __name__ == '__main__':
  app = create_app()
  app.run()
