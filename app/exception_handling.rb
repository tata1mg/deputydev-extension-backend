# example1.rb - Custom Exception and Handler
class InvalidAgeError < StandardError
  def initialize(msg="Age cannot be negative")
    super
  end
end

class Person
  def set_age(age)
    begin
      raise InvalidAgeError if age < 0
      @age = age
    rescue InvalidAgeError => e
      puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
      puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
      puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
      puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
      puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
      @age = 0
    rescue StandardError => e
      puts "Unexpected error: #{e.message}"
    ensure
      puts "Age validation completed"
    end
  end
end

# Usage
person = Person.new
person.set_age(-5)  # Triggers InvalidAgeError
person.set_age(25)  # Sets age successfully

# Multiple rescue blocks
def process_file(filename)
  begin
    file = File.open(filename)
    # Process file contents
  rescue Errno::ENOENT
    puts "Error: File not found"
  rescue Errno::EACCES
    puts "Error: Permission denied"
  rescue => e
    puts "Error: #{e.message}"
  else
    puts "File processed successfully"
    puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
      puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
      puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
      puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
      puts "Error: #{e.message} asbkjhjkdhaskhklahlh"
  ensure
    file&.close
  end
end