



import os
import gtk
import charts
import utils
import netview
import runview
from exportri import place_counter_name


class RunGroupView(gtk.VBox):
    
    def __init__(self, group, app):
        gtk.VBox.__init__(self)
        self.group = group
        self.group_views =[]
        self.views = []
        self.tracelog = None
        
        button = gtk.Button("Export sequence")
        button.connect("clicked", lambda w:
                app.save_sequence_into_project(self.export_sequence()))

        self.netinstance_view = netview.NetView(app, None, other_widgets=[button])            
        self.netinstance_view.set_config(
            netview.NetViewCanvasConfig(self.netinstance_view))
        for source in self.group._sources:
            self.netinstance_view.set_runinstance(source.data.first_runinstance)
        
        self.group_views.append(self.group_time_graph_view(self.group._sources))
        self.group_views.append(self.group_amount_data_view(self.group._sources))
        self.group_views.append(self.group_histogram_view(self.group._sources))
        
        self.pack_start(self._controls(self.group), False, False)
        for name, item in self.group_views:
            self.pack_start(item)

    def _controls(self, group):
        list_sources = group._sources
        for source in list_sources:
            self.scale = gtk.HScale(gtk.Adjustment(value=0, lower=0,
                upper=source.data.get_runinstances_count(), step_incr=1, page_incr=1, page_size=1))
            toolbar = gtk.HBox(False)
        
        self.combo1 = gtk.combo_box_new_text()
        self.combo1.append_text("{0}".format(group.name))
        for source in list_sources:
            self.combo1.append_text(os.path.basename(source.name))
        self.combo1.set_active(0)
        self.combo1.connect("changed", self._change_source)
        toolbar.pack_start(self.combo1, False, False)

        self.combo2 = gtk.combo_box_new_text()
        self.combo2.append_text("Select graph")
        for name, item in self.group_views:
            self.combo2.append_text(name)
        self.combo2.set_active(0)
        self.combo2.connect("changed", self._view_change)
        toolbar.pack_start(self.combo2, False, False)        
        
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
        if text == "Replay":
                    self.button1.show()
                    self.button2.show()
                    self.scale.show()
        for name, item in self.views:
            if name == text:
                item.show_all()
                if isinstance(item, charts.ChartWidget):
                    # set focus on graph canvas
                    item.get_figure().canvas.grab_focus()
            else:
                item.hide()
        for name, item in self.group_views:
            if name == text:
                item.show_all()
                if isinstance(item, charts.ChartWidget):
                    # set focus on graph canvas
                    item.get_figure().canvas.grab_focus()
            else:
                item.hide()
                
    def _change_source(self, w):
        views = []
        text = w.get_active_text()
        for source in self.group._sources:
            if os.path.basename(source.name)== text:
                self.tracelog = source.data
                table = self.tracelog.data
        
                net = self.tracelog.project.nets[0]
                processes = range(self.tracelog.process_count)
                transitions = [ t for t in net.transitions() if t.trace_fire ]
                places = [ p for p in net.places() if p.trace_tokens ]

                if len(self.views) == 0:
                    views = [ ("Replay", self.netinstance_view) ]
                    views.append(runview.process_utilization(table, processes))
                    views.append(runview.transition_utilization(table, processes, transitions))
                    views.append(runview.tet_per_processes_and_transitions_histogram(
                        table, processes, transitions))
                    views.append(runview.tet_per_processes_histogram(table, processes))
                    views.append(runview.tet_per_transitions_histogram(table, transitions))
                    views.append(runview.tokens_count(table, processes, places))
                    self.views = views    
                    for name, item in views:
                        self.pack_start(item)
                        
                for x in xrange(len(self.views)):
                    self.combo2.remove_text(0)
                for name, item in self.views:
                    self.combo2.append_text(name)        

        if text == self.group.name:
            self.scale.set_value(max(0,self.get_event_index()-self.get_event_index()))
            self.tracelog = None
            self.button1.hide()
            self.button2.hide()
            self.scale.hide()
            self.counter_label.set_text("")
            self.info_label.set_markup("")
            for x in xrange(len(self.views)):
                    self.combo2.remove_text(0)
            
            for name, item in self.group_views:
                    self.combo2.append_text(name)

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
    
    def group_amount_data_view(self, list_tracelogs):
        return ("Group amount data graph", charts.group_amount_data_chart(list_tracelogs))

    def group_histogram_view(self, list_tracelogs):
        return ("Group histogram graph", charts.group_histogram_chart(list_tracelogs))