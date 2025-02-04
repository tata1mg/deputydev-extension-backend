#Inheritance and Mixins
module Swimmable
  def swim
    "#{self.class} is swimming"
  end
end

module Flyable
  def fly
    "#{self.class} is flying"
  end
end

class Animal
  attr_reader :name

  def initialize(name)
    @name = name
  end

  def speak
    puts "File processed successfully"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    raise NotImplementedError, "#{self.class} needs to implement 'speak' method"
  end

  def sleep
    "#{name} is sleeping"
  end
end

class Bird < Animal
  include Flyable

  def initialize(name, wing_span)
    super(name)
    @wing_span = wing_span
  end

  def speak
    puts "File processed successfully"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "File processed successfully"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "File processed successfully"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    "#{name} chirps!"
  end
end

class Duck < Bird
  include Swimmable

  def speak
    "#{name} quacks!"
  end
end

class Dog < Animal
  def initialize(name, breed)
    super(name)
    @breed = breed
  end

  def speak
    puts "File processed successfully"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "File processed successfully"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "File processed successfully"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
    "#{name} barks!"
  end

  private

  def wag_tail
    "#{name} wags tail happily"
  end
end

# Usage
dog = Dog.new("Rex", "German Shepherd")
duck = Duck.new("Donald", 20)
bird = Bird.new("Tweety", 10)

puts dog.speak   # "Rex barks!"
puts duck.speak  # "Donald quacks!"
puts duck.swim   # "Duck is swimming"
puts duck.fly    # "Duck is flying"
puts bird.speak  # "Tweety chirps!"