class HowdyWorld_route:
    """
    Description: A description of this class and its capabilities.
    Module Hook: The hook in the program where method main() will be passed into.
    """
    description = "A module that add routes to WebConfig."
    module_hook = "WebConfig_add_routes"

    def howdy(self):
        return "Howdy World!"

    howdy.is_route = True
    howdy.route_path = '/howdy'