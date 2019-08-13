from api import *
from string_parser import StringParser

class TextBlock(ValueTemplate):

    """
    Example block that implements a string parser custom value.
    """

    PARSER = StringParser()
    NAME = "String Parser"

    def setup(self):

        self.min_width = 250
        self.addOutput(Output(self, "out", ConnectionType.VALUE, -1))
        self.addParameter(Parameter("string", ParameterType.TEXT_FIELD))
        self.addInput(Input(self, "variables", ConnectionType.VALUE, -1))

    def evaluate(self):
    
        #Get string from parameter
        input_string = self.parameters[0].value.lower()

        #Get input values
        vars = []
        for input in self.inputs["variables"].targets:
            vars.append(input.block.evaluate())

        #Parse string into OWW format
        return self.PARSER.parse(input_string, vars)