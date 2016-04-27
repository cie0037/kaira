import extensions
import datatypes
from exportri import place_counter_name


class TracelogProcessing(extensions.Operation):

    name = "Tracelog processing"
    description = "Processing group tracelog into graph"

    parameters = [
        extensions.Parameter("Group",
                             datatypes.t_tracelog,
                             type=extensions.Parameter.TYPE_GROUP)]

    def run(self, app, list_tracelogs):
        for tracelog in list_tracelogs:
            print(tracelog.filename)

extensions.add_operation(TracelogProcessing)