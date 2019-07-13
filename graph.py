import logging
import pathlib
import json
from enum import Enum

WORKSHOP_JSON_PATH = pathlib.Path("./res/workshop.json")

def loadWorkshopJSON():

    with open(WORKSHOP_JSON_PATH, "r") as f:
        d = json.load(f)
    return d

class BlockType(Enum):

    """
    Enum listing all the different block types in a graph.
    """

    ACTION = "action"
    VALUE = "value"
    RULE = "rule"
    CONDITION = "condition"
    NONE = -1

class ConnectionType(Enum):

    """
    Enum listing all the different connection types between blocks.
    """

    ACTION = "action"
    VALUE = "value"
    CONDITION = "condition"

class EventType(Enum):

    """
    Enum listing all the different event types for rules.
    """

    GLOBAL = "Ongoing - Global"
    PLAYER = "Ongoing - Each Player"
    ELIMINATION = "Player earned elimination"
    FINAL_BLOW = "Player dealt final blow"
    DAMAGE_DEALT = "Player dealt damage"
    DAMAGE_TAKEN = "Player took damage"
    DEATH = "Player Died"

EVENTS = [
    "Ongoing - Global",
    "Ongoing - Each Player",
    "Player Earned Elimination",
    "Player Dealt Final Blow",
    "Player Dealt Damage",
    "Player Took Damage",
    "Player Died"
    ]

class ParameterType(Enum):

    """
    Enum listing all available parameter types.
    """

    TEXT_FIELD = 0
    NUMBER_FIELD = 1
    DROP_DOWN = 2

class Input():

    def __init__(self, block, name, type, maxConnections=-1):

        assert isinstance(type, ConnectionType)

        self.block = block
        self.name = name
        self.type = type
        self.maxConnections = maxConnections
        self.targets = []

class Output():

    def __init__(self, block, name, type, maxConnections=-1):
        
        assert isinstance(type, ConnectionType)

        self.block = block
        self.name = name
        self.type = type
        self.maxConnections = maxConnections
        self.targets = []

class Parameter():

    def __init__(self, name, type, values=[], default=None):

        self.name = name
        self.type = type
        self.values = values
        self.default = default
        self.value = default

