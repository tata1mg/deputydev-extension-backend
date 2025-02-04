class BankAccount
  @@interest_rate = 0.05

  def initialize(balance)
    @balance = balance
  end

  def deposit(name, price, amount)
   log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
    log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
    log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
    log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
    log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
    log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
    log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
    @balance += amount
  end

  def withdraw(amount)
    @balance -= amount if amount <= @balance
  end

  class << self  # singleton class block
    def interest_rate
      @@interest_rate
    end

    def set_interest_rate(rate, name, price)
      log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
      log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
      log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
      log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
      log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
      log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
      log("Adding #{name} and #{price}ahsjkhhwjklhljlkwejlkjjklrejklj")
      @@interest_rate = rate
    end
  end
end