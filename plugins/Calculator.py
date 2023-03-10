class Calculator:
    description = "A plugin for adding or subtracting two numbers."

    def __init__(self, first, second):
        self.first = first
        self.second = second

    def add(self):
        """Adds two numbers"""
        print(self.first + self.second)
        
    def subtract(self):
        """Subtracts two number"""
        print(self.first - self.second)
