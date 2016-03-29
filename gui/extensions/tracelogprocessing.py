import extensions
import datatypes
from exportri import place_counter_name


class TracelogProcessing(extensions.Operation):

    name = "Tracelog processing"
    description = "Processing group tracelog into graph"

    parameters = [
        extensions.Parameter("Tracelogs",
                             datatypes.t_tracelog,
                             type=extensions.Parameter.TYPE_GROUP)]

    def run(self, app, list_tracelogs):
        values = []
        tables = []
        nets = []
        group_processes = []
        group_transitions = []
        group_places = []

        p_average = []
        p_divergence = []
        t_average = []
        t_divergence = []
        c_average = []
        c_divergence = []

        p_sum = 0
        p_len = 0
        toc = ()
        if len(p_average) > 0:
            del p_average[:]
            del p_divergence[:]
            del t_average[:]
            del t_divergence [:]
            del c_average[:]
            del c_divergence[:]

        for tracelog in list_tracelogs:
            tables.append(tracelog.data)
            nets.append(tracelog.project.nets[0])
            group_processes.append(range(tracelog.process_count))

        for net in nets:
            group_transitions.append([t for t in net.transitions() if t.trace_fire])
            group_places.append([p for p in net.places() if p.trace_tokens])

        #transitions
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
                tets = table.select(columns, filters + [("ID", f_eq, t.id)])
                if len(tets) == 0:
                    tets = [0]
                values.append(tets)
                p_sum += sum(tets)
                p_len += len(tets)
                break
            if x == len(tables)-1:
                x =0
                y +=1
                av = p_sum / p_len
                t_average.append(av)
                p_sum = 0
                p_len = 0
                if y == len(transitions):
                    break
            else:
                x +=1

        x = 0
        z = 0
        while x < len(values):
            y = 0
            while y < len(list_tracelogs):
                value = values[x]
                average = t_average[z]
                for val in value:
                    if val > (average * 3):
                        t_divergence.append(val)
                y +=1
                x +=1
            z +=1

        del values[:]
        #transitions process
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
                    tets = table.select(columns, f + [("Process", f_eq, p)])
                    if len(tets) == 0:
                        tets = [0]
                    values.append(tets)
                    p_len += len(tets)
                    break
                break
            if x == len(tables)-1:
                x =0
                z +=1
                av = p_len / len(tables)
                if av < 1:
                    av = 0
                p_average.append(av)
                p_len = 0
                if z == len(processes):
                    y +=1
                    z =0
                if y == len(transitions):
                    break
            else:
                x +=1

        x = 0
        z = 0
        while x < len(values):
            y = 0
            while y < len(list_tracelogs):
                value = values[x]
                average = p_average[z]
                if len(value) > (average * 3):
                    print(len(value))
                    p_divergence.append(len(value))
                y +=1
                x +=1
            z +=1

        del values[:]
        #tokens place
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
                    counts = table.select(columns, filters + [("Process", f_eq, p)])
                    toc = (counts[columns[0]], counts[columns[1]])
                    values.append(toc)
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

        x = 0
        z = 0
        while x < len(values):
            y = 0
            while y < len(list_tracelogs):
                value = values[x]
                for val in value:
                    for v in val:
                        p_sum += sum(sum(value))
                        p_len += len(sum(value))
                        av = p_sum / p_len
                        if (av * 3) < v:
                            c_divergence.append(v)
                y +=1
                x +=1
                c_average.append(av)
                p_sum = 0
                p_len = 0
            z +=1

        return p_average, p_divergence, t_average, t_divergence, c_average, c_divergence

extensions.add_operation(TracelogProcessing)