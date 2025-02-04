# example2.rb - Iterators and Loops
class Collection
  def initialize
    @items = []
  end

  # Custom iterator
  def each_with_index_and_time
    @items.each_with_index do |item, index|
      yield(item, index, Time.now)
    end
  end

  # Different types of loops
  def demonstrate_loops
    # Each iterator
    @items.each { |item| puts item }

    # Map with index
    @items.map.with_index { |item, i| "#{i}: #{item}" }

    # Select/filter
    even_items = @items.select { |item| item.to_i.even? }

    # While loop
    counter = 0
    while counter < @items.length
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
      puts @items[counter]
      counter += 1
    end

    # Until loop
    counter = 0
    until counter >= @items.length
      puts @items[counter]
      counter += 1
    end

    # For loop
    for item in @items
      puts item
    end

    # Times loop
    5.times { |i| puts "Iteration #{i}" }

    # Upto/downto
    1.upto(5) { |n| puts n }
    5.downto(1) { |n| puts n }

    # Step
    (0..10).step(2) { |x| puts x }  # Print even numbers
  end
end

# Usage
collection = Collection.new
collection.demonstrate_loops