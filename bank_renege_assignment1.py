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

    ## 이 강의의 핵심
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
    return model

if __name__ == '__main__':
    RANDOM_SEED = 43
    TOTAL_CUSTOMERS = 100000  # Total number of customers
    INTERVAL_CUSTOMERS = 5  # Generate new customers roughly every x seconds
    TIME_IN_BANK = 15  # Average of processing time in counter
    PATIENCE = 3  # Average of customer patience
    NUM_COUNTERS = 1  # Total number of Counters

    count = 0
    renege_rate_list = []
    while count < 10:
        while True:
            model = run_simulation(RANDOM_SEED, TOTAL_CUSTOMERS, INTERVAL_CUSTOMERS, TIME_IN_BANK, PATIENCE, NUM_COUNTERS)
            if (model['source'].renege / (model['source'].complete + model['source'].renege)) < 0.02:
                renege_rate_list.append(model['source'].renege / (model['source'].complete + model['source'].renege))
                break
            else:
                renege_rate_list = []
                count = 0
                NUM_COUNTERS += 1
        count += 1
        RANDOM_SEED += 10
    print(renege_rate_list)
    print(f'The minimum number of counters required to achieve a renege rate of 2% or less is {NUM_COUNTERS},'
          f' and the average renege rate is {np.round(np.average(renege_rate_list), 4)}.')

