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
    def __init__(self, env, model, total_customers, interval, min_patience, max_patience, counter):
        self.env = env
        self.model = model
        self.total_customers = total_customers
        self.interval = interval
        self.min_patience = min_patience
        self.max_patience = max_patience
        self.counter = counter
        self.env.process(self.processing())

    def processing(self):
        for i in range(int(self.total_customers)):
            customer = Customer(i, self.env.now, np.random.uniform(self.min_patience, self.max_patience))
            print('customer', customer.name, 'arrive at', customer.arrive_time)
            yield self.env.process(self.to_Counter(customer))
            yield self.env.timeout(np.random.exponential(self.interval))

    # 이 강의의 핵심
    def to_Counter(self, customer):
        req = self.counter.request()
        results = yield req | self.env.timeout(customer.patience)
        if req in results:
            customer.req = req
            print('customer', customer.name, 'start process at', self.env.now)
            yield self.model['counter'].store.put(customer)
        else:
            req.cancel()
            print('customer', customer.name, 'get angry at', self.env.now)
            self.counter.release(req)
            yield self.model['sink'].store.put(customer)

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
        print('customer', customer.name, 'finished process at', self.env.now)
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
            print('customer', customer.name, 'leaved at', customer.leave_time)



if __name__ == '__main__':
    RANDOM_SEED = 43
    TOTAL_CUSTOMERS = 5  # Total number of customers
    INTERVAL_CUSTOMERS = 10  # Generate new customers roughly every x seconds
    TIME_IN_BANK = 12  # Average of processing time in counter
    MIN_PATIENCE = 1  # Min. customer patience
    MAX_PATIENCE = 3  # Max. customer patience
    NUM_COUNTERS = 1  # Total number of Counters

    np.random.seed(RANDOM_SEED)

    env = simpy.Environment()
    counter = simpy.Resource(env, capacity=NUM_COUNTERS)
    model = dict()
    model['source'] = Source(env, model, TOTAL_CUSTOMERS, INTERVAL_CUSTOMERS, MIN_PATIENCE, MAX_PATIENCE, counter)
    model['counter'] = Counter(env, model, processing_time=TIME_IN_BANK, counter=counter)
    model['sink'] = Sink(env, model)
    env.run()
