import extensions
import datatypes


class TracelogProcessing(extensions.Operation):
    
    name = "Tracelog processing"
    description = "Processing group tracelog into graph"
    
    parameters = [ extensions.Parameter("Group", datatypes.t_tracelog, extensions.Group())]
    
    def run(self, app, group):
        print(type(group))
        
extensions.add_operation(TracelogProcessing)