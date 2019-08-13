from graph import ValueBlock, ActionBlock, Output, ConnectionType, Parameter, ParameterType, Input, Block

class ValueTemplate(ValueBlock):

    def __init__(self):

        Block.__init__(self)
        self.name = self.NAME.upper()
        self.setup()

    def setup(self):

        """
        Custom Block constructor.

        PLEASE MAKE SURE TO NOT OVERRIDE THE ACTUAL CONSTRUCTOR.
        USE THIS METHOD INSTEAD.
        """

        pass

class ActionTemplate(ActionBlock):

    def __init__(self):

        Block.__init__(self)
        self.name = self.NAME.upper()
        self.setup()

    def setup(self):

        """
        Custom Block constructor.

        PLEASE MAKE SURE TO NOT OVERRIDE THE ACTUAL CONSTRUCTOR.
        USE THIS METHOD INSTEAD.
        """

        pass