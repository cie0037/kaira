#
#    Copyright (C) 2011-2013 Stanislav Bohm
#
#    This file is part of Kaira.
#
#    Kaira is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, version 3 of the License, or
#    (at your option) any later version.
#
#    Kaira is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Kaira.  If not, see <http://www.gnu.org/licenses/>.
#


from writer import CppWriter, const_string

class Builder(CppWriter):

    def __init__(self, project, filename=None):
        CppWriter.__init__(self)
        self.filename = filename
        self.project = project

        # Real class used for thread representation,
        # CaThreadBase is cast to this type
        self.thread_class = "ca::Thread"

        # Generate operator== and operator!= for generated types
        # If true then all ExternTypes have to implement operator== and operator!=
        self.generate_operator_eq = False

        # Generate hash functions for generated types
        # If true then all ExternTypes have to implement get_hash
        self.generate_hash = False


def get_safe_id(string):
    return "__kaira__" + string

def get_hash_combination(codes):
    if not codes:
        return "113"
    numbers = [1, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71,
              73, 79, 83, 89, 97, 101, 103, 107, 109, 113]
    result = []
    for i, code in enumerate(codes):
        result.append("({0} * {1})".format(numbers[i % len(numbers)], code))

    return "^".join(result)

def write_header(builder):
    builder.line("/* This file is automatically generated")
    builder.line("   do not edit this file directly! */")
    builder.emptyline()
    builder.line('#include <cailie.h>')
    builder.line('#include <algorithm>')
    builder.line('#include <stdlib.h>')
    builder.line('#include <stdio.h>')
    builder.line('#include <sstream>')
    builder.emptyline()
    write_parameters_forward(builder)
    builder.emptyline()
    if builder.project.get_head_code():
        builder.line_directive("*head", 1)
        builder.raw_text(builder.project.get_head_code())
        builder.line_directive(None, builder.get_next_line_number() + 1)
        builder.emptyline()

def write_parameters_forward(builder):
    builder.line("struct param")
    builder.block_begin()
    for p in builder.project.get_parameters():
        builder.line("static ca::ParameterInt {0};", p.get_name())
    builder.write_class_end()

def write_parameters(builder):
    for p in builder.project.get_parameters():
        policy = "ca::PARAMETER_" + p.get_policy().upper()
        if p.get_policy() == "mandatory":
            default = ""
        else:
            default = ", " + p.default
        builder.line("ca::ParameterInt param::{0}({1}, {2}, {3}{4});",
                     p.name,
                     const_string(p.name),
                     const_string(p.description),
                     policy,
                     default)

def write_trace_user_function(builder, ufunction, type):
    declaration = "void trace_{0}(ca::TraceLog *tracelog, const {1} &value)".format(
                                                    ufunction.get_name(), type)
    returntype = builder.emit_type(ufunction.get_returntype())
    code = "\t" + returntype + " result = ufunction_" + ufunction.get_name()
    n = len(ufunction.get_parameters())
    if n == 1:
        code += "(value);\n"
    else:
        code += "(" + ", ".join(["value.t{0}".format(i) for i in xrange(n)]) + ");\n"
    code += "\ttracelog->trace_{0}(result);\n".format(ufunction.get_returntype().name.lower())
    builder.write_function(declaration, code)

def write_trace_value(builder, type):
    """
    declaration = "void trace_value(ca::TraceLog *tracelog, const {0} &value)".format(
                                                                        builder.emit_type(type))
    code = "\tstd::string result = {0}(value);\n".format(
            get_to_string_function_name(builder.project, type)) +\
            "\ttracelog->trace_string(result);\n"
    builder.write_function(declaration, code)
    """

def write_trace_user_functions(builder):
    traces = []
    value_traces = []
    for net in builder.project.nets:
        for place in net.places:
            for fn_name in place.tracing:
                if fn_name == "value":
                    if not place.type in value_traces:
                        value_traces.append(place.type)
                    continue
                if not (fn_name, place.type) in traces:
                    traces.append((fn_name, place.type))

    for type in value_traces:
        write_trace_value(builder, type)
    for fn_name, type in traces:
        fn = builder.project.get_user_function(fn_name.replace("fn: ", ""))
        write_trace_user_function(builder, fn, builder.emit_type(type))

def write_basic_definitions(builder):
    write_parameters(builder)
    write_trace_user_functions(builder)
