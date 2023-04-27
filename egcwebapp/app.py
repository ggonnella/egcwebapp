from flask import Flask, render_template, request, redirect, jsonify, \
                  url_for, abort, send_from_directory, flash
import egcwebapp.forms
from egctools.egcdata import EGCData
from pathlib import Path
import os
import functools
from egcwebapp.nav import configure_nav
from egcwebapp.record_kinds import record_kind_info
from egcwebapp.context import common_context_processors, \
                              column_context_processors

def create_app():
  app = Flask(__name__)
  configure_nav(app)
  app.egc_data = None
  app.secret_key = 'secret_key'
  app.config['UPLOAD_FOLDER'] = str(Path(app.instance_path) / 'uploads')
  if os.environ.get('EGCWEBAPP') == 'development':
    app.debug = True
    this_dir = Path(__file__).parent
    app.egc_data = EGCData.from_file(str(this_dir.parent / "development.egc"))

  @app.template_filter()
  def basename(path):
    return os.path.basename(path)

  app.context_processor(common_context_processors)
  app.context_processor(column_context_processors)

  def column_context_processor(record_kind, column):
    procs = column_context_processors()
    names = [p.__name__ for p in procs.values()]
    if f"{record_kind}_{column}" in names:
      return procs[f"{record_kind}_{column}"]
    elif f"record_{column}" in names:
      return procs[f"record_{column}"]
    else:
      return None
  app.jinja_env.globals.update(\
      column_context_processor=column_context_processor)

  @app.route('/')
  def index():
      return redirect(url_for('document_list'))

  @app.route('/load_egc_file', methods=['GET', 'POST'])
  def load_egc_file():
      if request.method == 'POST':
          file = request.files['file']
          file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
          file.save(file_path)
          app.egc_data = EGCData.from_file(file_path)
          return redirect(url_for('document_list'))
      return render_template('load_egc_file.html')

  def require_egc_data(func):
      @functools.wraps(func)
      def wrapper(*args, **kwargs):
          if app.egc_data is None:
              return redirect(url_for('load_egc_file'))
          else:
              return func(*args, **kwargs)
      return wrapper

  @app.route('/save_egc_file')
  @require_egc_data
  def save_egc_file():
      return send_from_directory(
          app.config['UPLOAD_FOLDER'],
          os.path.basename(app.egc_data.file_path),
          mimetype='application/egc')

  @app.route('/process_egc_data', methods=['POST'])
  def process_egc_data():
      data = request.get_json()
      file_path = os.path.join(app.config['UPLOAD_FOLDER'], data['filename'])
      with open(file_path, 'w') as f:
          f.write(data['contents'])
      app.egc_data = EGCData.from_file(file_path)
      return 'OK', 200

  @app.route('/get_egc_data/')
  def get_egc_data():
      with open(app.egc_data.file_path) as f:
          contents = f.read()
      filename = os.path.basename(app.egc_data.file_path)
      return jsonify({'contents': contents, 'filename': filename})

  record_kinds = list(record_kind_info.keys())

  #
  # The following web routes are defined for each type of record:
  #
  # /<record_type>s                       table of all records of a given type
  # C /<record_type>s/create              form to create a new record
  # R /<record_type>s/<record_id>         page showing a single record
  # U /<record_type>s/<record_id>/edit    page for editing a single record
  # D /<record_type>s/<record_id>/delete  deletes a single record
  #
  # Additionally api routes are defined for each type of record
  #

  def list_route(record_kind):
    def route_function():
      records = []
      for record_type in record_kind_info[record_kind]["record_types"]:
        records.extend(app.egc_data.find_all(record_type))
      return render_template('list.html',
              **{"records": records, 'egc_data': app.egc_data,
                 'record_kind': record_kind,
                 'info': record_kind_info[record_kind]})

    route_function.__name__ = f"{record_kind}_list"
    route_function = app.route(f"/{record_kind}s",
        methods=["GET"])(require_egc_data(route_function))
    return route_function

  def create_route(record_kind):
    def route_function():
        prev = request.args.get('previous_page') or f'{record_kind}_list'
        form_class = getattr(egcwebapp.forms,
                             f"{record_kind.capitalize()}Form")
        form = form_class(request.form, egc_data=app.egc_data)
        if hasattr(form, 'auto_generate_id'):
          form.auto_generate_id()
        if request.method == "POST" and form.validate():
            new_record = form.to_record()
            app.egc_data.create(new_record)
            app.egc_data.save()
            return redirect(url_for(prev))
        title_label = record_kind_info[record_kind]["title"]
        return render_template("record_form.html", form=form,
            egc_data=app.egc_data,
            errors=form.errors, previous_page=prev,
            info=record_kind_info[record_kind],
            title_label=f"Create {title_label}",
        )

    route_function.__name__ = f"create_{record_kind}"
    route_function = app.route(f"/{record_kind}s/create",
        methods=["GET", "POST"])(require_egc_data(route_function))
    return route_function

  def edit_record_route(record_kind):
    def route_function(record_id):
        record = app.egc_data.find(record_id) or abort(404)
        prev = request.args.get('previous_page') or f'{record_kind}_list'
        form_class = getattr(egcwebapp.forms,
                             f"{record_kind.capitalize()}Form")
        form = form_class.from_record(request.form, record,
                          egc_data=app.egc_data, old_id=record_id)
        if request.method == 'POST' and form.validate():
            updated_data = form.to_record()
            app.egc_data.update(record_id, updated_data)
            app.egc_data.save()
            return redirect(url_for(prev))
        title_label = record_kind_info[record_kind]["title"]
        return render_template('record_form.html', form=form,
                    egc_data=app.egc_data,
                    errors=form.errors, previous_page=prev,
                    info=record_kind_info[record_kind],
                    title_label=f'Edit {title_label}')

    route_function.__name__ = f'edit_{record_kind}'
    route_function = app.route(f'/{record_kind}s/<record_id>/edit',
        methods=['GET', 'POST'])(require_egc_data(route_function))
    return route_function

  def edit_record_api_route(record_kind):
    def route_function(record_id):
        record = app.egc_data.find(record_id) or abort(404)
        form_class = getattr(egcwebapp.forms,
                             f"{record_kind.capitalize()}Form")
        form = form_class.from_record(request.form, record,
                          egc_data=app.egc_data, old_id=record_id)
        form_html = render_template('nested_record_form.html', form=form,
                    egc_data=app.egc_data, errors=form.errors,
                    info=record_kind_info[record_kind],
                    record_kind=record_kind, record_id=record_id)
        return form_html

    route_function.__name__ = f'edit_{record_kind}_api'
    route_function = app.route(f'/api/{record_kind}s/<record_id>/edit',
        methods=['GET'])(require_egc_data(route_function))
    return route_function

  def update_record_api_route(record_kind):
    def route_function(record_id):
        record = app.egc_data.find(record_id) or abort(404)
        form_class = getattr(egcwebapp.forms,
                             f"{record_kind.capitalize()}Form")
        form = form_class.from_record(request.form, record,
                          egc_data=app.egc_data, old_id=record_id)
        if hasattr(form, 'auto_generate_id'):
          form.auto_generate_id()
        if form.validate():
            updated_data = form.to_record()
            app.egc_data.update(record_id, updated_data)
            app.egc_data.save()
            updated_row_html = render_template("row.html",
                    record=updated_data, record_kind=record_kind,
                    info=record_kind_info[record_kind],
                    egc_data=app.egc_data)
            updated_row_html += render_template("jslinks.html",
                    record_kind=record_kind, info=record_kind_info[record_kind])
            return jsonify({'success': True, 'html': updated_row_html})
        else:
            form_html = render_template('nested_record_form.html', form=form,
                    egc_data=app.egc_data, errors=form.errors,
                    info=record_kind_info[record_kind],
                    record_kind=record_kind, record_id=record_id)
            return jsonify({'success': False, 'html': form_html})

    route_function.__name__ = f'update_{record_kind}_api'
    route_function = app.route(f'/api/{record_kind}s/<record_id>/update',
        methods=['POST'])(require_egc_data(route_function))
    return route_function

  def delete_record_route(record_kind):
    def route_function(record_id):
      previous_page = request.args.get('previous_page') or record_kind + '_list'
      if app.egc_data.is_ref_by(record_id):
        flash(f"Cannot delete {record_id} "+\
               "because it is referenced by other records")
        return redirect(url_for(previous_page))
      app.egc_data.delete(record_id)
      app.egc_data.save()
      return redirect(url_for(previous_page))

    route_function.__name__ = f'delete_{record_kind}'
    route_function = app.route(f'/{record_kind}s/<record_id>/delete', \
        methods=['POST'])(require_egc_data(route_function))
    return route_function

  def show_record_route(record_kind):
    def route_function(record_id):
        record = app.egc_data.find(record_id) or abort(404)
        return render_template('show.html',
                **{"records": [record], 'egc_data': app.egc_data,
                   'record_kind': record_kind, 'record_id': record_id,
                   'info': record_kind_info[record_kind],
                   'record_title': record_kind_info[record_kind]['title']})

    route_function.__name__ = f'show_{record_kind}'
    route_function = app.route(f'/{record_kind}s/<record_id>', \
        methods=['GET'])(require_egc_data(route_function))
    return route_function

  def get_record_route(record_kind):
    def route_function(record_id):
        record = app.egc_data.find(record_id) or abort(404)
        return render_template('table.html',
            **{'record': record, 'egc_data': app.egc_data,
               'record_kind': record_kind, 'record_id': record_id,
               'info': record_kind_info[record_kind],
              })

    route_function.__name__ = f'get_{record_kind}'
    route_function = app.route(f'/api/{record_kind}s/<record_id>', \
        methods=['GET'])(require_egc_data(route_function))
    return route_function

  def get_ref_route(record_kind):
      def route_function(ancestor_ids, record_id):
          record = app.egc_data.find(record_id) or abort(404)
          return render_template('datatable.html',
              **{"records": [record], 'egc_data': app.egc_data,
                 'record_kind': record_kind,
                 'info': record_kind_info[record_kind],
                 'ancestor_ids': ancestor_ids.split(',')})

      route_function.__name__ = f'get_ref_{record_kind}'
      route_function = app.route(\
          f'/api/ref/<ancestor_ids>/{record_kind}s/<record_id>',
          methods=['GET'])(require_egc_data(route_function))
      return route_function

  def get_refby_route(ref_by_kind, ref_from_kind):
    def route_function(ancestor_ids):
      ref_by_id = ancestor_ids.split(',')[-1]
      ref_by_record = app.egc_data.find(ref_by_id) or abort(404)
      ref_by_rt = ref_by_record['record_type']
      ref_from_records = []
      for ref_from_rt in record_kind_info[ref_from_kind]["record_types"]:
        ref_from_records.extend(\
            app.egc_data.ref_by(ref_by_rt, ref_by_id, ref_from_rt))
      return render_template('datatable.html',
          **{"records": ref_from_records, 'egc_data': app.egc_data,
             'record_kind': ref_from_kind,
             'info': record_kind_info[ref_from_kind],
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
      edit_record_api_route(record_kind)
      update_record_api_route(record_kind)
      delete_record_route(record_kind)
      show_record_route(record_kind)
      get_record_route(record_kind)
      get_ref_route(record_kind)
      for ref_from_kind in record_kind_info[record_kind]["ref_by_kinds"]:
          get_refby_route(record_kind, ref_from_kind)

  return app

if __name__ == '__main__':
  app = create_app()
  app.run()