PARAM_TYPE_MAP = {
    "number constant": (ParameterType.NUMBER_FIELD, []),
    "team constant": (ParameterType.DROP_DOWN, ["All", "Team 1", "Team 2"]),
    "string constant": (ParameterType.TEXT_FIELD, []),
    "hero constant": (ParameterType.TEXT_FIELD, []),
    "play effect": (ParameterType.TEXT_FIELD, []),
    "create effect": (ParameterType.TEXT_FIELD, []),
    "communicate": (ParameterType.TEXT_FIELD, []),
    "icon": (ParameterType.TEXT_FIELD, []),
    "relative": (ParameterType.DROP_DOWN, ["To Player", "To World"]),
    "motion": (ParameterType.DROP_DOWN, ["Cancel Contrary Motion", "Incorporate Contrary Motion"]),
    "rounding type": (ParameterType.DROP_DOWN, ["Down", "To Nearest", "Up"]),
    "los check": (ParameterType.DROP_DOWN, ["Off", "Surfaces", "Surfaces and Barriers", "Surfaces and Enemy Barriers"]),
    "world text clipping": (ParameterType.DROP_DOWN, ["Clip Against Surfaces", "Do Not Clip"]),
    "hud location": (ParameterType.DROP_DOWN, ["Left", "Right", "Top"]),
    "icon reevaluation": (ParameterType.DROP_DOWN, ["None", "Position", "Visible To", "Visible To and Position"]),
    "effect reevaluation": (ParameterType.DROP_DOWN, ["None", "Position and Radius", "Visible To", "Visible to, Position, and Radius"]),
    "hud text reevaluation": (ParameterType.DROP_DOWN, ["String", "Visible To and String"]),
    "world text reevaluation": (ParameterType.DROP_DOWN, ["String", "Visible To and String", "Visible To, Position, and String"]),
    "chase rate reevaluation": (ParameterType.DROP_DOWN, ["Destination and Rate", "None"]),
    "chase time reevaluation": (ParameterType.DROP_DOWN, ["Destination and Duration", "None"]),
    "objective description reevaluation": (ParameterType.DROP_DOWN, ["String", "Visible To and String"]),
    "damage modification reevaluation": (ParameterType.DROP_DOWN, ["None", "Receivers and Damagers", "Receivers, Damagers, and Damage Percent"]),
    "wait behavior": (ParameterType.DROP_DOWN, ["Abort When False", "Ignore Condition", "Restart When True"]),
    "barriers los": (ParameterType.DROP_DOWN, ["All Barriers Block LOS", "Barriers Do Not Block LOS", "Enemy Barriers Block LOS"]),
    "status": (ParameterType.DROP_DOWN, ["Asleep", "Burning", "Frozen", "Hacked", "Invincible", "Knocked Down", "Phased Out", "Rooted", "Stunned", "Unkillable"]),
    "compare operator": (ParameterType.DROP_DOWN, ["==", "!=", "<", "<=", ">", ">="]),
    "variable": (ParameterType.TEXT_FIELD, []),
    "operation": (ParameterType.DROP_DOWN, ["Add", "Append To Array", "Divide", "Max", "Min", "Modulo", "Multiply", "Raise To Power", "Remove From Array by Index", "Remove From Array by Value", "Subtract"]),
    "button": (ParameterType.DROP_DOWN, ["Ability 1", "Ability 2", "Crouch", "Interact", "Jump", "Primary Fire", "Secondary Fire", "Ultimate"]),
    "color": (ParameterType.DROP_DOWN, ["Blue", "Green", "Purple", "Red", "Team 1", "Team 2", "White", "Yellow"]),
    "invisible to": (ParameterType.DROP_DOWN, ["All", "Enemies", "None"]),
    "transformation": (ParameterType.DROP_DOWN, ["Rotation", "Rotation and Translation"]),
    }

def parseArgs(d):

    order = []
    inputs = []
    params = []

    for arg in d["args"]:
        if arg["type"].lower() in PARAM_TYPE_MAP:
            params.append(Parameter(arg["name"].lower(), *PARAM_TYPE_MAP[arg["type"].lower()], default=arg.get("default")))
            order.append((arg["name"].lower(), "parameter"))
        else:
            inputs.append(Input(None, arg["name"].lower(), ConnectionType.VALUE))
            order.append((arg["name"].lower(), "input"))

    return (inputs, params, order)

class Block():

    """
    Each Block instance represents a node in the
    program graph.
    A block consists of one or multiple inputs, one or multiple
    outputs and a set of properties.

    For example, the value block Append To Array takes
    n inputs (the array and all elements that will be added).
    
    Each input aggregates all incoming connections before passing
    them onto the block. This means that input values will always
    appear as a list rather than a value of the specified type.

    There are three different types of blocks: Action, Value and Rule.

    Each block may provide a set of parameters
    """

    TYPE = BlockType.NONE

    logger = logging.getLogger("Block.Generic")

    def __init__(self):

        self.name = "Untitled Block"
        self.inputs = {}
        self.outputs = {}
        self.parameters = []
        self.argumentOrder = []

    def addInput(self, input):

        input.block = self
        self.inputs[input.name] = input

    def addOutput(self, output):

        output.block = self
        self.outputs[output.name] = output

    def connectInput(self, input, output, other):

        """
        Connect another blocks output to this blocks input.
        input must be an input of this block.
        output must be an output of the other block.
        """

        if not input.name in self.inputs:
            raise ValueError("Input is not part of this block")

        if not output.name in other.outputs:
            raise ValueError("Output is not part of target block")

        if input.maxConnections > -1 and (not len(input.targets) < input.maxConnections):
            raise ValueError("Too many connections to input '%s'" % input.name)

        if output.maxConnections > -1 and (not len(output.targets) < output.maxConnections):
            raise ValueError("Too many connections from output '%s'" % output.name)

        input.targets.append(output)
        output.targets.append(input)

    def evaluate(self):

        """
        Evaluate this block.
        This method should return a list containing one or multiple actions/values (depending on the block).
        """

        return []

