



import os
import gtk
import charts
import utils
import netview
from exportri import place_counter_name


class RunGroupView(gtk.VBox):
    
    def __init__(self, list_sources, app):
        gtk.VBox.__init__(self)
        self.list_sources = list_sources
        self.views = []
        self.tracelog = None
        
        button = gtk.Button("Export sequence")
        button.connect("clicked", lambda w:
                app.save_sequence_into_project(self.export_sequence()))
        
        self.netinstance_view = netview.NetView(app, None, other_widgets=[button])            
        self.netinstance_view.set_config(
            netview.NetViewCanvasConfig(self.netinstance_view))
        for source in self.list_sources:
            self.netinstance_view.set_runinstance(source.data.first_runinstance)
        
        self.views = [ ("Replay", self.netinstance_view) ]
        self.views.append(self.group_time_graph_view(self.list_sources))
        
        self.pack_start(self._controls(self.list_sources), False, False)
        for name, item in self.views:
            self.pack_start(item)

    def _controls(self, list_sources):
        for source in list_sources:
            self.scale = gtk.HScale(gtk.Adjustment(value=0, lower=0,
                upper=source.data.get_runinstances_count(), step_incr=1, page_incr=1, page_size=1))
            toolbar = gtk.HBox(False)

        combo = gtk.combo_box_new_text()
        for name, item in self.views:
            combo.append_text(name)
        combo.set_active(0)
        combo.connect("changed", self._view_change)
        toolbar.pack_start(combo, False, False)
        
        combo = gtk.combo_box_new_text()
        combo.append_text("Select tracelog")
        for source in list_sources:
            combo.append_text(os.path.basename(source.name))
        combo.set_active(0)
        combo.connect("changed", self._change_source)
        toolbar.pack_start(combo, False, False)
        
        self.button1 = gtk.Button("<<")
        self.button1.connect("clicked", lambda w: self.scale.set_value(max(0, self.get_event_index() - 1)))
        toolbar.pack_start(self.button1, False, False)

        self.counter_label = gtk.Label()
        toolbar.pack_start(self.counter_label, False, False)
        
        self.button2 = gtk.Button(">>")
        self.button2.connect("clicked", lambda w:
            self.scale.set_value(min(self.tracelog.get_runinstances_count() - 1,
                                    self.get_event_index() + 1)))
        toolbar.pack_start(self.button2, False, False)

        self.scale.set_draw_value(False)
        self.scale.connect("value-changed", lambda w: self.show_runinstance())
        toolbar.pack_start(self.scale)

        self.info_label = gtk.Label()
        toolbar.pack_start(self.info_label, False, False)
        
        if self.tracelog is not None: 
            self.update_labels()
            
        toolbar.show_all()
        if self.tracelog is None:
            self.button1.hide()
            self.button2.hide()
            self.scale.hide()
            
        return toolbar
    
    def get_event_index(self):
        return int(self.scale.get_value())

    def show_runinstance(self):
        index = self.get_event_index()
        tracelog = self.get_tracelog()
        runinstance = tracelog.get_event_runinstance(index)
        self.netinstance_view.set_runinstance(runinstance)
        self.update_labels()
    
    def export_sequence(self):
        tracelog = self.get_tracelog()
        return tracelog.export_sequence(self.get_event_index())

    def _view_change(self, w):
        text = w.get_active_text()
        for name, item in self.views:
            if name == text:
                item.show_all()
                if isinstance(item, charts.ChartWidget):
                    # set focus on graph canvas
                    item.get_figure().canvas.grab_focus()
            else:
                item.hide()
    
    def _change_source(self, w):
        text = w.get_active_text()
        for source in self.list_sources:
            if os.path.basename(source.name) == text:
                self.tracelog = source.data
                self.button1.show()
                self.button2.show()
                self.scale.show()
        if text == "Select tracelog":
            self.scale.set_value(max(0,self.get_event_index()-self.get_event_index()))
            self.tracelog = None
            self.button1.hide()
            self.button2.hide()
            self.scale.hide()
            self.counter_label.set_text("")
            self.info_label.set_markup("")

    def save_as_svg(self, filename):
        self.netinstance_view.save_as_svg(filename)

    def update_labels(self):
        def format(num, max):
            if num is not None:
                return "{0:0>{1}}".format(num, len(str(max)))
            else:
                return "-" * len(str(max))
            
        tracelog = self.get_tracelog()
        index = self.get_event_index()
        last_index = tracelog.get_runinstances_count() - 1
        m = str(last_index)
        maxtime = utils.time_to_string(tracelog.get_event_time(last_index))
        self.counter_label.set_text("{0:0>{2}}/{1}".format(index, m, len(m)))
        time = "{0:0>{1}}".format(utils.time_to_string(tracelog.get_event_time(index)),
                                  len(maxtime))
        text = "<span font_family='monospace'>{0} {2} {1}</span>".format(
            tracelog.get_event_process(index),
            tracelog.get_event_name(index),
            time)
        self.info_label.set_markup(text)  
        
    def get_tracelog(self):
        return self.tracelog 

    def group_time_graph_view(self, list_tracelogs):
        return ("Group time graph", charts.group_time_chart(list_tracelogs))
        