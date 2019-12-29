import sys
import os
import gi
import re
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
try:
  import json
except:
  import simplejson as json
  pass

raw_data = ''
from_stdin = False

is_dark = Gtk.Settings.get_default().get_property("gtk-application-prefer-dark-theme")
if is_dark:
  color_array = 'yellow'
  color_type = 'orange'
  color_string = 'pink'
  color_integer = 'red'
  color_object = 'yellow'
  color_key = 'light green'
else:
  color_array = 'magenta'
  color_type = 'orange'
  color_string = 'purple'
  color_integer = 'red'
  color_object = 'blue'
  color_key = 'dark green'

def add_item(key, data, model, parent = None):
  if isinstance(data, dict):
    if len(key):
      obj = model.append(parent, ['<span foreground="'+color_object+'">'
                                  + str(key) + '</span>' +
                                  ' <span foreground="'+color_type+'"><b>{}</b></span>'])
      walk_tree(data, model, obj)
    else:
      walk_tree(data, model, parent)
  elif isinstance(data, list):
    arr = model.append(parent, ['<span foreground="'+color_array+'">'+ key + '</span> '
                                '<span foreground="'+color_type+'"><b>[]</b></span> ' +
                                '<span foreground="'+color_integer+'">' + str(len(data)) + '</span>'])
    for index in range(0, len(data)):
      add_item('', data[index], model, model.append(arr, ['<b><span foreground="'+color_type+'">'+'['+'</span></b><span foreground="'+color_integer+'">'
                                                          + str(index)
                                                          + '</span><b><span foreground="'+color_type+'">]</span></b>']))
  elif isinstance(data, str):
    if len(data) > 256:
      data = data[0:255] + "..."
      if len(key):
        model.append(parent, ['<span foreground="'+color_key+'">"' + key + '"</span>' +
                            '<b>:</b> <span foreground="'+color_string+'">"' + data + '"</span>'])
      else:
        model.append(parent, ['<span foreground="'+color_string+'">"' + data + '"</span>'])
    else:
      if len(key):
        model.append(parent, ['<span foreground="'+color_key+'">"' + key + '"</span>' +
                            '  <b>:</b> <span foreground="'+color_string+'">"' + data + '"</span>'])
      else:
        model.append(parent, ['<span foreground="'+color_string+'">"' + data + '"</span>'])

  elif isinstance(data, int) or isinstance(data, float):
    model.append(parent, ['<span foreground="'+color_key+'">"' + key + '"</span>' +
                          '  <b>:</b> <span foreground="'+color_integer+'">' + str(data) + '</span>'])
  else:
    model.append(parent, [str(data)])

def walk_tree(data, model, parent = None):
  if isinstance(data, list):
    add_item('', data, model, parent)
  elif isinstance(data, dict):
    for key in sorted(data):
      add_item(key, data[key], model, parent)
  else:
    add_item('', data, model, parent)

# Key/property names which match this regex syntax may appear in a
# JSON path in their original unquoted form in dotted notation.
# Otherwise they must use the quoted-bracked notation.
jsonpath_unquoted_property_regex = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")

#return the json query given a path
def to_jq(path, data):
  indices = path.get_indices()
  jq = ''
  is_array_index = False

  #the expression must begins with identity `.`
  #if the first element is not a dict, add a dot
  if not isinstance(data, dict):
    jq += '.'

  for index in indices:
    if isinstance(data, dict):
      key = (list(sorted(data))[index])
      if len(key)==0 or not jsonpath_unquoted_property_regex.match(key):
        jq += '[\'{}\']'.format(key) # bracket notation (no initial dot)
      else:
        jq += '.' + key # dotted notation
      data = data[key]
      if isinstance(data, list):
        jq += '[]'
        is_array_index = True
    elif isinstance(data, list):
      if is_array_index:
        selected_index = index
        jq = jq[:-2]   #remove []
        jq += '[{}]'.format(selected_index)
        data = data[selected_index]
        is_array_index = False
      else:
        jq += '[]'
        is_array_index = True

  return jq

class JSONViewerBox(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self)
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.label_info = Gtk.Label()
        self.data = {}

        column_title = ''

        try:
          self.parse_json(raw_data)
        except Exception as e:
          self.label_info.set_text(str(e))
        else:
          self.label_info.set_text("No data loaded")

        self.last_box = None
        self.rebuild(self.data)

    def parse_json(self, data):
        self.data = json.loads(data)

    def rebuild(self, data):
        if not (self.last_box is None):
            self.remove(self.last_box)

        self.model = Gtk.TreeStore(str)
        self.swintree = Gtk.ScrolledWindow()
        self.tree = Gtk.TreeView(self.model)

        self.cell = Gtk.CellRendererText()

        self.tvcol = Gtk.TreeViewColumn('', self.cell, markup=0)

        self.tree_selection = self.tree.get_selection()
        self.tree_selection.set_mode(Gtk.SelectionMode.NONE)
        self.tree.append_column(self.tvcol)

        self.last_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.last_box.pack_start(self.swintree, True, True, 1)
        self.swintree.add(self.tree)
        self.add(self.last_box)
        self.swintree.set_hexpand(True)
        self.swintree.set_vexpand(True)

        walk_tree(self.data, self.model)


if __name__ == "__main__":
  glade_file = "/home/safoex/Documents/glade_works/abtm/json_viewer.glade"
  builder = Gtk.Builder()
  builder.add_from_file(glade_file)
  # builder.connect_signals(Handler())

  window = builder.get_object("window")
  window.connect('destroy', Gtk.main_quit)
  tree_box = builder.get_object('JSONViewerBox')

  jvb = JSONViewerBox()
  tree_box.add(jvb)
  data = """
    {"time": 1043}
  """
  jvb.rebuild(json.loads(data))

  window.connect("delete-event", Gtk.main_quit)
  window.show_all()
  Gtk.run()
