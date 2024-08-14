import contextvars

# Create a context variable that holds a dictionary
context_var = contextvars.ContextVar("context_var", default={})

# Function to set multiple values


def set_context_values(**kwargs):
    # Get the current context variable value
    current_values = context_var.get().copy()
    # Update the dictionary with new values
    current_values.update(kwargs)
    # Set the updated dictionary back to the context variable
    context_var.set(current_values)


# Function to get a value
def get_context_value(key):
    return context_var.get().get(key)


# Set multiple values
# set_values(a=1, b=2, c=3)

# # Get values
# print(get_value('a'))  # Output: 1
# print(get_value('b'))  # Output: 2
# print(get_value('c'))  # Output: 3
#
# # Update one value and add another
# set_values(b=20, d=4)
#
# # Get updated values
# print(get_value('b'))  # Output: 20
# print(get_value('d'))  # Output: 4
