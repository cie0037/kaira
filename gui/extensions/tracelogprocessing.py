import extensions
import datatypes


class TracelogProcessing(extensions.Operation):

    name = "Tracelog processing"
    description = "Processing group tracelog into graph"

    parameters = [
        extensions.Parameter("Tracelogs",
                             datatypes.t_tracelog,
                             type=extensions.Parameter.TYPE_GROUP)]

    def run(self, app, group):
        print(group)
        print("konec")

extensions.add_operation(TracelogProcessing)
