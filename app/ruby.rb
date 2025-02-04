# File: dummy_ruby_file.rb

# Module as Namespace
module MyNamespace
  # Class Definition
  class MyClass
    # Constructor
    def initialize(name)
      @name = name
    end

    # Method Definition
    def greet(name)
      "Hello, #{name}!"
    end

    # Nested Class
    class NestedClass
      def say_hi
        puts "Hi from NestedClass!"
      end
    end
  end

  # Enum-like structure using constants
  Days = [:MONDAY, :TUESDAY, :WEDNESDAY, :THURSDAY, :FRIDAY, :SATURDAY, :SUNDAY]
end

# Decorator-like behavior using metaprogramming
class MyClass
  def self.decorated_method
    puts "This method is decorated."
  end
end

# Expression Statement
if __FILE__ == $0
  instance = MyNamespace::MyClass.new("Test")
  puts instance.greet("Ruby")
  puts MyNamespace::Days[0]
end
