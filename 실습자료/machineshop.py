import simpy
import random

def time_per_part(pt_mean, pt_sigma):
    t = random.normalvariate(pt_mean, pt_sigma)
    while t <= 0:
        t = random.normalvariate(pt_mean, pt_sigma)
    return t

def time_to_failure(break_mean):
    return random.expovariate(break_mean)

class Machine:
    def __init__(self, env, name, repairman, pt_mean, pt_sigma, break_mean, repair_time):
        self.env = env
        self.name = name
        self.repairman = repairman
        self.pt_mean = pt_mean
        self.pt_sigma = pt_sigma
        self.break_mean = break_mean
        self.repair_time = repair_time

        self.parts_made = 0
        self.broken = False

        self.process = env.process(self.working())
        self.env.process(self.break_machine())

    def working(self):
        while True:
            done_in = time_per_part(self.pt_mean, self.pt_sigma)
            while done_in:
                start = self.env.now
                try:
                    yield self.env.timeout(done_in)
                    done_in = 0
                except simpy.Interrupt:
                    self.broken = True
                    done_in -= self.env.now - start

                    with self.repairman.request(priority=1) as req:
                        yield req
                        yield self.env.timeout(self.repair_time)
                    self.broken = False

            self.parts_made += 1

    def break_machine(self):
        while True:
            yield self.env.timeout(time_to_failure(self.break_mean))
            if not self.broken:
                self.process.interrupt()

def other_jobs(env, repairman, job_duration):
    while True:
        done_in = job_duration
        while done_in:
            with repairman.request(priority=2) as req:
                yield req
                start = env.now
                try:
                    yield env.timeout(done_in)
                    done_in = 0
                except simpy.Interrupt:
                    done_in -= env.now - start

RANDOM_SEED = 42
PT_MEAN = 10.0
PT_SIGMA = 2.0
MTTF = 300.0
BREAK_MEAN = 1 / MTTF
REPAIR_TIME = 30.0
JOB_DURATION = 30.0
NUM_MACHINES = 10
WEEKS = 4
SIM_TIME = WEEKS * 7 * 24 * 60

random.seed(RANDOM_SEED)

env = simpy.Environment()
repairman = simpy.PreemptiveResource(env, capacity=1)
machines = [Machine(env, 'Machine {0}'.format(i), repairman, PT_MEAN, PT_SIGMA, BREAK_MEAN, REPAIR_TIME) for i in range(NUM_MACHINES)]
env.process(other_jobs(env, repairman, JOB_DURATION))

env.run(until=SIM_TIME)

print('Machine shop results after {0} weeks'.format(WEEKS))
for machine in machines:
    print('{0} made {1} parts.'.format(machine.name, machine.parts_made))