class GreetingPlugin:
    description = "A plugin for greeting people."

    def __init__(self, name):
        self.name = name

    def greet(self):
        """Greet the person."""
        print(f"Hello, {self.name}!")

    def farewell(self):
        """Say farewell to the person."""
        print(f"Goodbye, {self.name}!")