class ActionBlock(Block):

    """
    An Action block defines an action. Each action block MUST take at least
    one input, this being the previous action in the chain, but does not
    have to produce an output. If more than one output is present, all outputs
    will be evaluated in order.
    If no output is generated, this terminates the
    currently executing branch and evaluation continues at the next branch.
    If all branches have been exhausted, the current rule is finalized.
    """

    TYPE = BlockType.ACTION

    logger = logging.getLogger("Block.Action")

    def __init__(self, name, inputs, outputs, parameters=[], order=[]):

        if not isinstance(inputs, (list, tuple)):
            raise TypeError("inputs must be a sequence")

        if not isinstance(outputs, (list, tuple)):
            raise TypeError("outputs must be a sequence")

        super().__init__()
        self.name = name
        self._order = order
        for input in inputs:
            self.addInput(input)
        for output in outputs:
            self.addOutput(output)
        self.parameters = parameters

        self.addInput(Input(self, "previous", ConnectionType.ACTION))

    @classmethod
    def fromJSON(self, d):

        name = d["name"]
        inputs, params, order = parseArgs(d)
        return ActionBlock(name, inputs, [Output(None, "next", ConnectionType.ACTION, 1)], params, order)

    def evaluate(self):

        #Since this contains the "previous" link, we need to filter for values
        inputs = [i for i in self.inputs.values() if i.type == ConnectionType.VALUE]
        arg_list = []
        p_ind = 0
        for name, type in self._order:
            if type == "input":
                arg_list.append(self.inputs[name].targets[0].block.evaluate())
            else:
                arg_list.append(str(self.parameters[p_ind].value))
                p_ind += 1
        args = ", ".join(arg_list)

        code = ["%s(%s);" % (self.name, args)]
        for out in self.outputs.values():
            actions = map(lambda x: x.block.evaluate(), out.targets)
            for action in actions:
                code.extend(action)

        return code

class ValueBlock(Block):

    """
    A Value block defines a value. Each value block MUST produce EXACTLY one
    output, but may take zero, one or multiple inputs.
    """

    TYPE = BlockType.VALUE

    logger = logging.getLogger("Block.Value")

    def __init__(self, name, inputs, output, parameters=[], order=[]):

        if not isinstance(inputs, (list, tuple)):
            raise TypeError("inputs must be a sequence")

        if not isinstance(output, Output):
            raise TypeError("output must be of type Output")

        super().__init__()
        self.name = name
        self._order = order
        for input in inputs:
            self.addInput(input)
        self.addOutput(output)
        self.parameters = parameters

    @classmethod
    def fromJSON(self, d):

        name = d["name"]
        inputs, params, order = parseArgs(d)
        return ValueBlock(name, inputs, Output(None, "out", ConnectionType.VALUE), params, order)

    def evaluate(self):

        #TODO: add support for array inputs
        arg_list = []
        p_ind = 0
        for name, type in self._order:
            if type == "input":
                arg_list.append(self.inputs[name].targets[0].block.evaluate())
            else:
                arg_list.append(str(self.parameters[p_ind].value))
                p_ind += 1
        args = ", ".join(arg_list)

        return "%s(%s)" % (self.name, args)

