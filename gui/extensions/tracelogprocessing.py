import extensions
import datatypes


class TracelogProcessing(extensions.Operation):
    
    name = "Tracelog processing"
    description = "Processing group tracelog into graph"
    
    parameters = [ extensions.Parameter("Group", datatypes.t_tracelog)]
    
    def run(self, app, group):
        print(type(group))
        print("konec")
        
extensions.add_operation(TracelogProcessing)