import numpy as np
import simpy

class Customer:
    def __init__(self, name, arrive_time, patience):
        self.name = name
        self.arrive_time = arrive_time
        self.leave_time = None
        self.patience = patience
        self.req = None

class Source:
    def __init__(self, env, model, total_customers, interval, patience, counter):
        self.env = env
        self.model = model
        self.total_customers = total_customers
        self.interval = interval
        self.patience = patience
        self.counter = counter
        self.env.process(self.processing())
        self.complete = 0
        self.renege = 0

    def processing(self):
        for i in range(int(self.total_customers)):
            customer = Customer(i, self.env.now, np.random.exponential(self.patience))
            yield self.env.process(self.to_Counter(customer))
            yield self.env.timeout(np.random.exponential(self.interval))

    def to_Counter(self, customer):
        req = self.counter.request()
        results = yield req | self.env.timeout(customer.patience)
        if req in results:
            customer.req = req
            yield self.model['counter'].store.put(customer)
            self.complete += 1
        else:
            req.cancel()
            self.counter.release(req)
            yield self.model['sink'].store.put(customer)
            self.renege += 1

class Counter:
    def __init__(self, env, model, processing_time, counter):
        self.env = env
        self.model = model
        self.processing_time = processing_time
        self.counter = counter
        self.store = simpy.Store(env)
        self.env.process(self.processing())

    def processing(self):
        while True:
            customer = yield self.store.get()
            self.env.process(self.servicing(customer))

    def servicing(self, customer):
        yield self.env.timeout(np.random.exponential(self.processing_time))
        self.env.process(self.to_Sink(customer))

    def to_Sink(self, customer):
        self.counter.release(customer.req)
        yield self.model['sink'].store.put(customer)

class Sink:
    def __init__(self, env, model):
        self.env = env
        self.model = model
        self.store = simpy.Store(env)
        self.env.process(self.processing())

    def processing(self):
        while True:
            customer = yield self.store.get()
            customer.leave_time = self.env.now

def run_simulation(RANDOM_SEED, TOTAL_CUSTOMERS, INTERVAL_CUSTOMERS, TIME_IN_BANK, PATIENCE, NUM_COUNTERS):
    np.random.seed(RANDOM_SEED)
    env = simpy.Environment()
    counter = simpy.Resource(env, capacity=NUM_COUNTERS)
    model = dict()
    model['source'] = Source(env, model, TOTAL_CUSTOMERS, INTERVAL_CUSTOMERS, PATIENCE, counter)
    model['counter'] = Counter(env, model, processing_time=TIME_IN_BANK, counter=counter)
    model['sink'] = Sink(env, model)
    env.run()
    return model, env.now

if __name__ == '__main__':
    RANDOM_SEED = 43
    TOTAL_CUSTOMERS = 100000  # Total number of customers
    INTERVAL_CUSTOMERS = 5  # Generate new customers roughly every x seconds
    TIME_IN_BANK = 15  # Average of processing time in counter
    PATIENCE = 3  # Average of customer patience
    NUM_COUNTERS = 10  # Total number of Counters
    PROFIT_PER_CUSTOMER = 25
    LOSS_PER_COUNTER = 0.5

    while RANDOM_SEED < 100:
        cost_list = []
        for i in range(1, NUM_COUNTERS):
            model, end_time = run_simulation(RANDOM_SEED, TOTAL_CUSTOMERS, INTERVAL_CUSTOMERS, TIME_IN_BANK, PATIENCE, i)
            cost_list.append(model['source'].complete * PROFIT_PER_CUSTOMER - end_time * i * LOSS_PER_COUNTER)
        print(np.round(cost_list))
        RANDOM_SEED = RANDOM_SEED + 10
