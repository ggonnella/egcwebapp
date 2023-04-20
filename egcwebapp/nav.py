from flask_navigation import Navigation

nav = Navigation()

def configure_nav(app):
    nav.init_app(app)
    nav.Bar('top', [
        nav.Item('Load', 'load_egc_file'),
        nav.Item('Save', 'save_egc_file'),
        nav.Item('Documents', 'document_list'),
        nav.Item('Extracts', 'extract_list'),
        nav.Item('Groups', 'group_list'),
        nav.Item('Units', 'unit_list'),
        nav.Item('Models', 'model_list'),
        nav.Item('Attributes', 'attribute_list'),
        nav.Item('Value Exp.', 'vrule_list'),
        nav.Item('Comp. Exp.', 'crule_list'),
    ])

