



import os
import gtk
import charts
import utils
import netview
import runview
#import extensions.tracelogprocessing
from exportri import place_counter_name
from events import EventSource, EventCallbacksList


class RunGroupView(gtk.VBox, EventSource):

    def __init__(self, group, app):
        gtk.VBox.__init__(self)
        EventSource.__init__(self)

        self.group = group
        self.group_views =[]
        self.views = []
        self.source = None
        self.tracelog = None

        self.set_callback("add-source", self._add_source)
        self.set_callback("detach-source", self._detach_source)

        button = gtk.Button("Export sequence")
        button.connect("clicked", lambda w:
                app.save_sequence_into_project(self.export_sequence()))

        self.netinstance_view = netview.NetView(app, None, other_widgets=[button])            
        self.netinstance_view.set_config(
            netview.NetViewCanvasConfig(self.netinstance_view))

        for source in self.group._sources:
            self.netinstance_view.set_runinstance(source.data.first_runinstance)

        self.group_views.append(self.group_transitions_prepare(self.group._sources))
        self.group_views.append(self.group_count_tokens_prepare(self.group._sources))
        self.group_views.append(self.group_transitions_processes_prepare(self.group._sources))

        for name, item in self.group_views:
            self.pack_end(item)

        self.pack_start(self._controls(self.group), False, False)

    def _controls(self, group):
        for source in group._sources:
            self.scale = gtk.HScale(gtk.Adjustment(value=0, lower=0,
                upper=source.data.get_runinstances_count(), step_incr=1, page_incr=1, page_size=1))
            toolbar = gtk.HBox(False)

        self.store = gtk.ListStore(str, object)
        self.store.append([group.name, group])
        for source in group._sources:
            self.store.append([os.path.basename(source.name), [source]])

        self.combo1 = gtk.ComboBox(self.store)
        cell = gtk.CellRendererText()
        self.combo1.pack_start(cell, True)
        self.combo1.add_attribute(cell, 'text', 0)
        self.combo1.set_active(0)
        self.combo1.connect("changed", self._change_source)
        toolbar.pack_start(self.combo1, False, False)

        self.combo2 = gtk.combo_box_new_text()
        self.combo2.append_text("Select chart")
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
        index = w.get_active_iter()
        text = w.get_active_text()
        if index != None:
            model = w.get_model()
            list = model[index][1]
            source = list[0]
            if len(source.name) > 10:
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
                    self.combo2.set_active(0)        

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

            self.combo2.append_text("Select chart")
            for name, item in self.group_views:
                    self.combo2.append_text(name)
                    self.combo2.set_active(0)

    def add_source(self):
        self.emit_event("add-source")

    def detach_source(self):
        self.emit_event("detach-source")

    def _add_source(self):
        self.store.clear()
        self.store.append([self.group.name, self.group])
        for source in self.group._sources:
            self.store.append([os.path.basename(source.name), [source]])

        self.group_views[0] = (self.group_transitions_prepare(self.group._sources))
        self.group_views[1] = (self.group_count_tokens_prepare(self.group._sources))
        self.group_views[2] = (self.group_transitions_processes_prepare(self.group._sources))

        for name, item in self.group_views:
            self.pack_end(item)

        self.combo1.set_active(0)

    def _detach_source(self):
        self.store.clear()
        self.store.append([self.group.name, self.group])
        for source in self.group._sources:
            self.store.append([os.path.basename(source.name), [source]])

        self.group_views[0] = (self.group_transitions_prepare(self.group._sources))
        self.group_views[1] = (self.group_count_tokens_prepare(self.group._sources))
        self.group_views[2] = (self.group_transitions_processes_prepare(self.group._sources))

        for name, item in self.group_views:
            self.pack_end(item)

        self.combo1.set_active(0)

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

    def group_transitions_prepare(self, list_sources):
        group_names = []
        group_values = []
        required = ["Event", "Duration", "ID"]

        tables, group_transitions  = self.preparation(list_sources, "transitions")

        for table in tables:
            header =table.header
            if not all(item in header for item in required):
                tables.remove(table)

        f_eq = lambda x, y: x == y
        columns = ["Duration"]
        filters = [("Event", f_eq, 'T')]

        x = 0
        y = 0
        z = 0
        while x < len(tables):
            table = tables[x]
            transitions = group_transitions[x]
            while y < len(transitions):
                t = transitions[y]
                group_names.append(t.get_name_or_id())
                tets = table.select(columns, filters + [("ID", f_eq, t.id)])
                if len(tets) == 0:
                    tets = [0]
                group_values.append(tets)
                break
            if x == len(tables)-1:
                x =0
                y +=1
                if y == len(transitions):
                    break
            else:
                x +=1

        average, divergence = data_from_operation("transitions")

        lenght = len(tables)
        return ("Group transitions time",
                charts.group_boxplot_transitions_chart(
                    group_names, group_values, lenght, average, divergence,
                        "Group transitions time", "Transitions", "Time"))

    def group_count_tokens_prepare(self, list_sources):
        group_names = []
        group_values = []
        result = []
        tables, group_processes, group_places = self.preparation(list_sources, "tokens")
        for places in group_places:
            result = result +[place_counter_name(place) for place in places]

        required = ["Event", "Process", "Time"] + result

        for table in tables:
            header =table.header
            if not all(item in header for item in required):
                tables.remove(table)

        f_eq = lambda x, y: x == y
        filters = [("Event", f_eq, 'C')]

        x = 0
        y = 0
        z = 0
        while x < len(tables):
            table = tables[x]
            processes = group_processes[x]
            places = group_places[x]
            while y < len(places):
                place = places[y]
                columns = ["Time", place_counter_name(place)]
                while z < len(processes):
                    p = processes[z]
                    group_names.append("{0}@{1}".format(place.get_name_or_id(), p))
                    counts = table.select(columns, filters + [("Process", f_eq, p)])
                    group_values.append((counts[columns[0]], counts[columns[1]]))
                    break
                break
            if x == len(tables)-1:
                x =0
                z +=1
                if z == len(processes):
                    y +=1
                    z =0
                if y == len(places):
                    break
            else:
                x +=1

        average, divergence = data_from_operation("tokens")

        lenght = len(tables)
        return ("Number of tokens in places",
                    charts.group_boxplot_data_chart(
                        group_names, group_values, lenght, average, divergence,
                            "Number of tokens in places", "Places", "Count"))

    def group_transitions_processes_prepare(self, list_sources):
        group_names = []
        group_values = []
        required = ["Event", "Process", "Duration", "ID"]
        tables, group_processes, group_transitions  = self.preparation(list_sources, "processes")

        for table in tables:
            header = table.header
            if not all(item in header for item in required):
                tables.remove(table)

        f_eq = lambda x, y: x == y
        columns = ["Duration"]
        filters = [("Event", f_eq, 'T')]

        x = 0
        y = 0
        z = 0
        while x < len(tables):
            table = tables[x]
            transitions = group_transitions[x]
            processes = group_processes[x]
            while y < len(transitions):
                t = transitions[y]
                f = filters + [("ID", f_eq, t.id)]
                while z < len(processes):
                    p = processes[z]
                    group_names.append("{0}`{1}".format(t.get_name_or_id(), p))
                    tets = table.select(columns, f + [("Process", f_eq, p)])
                    if len(tets) == 0:
                        tets = [0]
                    group_values.append(tets)
                    break
                break
            if x == len(tables)-1:
                x =0
                z +=1
                if z == len(processes):
                    y +=1
                    z =0
                if y == len(transitions):
                    break
            else:
                x +=1

        average, divergence = data_from_operation("processes")

        lenght = len(tables)
        return ("Group processes and transitions",
                    charts.group_histogram_chart(
                        group_names, group_values, lenght, average, divergence,
                            "Group processes and transitions", "Duration", "Count"))

    def preparation(self, list_sources, flag):
        tables = []
        tracelogs = []
        nets = []
        group_processes = []
        group_transitions =  []
        group_places = []

        average_data, divergence_data = data_from_operation(flag)

        for source in list_sources:
            tracelogs.append(source.data)

        for tracelog in tracelogs:
            tables.append(tracelog.data)
            nets.append(tracelog.project.nets[0])
            group_processes.append(range(tracelog.process_count))

        for net in nets:
            group_transitions.append([t for t in net.transitions() if t.trace_fire])
            group_places.append([p for p in net.places() if p.trace_tokens])

        if flag == "processes":
            return tables, group_processes, group_transitions
        if flag == "transitions":
            return tables, group_transitions
        if flag == "tokens":
            return tables, group_processes, group_places

def data_from_operation(flag):
    return None, None #tracelogprocessing.data(flag)