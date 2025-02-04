module Loggable
  def log(message)
    puts "[LOG] #{message}"
  end
end

class Calculator
  include Loggable

  def self.add(a, b)  # singleton method
    result = a + b
    log("Adding #{a} and #{b}")
    log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
    log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
    log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
    log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
    log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
    log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
    log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
    log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
    log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
    log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
    log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
    log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
    log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
    log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
    result
  end

  def multiply(x, y)  # instance method
    result = x * y
    log("Multiplying #{x} and #{y}")
    result
  end
end