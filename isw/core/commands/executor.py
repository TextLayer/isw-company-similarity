class Executor:
    """
    Singleton class for executing commands in the command pattern.

    The Executor is a key component in the application's command processing architecture.
    It provides a centralized way to execute both read and write commands, acting as an
    intermediary between controllers (which handle API requests) and commands (which
    contain business logic).

    This design follows the command pattern to ensure:
    - Separation of concerns between request handling and business logic
    - Consistent command execution throughout the application
    - Reusability of commands across different controllers
    - Easier testing of isolated business logic

    The Executor follows the Singleton pattern to ensure only one instance exists
    in the application.

    Example:
        executor = Executor.get_instance()
        result = executor.execute_read(GetUserCommand(user_id=123))
    """

    __instance = None

    @staticmethod
    def get_instance():
        if not Executor.__instance:
            Executor()
        return Executor.__instance

    def __init__(self):
        if Executor.__instance:
            raise Exception("This class is a singleton!")
        else:
            Executor.__instance = self

    @staticmethod
    def execute_read(command):
        """
        Execute a read command that retrieves data without modifying state.

        Used for operations that only retrieve data, such as fetching resources
        or performing calculations.

        Args:
            command (ReadCommand): A command instance that inherits from ReadCommand.

        Returns:
            The result of the command execution, which can be of any type
            depending on the specific command implementation.
        """
        return command.run()

    @staticmethod
    def execute_write(command):
        """
        Execute a write command that modifies system state.

        Used for operations that change data, such as creating, updating,
        or deleting resources.

        Args:
            command (WriteCommand): A command instance that inherits from WriteCommand.

        Returns:
            The result of the command execution, which can be of any type
            depending on the specific command implementation.
        """
        return command.run()
