from isw.core.commands.executor import Executor


class Controller:
    """
    Base controller class that provides access to the command executor.

    The Controller class is a foundational component in the application's request handling
    flow. Controllers are responsible for:
    - Receiving and processing incoming API requests
    - Delegating business logic to appropriate command handlers
    - Returning structured API responses

    This design implements a clean separation of concerns where:
    - Controllers handle HTTP request/response concerns
    - Commands encapsulate business logic
    - The Executor mediates between them

    All application-specific controllers should inherit from this class to gain access
    to the singleton Executor instance for processing business logic through commands.

    Example:
        class UserController(Controller):
            def get_user(self, user_id):
                command = GetUserCommand(user_id)
                return self.executor.execute_read(command)

            def create_user(self, user_data):
                command = CreateUserCommand(user_data)
                return self.executor.execute_write(command)
    """

    executor = Executor.get_instance()
