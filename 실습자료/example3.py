import simpy

class School():
    def __init__(self, env):
        self.env = env
        self.class_ends = env.event()
        self.pupil_procs = [env.process(self.pupil()) for i in range(5)]
        self.bell_proc = env.process(self.bell())

    def bell(self):
        for i in range(5):
            yield self.env.timeout(50)
            self.class_ends.succeed()
            self.class_ends = env.event()
            print()

    def pupil(self):
        while True:
            print('\o/', end='')
            yield self.class_ends

env = simpy.Environment()

school = School(env)
env.run()