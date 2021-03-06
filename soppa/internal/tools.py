import os, sys, inspect
from importlib import import_module
import fnmatch

def here(path=None, fn=None, instance=None):
    """ Evaluate path relative to where function was called
    fn = provide scope ('source')
    """
    if instance:
        calling_file = inspect.getfile(instance.__class__)
    elif fn:
        calling_file = fn
    else:
        calling_file = inspect.getfile(sys._getframe(1)) # relative or absolute return value
    calling_file = os.path.abspath(calling_file)
    subfolder = path.lstrip('/') if path else ''
    return os.path.join(os.path.dirname(calling_file), subfolder)

def import_string(dotted_path):
    """ Import something, eg. 'soppa.pip', or 'x.y.z' """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except (ValueError, AttributeError) as e:
        module_path = dotted_path
    try:
        return import_module(dotted_path)
    except ImportError, e:
        module = import_module(module_path)
        try:
            return getattr(module, class_name)
        except ImportError, e:
            log.debug(e)

class Upload(object):
    """ Upload a template """
    def __init__(self, frm, to, instance, caller_path):
        self.instance = instance
        self.args = (frm, to)
        self.caller_path = caller_path

        self.up()

    def config_dirs(self):
        dirs = []
        dirs.append(os.path.join(self.instance.soppa.basedir,
            self.instance.soppa.local_conf_path,
            self.instance.get_name(), ''))
        dirs.append(os.path.join(self.instance.soppa.local_path,
            self.instance.soppa.local_conf_path,
            self.instance.get_name(), ''))
        dirs.append(os.path.join(self.instance.module_path(),
            self.instance.soppa.local_conf_path, ''))
        dirs += self.instance.soppa.config_dirs
        return dirs

    def find(self, path, needle):
        matches = []
        for root, dirnames, filenames in os.walk(path):
            for filename in fnmatch.filter(filenames, needle):
                matches.append(os.path.join(root, filename))
        return matches

    def choose_template(self):
        filename = self.args[0].split('/')[-1]
        filepath = os.path.join(self.caller_path, self.args[0])
        rs = []
        for k in self.config_dirs():
            rs += self.find(k, filename)
        if rs:
            filepath = '{0}'.format(rs[0])
        return filepath

    def up(self):
        from_path = self.instance.fmt(self.args[0])
        if not from_path.startswith('/'):
            filepath = self.choose_template()
            self.args = (filepath,) + self.args[1:]
        self.args = tuple([self.instance.fmt(k) for k in self.args])

class ObjectDict(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            # to conform with __getattr__ spec
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value

def get_full_dict(obj):
    return dict(sum([cls.__dict__.items() for cls in obj.__class__.__mro__ if cls.__name__ != "object"], obj.__dict__.items()))

def get_class_dict(obj):
    return dict({k:v for k,v in obj.__dict__.iteritems() if not k.startswith('__')})

def is_configurable_property(key, value):
    if key.startswith('__') \
        or callable(value) \
        or isinstance(value, property) \
        or isinstance(value, staticmethod):
            return False
    return True

def get_namespaced_class_values(obj):
    values = get_full_dict(obj.__class__)
    vals = {}
    for k,v in values.iteritems():
        if not is_configurable_property(k, v):
            continue
        if k in obj.reserved_keys:
            continue
        vals[k] = v
    return vals

def fmt_namespaced_values(obj, vals):
    namespace = obj.get_name()
    namespaced_vals = {}
    for k,v in vals.iteritems():
        value = obj.fmt(v)
        if not k.startswith('{}_'.format(namespace)):
            k = '{}_{}'.format(namespace, k)
        namespaced_vals[k] = value
    return namespaced_vals

def generate_config(module, include_cls=[], include_vars=[], exclude_vars=[], fmt=True):
    c = {}
    for k in include_cls:
        for key,val in get_class_dict(k).iteritems():
            c[key] = getattr(module, key, val)# actual values from module, default to include
    for k in [module] + module.get_needs():
        for key,val in k.__dict__.iteritems():
            if key.startswith('{}_'.format(k.get_name())):
                c[key] = val
    cf = {}
    for k,v in c.iteritems():
        if not is_configurable_property(k, v):
            continue
        if k in module.reserved_keys:
            continue
        if k in exclude_vars:
            continue
        if v is None:
            continue
        if '__' in k:
            continue
        if fmt:
            v = module.fmt(v)
        cf[k] = v
    return cf

