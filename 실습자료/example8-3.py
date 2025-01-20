import simpy
import pandas as pd

class Part:
    def __init__(self, id, enter_time):
        self.id = id
        self.enter_time = enter_time
        self.exit_time = 0
        self.step = 0
        self.process_list = ['process1', 'process2', 'sink']

class Source:
    def __init__(self, env, model, monitor, name, IAT):
        self.env = env
        self.model = model
        self.monitor = monitor
        self.name = name
        self.IAT = IAT
        self.part_id = 0
        self.env.process(self.processing())

    def processing(self):
        while True:
            self.part_id += 1
            part = Part(self.part_id, enter_time=self.env.now)
            self.monitor.record(time=env.now, part=part.id, process=self.name, event='part created')
            yield self.env.process(self.to_next_process(part))

            IAT = self.IAT
            yield self.env.timeout(IAT)

    def to_next_process(self, part):
        next_process = part.process_list[part.step]
        yield self.model[next_process].store.put(part)


class Process:
    def __init__(self, env, model, monitor, name, setup_time, service_time, capacity):
        self.env = env
        self.model = model
        self.monitor = monitor
        self.name = name
        self.setup_time = setup_time
        self.service_time = service_time
        self.store = simpy.Store(env)
        self.machines = simpy.Store(env, capacity=capacity)
        for i in range(capacity):
            self.machines.put('resource'+str(i))
        self.env.process(self.processing())

    def processing(self):
        while True:
            machine = yield self.machines.get()
            part = yield self.store.get()
            self.env.process(self.servicing(part, machine))

    def servicing(self, part, machine):
        setup_time = self.setup_time
        self.monitor.record(time=self.env.now, part=part.id, process=self.name, event='setup start', resource=machine)
        yield self.env.timeout(setup_time)
        self.monitor.record(time=self.env.now, part=part.id, process=self.name, event='setup finish', resource=machine)

        service_time = self.service_time
        self.monitor.record(time=self.env.now, part=part.id, process=self.name, event='service start', resource=machine)
        yield self.env.timeout(service_time)
        self.monitor.record(time=self.env.now, part=part.id, process=self.name, event='service finish', resource=machine)

        self.env.process(self.to_next_process(part, machine))

    def to_next_process(self, part, machine):
        part.step += 1
        next_process = part.process_list[part.step]
        yield self.model[next_process].store.put(part)
        self.machines.put(machine)

class Sink:
    def __init__(self, env, model, monitor, name):
        self.env = env
        self.model = model
        self.monitor = monitor
        self.name = name
        self.store = simpy.Store(env)
        self.env.process(self.processing())

        self.part_count = 0

    def processing(self):
        while True:
            part = yield self.store.get()
            self.monitor.record(time=self.env.now, part=part.id, process=self.name, event='part finish')
            self.part_count += 1

class Monitor:
    def __init__(self, filepath):
        self.filepath = filepath
        self.time = list()
        self.part = list()
        self.process = list()
        self.event = list()
        self.resource = list()

    def record(self, time, process=None, part=None, event=None, resource=None):
        self.time.append(time)
        self.process.append(process)
        self.part.append(part)
        self.event.append(event)
        self.resource.append(resource)

    def save_event_tracer(self):
        event_tracer = pd.DataFrame(columns=['Time', 'Part', 'Process', 'Event', 'Resource'])
        event_tracer['Time'] = self.time
        event_tracer['Part'] = self.part
        event_tracer['Process'] = self.process
        event_tracer['Event'] = self.event
        event_tracer['Resource'] = self.resource

        event_tracer.to_csv(self.filepath)


if __name__== '__main__':
    IAT = 4
    setup_time = 2
    service_time = 3
    capacity = 1

    env = simpy.Environment()

    monitor = Monitor('eventlog.csv')

    model = dict()
    model['source'] = Source(env, model, monitor, 'source', IAT)
    model['process1'] = Process(env, model, monitor, 'process1', setup_time, service_time, capacity)
    model['process2'] = Process(env, model, monitor, 'process2', setup_time, service_time, capacity)
    model['sink'] = Sink(env, model, monitor, 'sink')

    env.run(until=100)

    monitor.save_event_tracer()
