import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

from abtm_ui.definitions import ROOT_DIR

from abtm_ui import xdot

import abtm_ui.abtm.abtm_simple
import abtm_ui.abtm.json_viewer
from ruamel import yaml
import roslibpy
from threading import Lock


class ABTMDotWidget(xdot.DotWidget):
    def __init__(self, runtime=False):
        xdot.DotWidget.__init__(self)
        self.dc = abtm_ui.abtm.abtm_simple.DotCoder()
        self.runtime = runtime
        # self.dotwidget.connect('clicked', self.on_click)

    def on_click(self, element, event):
        name = element.id.decode("utf-8")
        if name in self.dc.expanded:
            self.dc.hide_templated_node(name)
        else:
            self.dc.expand_templated_node(name)
        self.set_dotcode(bytes(self.dc.get_dotcode(self.runtime), 'utf-8'))


class ABTMApp:
    def __init__(self, rosparams=None, glade_file=None):
        self.rosparams = rosparams or {'host': 'localhost', 'port': 9090}
        self.glade_file = glade_file or ROOT_DIR + "/abtm/abtm.glade"
        self.vars = {}
        self.mutex = Lock()
        self.is_now_correct = False

    def build_gtk(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(self.glade_file)
        self.window = self.builder.get_object("window")
        self.window.connect('destroy', Gtk.main_quit)
        self.window.set_default_size(900, 800)
        self.window.set_title('A-B-T-M')
        self.tree_widget = ABTMDotWidget()
        self.memory_widget = abtm_ui.abtm.json_viewer.JSONViewerBox()

        self.tree_box = self.tab_widget('TreeBox', self.tree_widget)
        self.memory_box = self.tab_widget('MemoryBox', self.memory_widget)

        self.ex_text_widget = self.builder.get_object('Exception')
        self.ex_image_widget = self.builder.get_object('ExceptionIcon')

    def tab_widget(self, name, widget):
        tab_box = self.builder.get_object(name)
        tab_box.pack_start(widget, True, True, 10)
        widget.set_vexpand(True)
        widget.set_hexpand(True)
        return tab_box

    def setup_ros(self):
        self.ros = roslibpy.Ros(host=self.rosparams['host'], port=self.rosparams['port'])
        self.ros.run()
        self.tree_description_listener = roslibpy.Topic(self.ros, '/abtm/yaml_tree_description', 'std_msgs/String')
        self.tree_description_listener.subscribe(self.on_tree)

        self.exception_listener = roslibpy.Topic(self.ros, '/abtm/exception', 'std_msgs/String')
        self.exception_listener.subscribe(self.on_exception)

        self.states_listener = roslibpy.Topic(self.ros, '/abtm/yaml_state_changes', 'std_msgs/String')
        self.states_listener.subscribe(self.on_states)

        self.vars_listener = roslibpy.Topic(self.ros, '/abtm/yaml_var_changes', 'std_msgs/String')
        self.vars_listener.subscribe(self.on_vars)

        self.command_publisher = roslibpy.Topic(self.ros, '/abtm/yaml_command', 'std_msgs/String')
        self.main_file_publisher = roslibpy.Topic(self.ros, '/abtm/main_file', 'std_msgs/String')

    def on_vars(self, message):
        with self.mutex:
            vars = yaml.safe_load(message['data'])
            self.vars.update(vars)
            for v in self.vars.keys():
                if v[:9] == "__STATE__":
                    self.tree_widget.dc.states[v[9:]] = self.vars[v]
            self.memory_widget.data = self.vars
            self.vars_view_refresh()

    def vars_view_refresh(self):
        self.memory_widget.model.clear()
        abtm_ui.abtm.json_viewer.walk_tree(self.memory_widget.data, self.memory_widget.model)
        self.memory_widget.tree.set_model(self.memory_widget.model)

    def on_tree(self, message):
        with self.mutex:
            self.is_now_correct = True
            self.tree_widget.dc.tree_from_nodes(message['data'])
            self.tree_widget.set_dotcode(bytes(self.tree_widget.dc.get_dotcode(), 'utf-8'))
            self.ex_image_widget.set_from_stock(Gtk.STOCK_APPLY, Gtk.IconSize.LARGE_TOOLBAR)
            self.ex_text_widget.set_text('ready')

    def on_states(self, message):
        with self.mutex:
            self.tree_widget.dc.set_states(message['data'])
            rt_dotcode = self.tree_widget.dc.get_dotcode(True)
            self.tree_widget.set_dotcode(bytes(rt_dotcode, 'utf-8'))

    def on_exception(self, message):
        with self.mutex:
            self.is_now_correct = False
            self.ex_text_widget.set_text(message['data'])
            self.ex_image_widget.set_from_stock(Gtk.STOCK_DIALOG_WARNING, Gtk.IconSize.LARGE_TOOLBAR)

    def get_button_cb(self, word):
        return lambda _: self.command_publisher.publish(roslibpy.Message({'data': word}))

    def setup_buttons(self):
        self.buttons = {}
        for word in ['start', 'pause', 'stop', 'vars']:
            self.buttons[word] = self.builder.get_object('rt_' + word)
            self.buttons[word].connect('clicked', self.get_button_cb(word))

        self.buttons['open'] = self.builder.get_object('open')
        self.buttons['open'].connect('clicked', self.on_file)

        tick_btns = ['compact', 'details', 'states', 'names']
        for btn in tick_btns:
            self.buttons[btn] = self.builder.get_object('t_' + btn)
            self.buttons[btn].connect('toggled', self.get_tick_button_cb(btn))

    def get_tick_button_cb(self, btn):
        def f(widget, data=None):
            return self.tick_button_cb(btn, widget, data)

        return f

    def tick_button_cb(self, btn, widget, data=None):
        self.tree_widget.dc.view_params[btn] = widget.get_active()
        if self.is_now_correct:
            self.tree_widget.set_dotcode(bytes(self.tree_widget.dc.get_dotcode(), 'utf-8'))

    def on_file(self, widget):
        dlg = Gtk.FileChooserDialog("Open..", None, Gtk.FileChooserAction.OPEN,
                                    (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        response = dlg.run()
        if response == Gtk.ResponseType.OK:
            self.main_file_publisher.publish(roslibpy.Message({'data': dlg.get_filename()}))
            self.builder.get_object('choosed-file').set_text(dlg.get_filename())
        dlg.destroy()

    def setup_all(self, with_ros=True, icon=ROOT_DIR + "/abtm/abtm.png"):
        self.build_gtk()
        if with_ros:
            self.setup_ros()
        self.setup_buttons()
        self.set_icon(icon)

    def request_tree(self):
        self.command_publisher.publish(roslibpy.Message({'data': 'tree'}))

    def set_icon(self, icon_path):
        self.window.set_icon_from_file(icon_path)

    def run(self):
        self.window.show_all()
        Gtk.main()
