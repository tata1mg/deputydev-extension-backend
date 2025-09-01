class SingletonMeta(type):
    """A metaclass for creating singleton classes.

    This metaclass ensures that a class has only one instance.
    If an instance of the class does not exist, it creates one.
    If it does exist, it returns the existing instance.

    Attributes:
        _instances (dict): A dictionary to hold the instance of the class.

    Example:
        Create a singleton class using the `_SingletonMeta` metaclass:

        ```python
        class SingletonClass(metaclass=_SingletonMeta):
            def __init__(self, value):
                self.value = value


        instance1 = SingletonClass(10)
        instance2 = SingletonClass(20)

        # Both instances will be the same
        assert instance1 is instance2
        assert instance1.value == 10
        assert instance2.value == 10
        ```

    """

    _instances = {}

    def __call__(cls, *args, **kwargs):  # noqa
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]
