# frozen_string_literal: true

# Module for data validation
module Validatable
  def self.included(base)
    base.extend(ClassMethods)
  end

  module ClassMethods
    def validate_field(field, &block)
      @validations ||= {}
      @validations[field] = block
    end

    def validations
      @validations || {}
    end
  end

  def valid?
    self.class.validations.all? do |field, validator|
      value = send(field)
      validator.call(value)
    end
  end
end

# Custom collection with enumerable functionality
class DataCollection
  include Enumerable

  def initialize(items = [])
    @items = items
  end

  def each(&block)
    return enum_for(:each) unless block_given?

    @items.each(&block)
  end

  def <<(item)
    @items << item
    self
  end
end

# Data model with meta-programming features
class DataRecord
  include Validatable

  class << self
    def attributes(*names)
      names.each do |name|
        define_method(name) do
          instance_variable_get("@#{name}")
        end

        define_method("#{name}=") do |value|
          instance_variable_set("@#{name}", value)
        end
      end
    end
  end

  attributes :name, :value, :created_at

  validate_field(:name) { |n| n.is_a?(String) && !n.empty? }
  validate_field(:value) { |v| v.is_a?(Numeric) && v.positive? }
  validate_field(:created_at) { |t| t.is_a?(Time) }

  def initialize(name:, value:, created_at: Time.now)
    @name = name
    @value = value
    @created_at = created_at
  end

  def to_s
    "#{name}: #{value} (#{created_at.strftime('%Y-%m-%d')})"
  end
end

# Data processor using Ruby's functional features
class DataProcessor
  def initialize(collection)
    @collection = collection
  end

  def process
    @collection
      .select(&:valid?)
      .map { |record| yield record if block_given? }
      .compact
  end
end

# Usage example
if $PROGRAM_NAME == __FILE__
  # Create a collection of records
  records = DataCollection.new

  # Add some test data
  [
    { name: "First", value: 100 },
    { name: "", value: -50 },
    { name: "Third", value: 75 }
  ].each do |data|
    begin
      record = DataRecord.new(
        name: data[:name],
        value: data[:value]
      )
      records << record
    rescue StandardError => e
      puts "Error creating record: #{e.message}"
    end
  end

  # Process the records
  processor = DataProcessor.new(records)
  begin
    results = processor.process do |record|
      "Processed: #{record}"
    end

    puts "\nProcessing results:"
    results.each { |result| puts result }
  rescue StandardError => e
    puts "Processing failed: #{e.message}"
  end
end