class RuleBlock(Block):

    """
    A Rule block defines the start of a new rule. Only rule blocks
    may be added to a graph. When the graph is compiled, each rule block
    creates a new rule, with the first action being the action block that
    follows the rule block.
    """

    TYPE = BlockType.RULE

    logger = logging.getLogger("Block.Rule")

    def __init__(self, name, event):
        
        """
        Create a new RuleBlock instance.
        name is the name of the rule and will determine how it is displayed in
        the Overwatch Workshop.
        event is the event type of the rule and must be an instance of EventType.
        """

        super().__init__()
        self.name = name
        self.event = event
        self.parameters = [
            Parameter("event", ParameterType.DROP_DOWN, EVENTS, EVENTS[0]),
            Parameter("team", ParameterType.DROP_DOWN, ["All", "Team 1", "Team 2"], "All"),
            Parameter("player", ParameterType.TEXT_FIELD, default="All")
            ]
        self.addOutput(Output(self, "action", ConnectionType.ACTION, 1)) #this points to the next action in the chain
        self.addInput(Input(self, "conditions", ConnectionType.CONDITION))

    def evaluate(self):

        conditions = []
        for cond in self.inputs["conditions"].targets:
            conditions.extend(cond.block.evaluate())
           
        outs = self.outputs["action"].targets
        if len(outs) > 0:
            actions = outs[0].block.evaluate() #this should never be longer than one element because we are not allowing multiple connections here
        else:
            actions = []

        code = [
            """rule("%s")""" % self.name,
            "{",
            "\tevent",
            "\t{",
            "\t\t%s;" % self.parameters[0].value
            ]
        if self.parameters[0].value != "Ongoing - Global":
            code.append("%s;" % self.parameters[1].value)
            code.append("%s;" % self.parameters[2].value)

        code.extend([
            "\t}",
            "",
            "\tconditions",
            "\t{"
            ])

        code.extend(map(lambda x: "\t\t%s" % x, conditions))
        code.extend([
            "\t}",
            "",
            "\tactions",
            "\t{"
            ])

        code.extend(map(lambda x: "\t\t%s" % x, actions))
        code.extend([
            "\t}",
            "}"
            ])

        return code

class ConditionBlock(Block):

    """
    Condition blocks are special values that may be used to determine triggers for rules.
    Condition blocks can take arbitrary values as inputs, but can only output to the condition
    input of a rule block. Otherwise, they function exactly like a ValueBlock.
    """

    TYPE = BlockType.CONDITION

    logger = logging.getLogger("Block.Condition")

    def __init__(self):

        super().__init__()
        self.title = "New Condition"
        self.parameters = [
            Parameter("operation", ParameterType.DROP_DOWN, ["==", ">=", "<=", ">", "<", "!="], "==")
            ]
        self.addInput(Input(self, "value_a", ConnectionType.VALUE))
        self.addInput(Input(self, "value_b", ConnectionType.VALUE, 1))
        self.addOutput(Output(self, "condition", ConnectionType.CONDITION))

    def evaluate(self):
        
        code = []

        value_b = self.inputs["value_b"].targets[0].block.evaluate()
        for val in self.inputs["value_a"].targets:
            code.append("%s %s %s;" % (val.block.evaluate(), self.parameters[0].value, value_b))

        return code

class Graph():

    """
    A ruleset graph.

    A graph consist of one or multiple nodes, referred to as Blocks.
    Each block contains information about some action or value being
    created. Together, these blocks form an evaluation graph which, 
    when executed, produces a program executable by the Overwatch
    Workshop.
    """

    logger = logging.getLogger("Graph")

    def __init__(self):

        self._startBlocks = []

    def addBlock(self, block):

        if not isinstance(block, RuleBlock):
            raise TypeError("block must be of type 'RuleBlock', not '%s'" % str(block.__class__))
        self._startBlocks.append(block)

    def removeBlock(self, block):

        self._startBlocks.remove(block)

    def compile(self):

        """
        Compile the graph into workshop code.
        """

        code = []
        
        self.logger.debug("compiling graph...")
        for block in self._startBlocks:
            code.extend(block.evaluate())

        return "\n".join(code)

