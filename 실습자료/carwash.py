import simpy

class Carwash():
    def __init__(self, env, n, washtime):
        self.env = env
        self.machines = simpy.Resource(self.env, capacity=n)

        self.washtime = washtime

    def wash(self, car):
        yield self.env.timeout(self.washtime)
        print('cleaning machine remove {0}s dirt at'.format(car), self.env.now)

def car(env, carname, carwash):
    print("{0} arrives at the Carwash at".format(carname), env.now)

    with carwash.machines.request() as req:
        yield req

        print("{0} enters the cleaning machine at".format(carname), env.now)
        yield env.process(carwash.wash(carname))

        print("{0} leaves the machine at".format(carname), env.now)

def setup(env, n, IAT, washtime):
    carwash = Carwash(env, n, washtime)

    car_num = 0
    # 최초의 car 도착
    for _ in range(4):
        car_num += 1
        env.process(car(env, "Car{0}".format(car_num), carwash))
    while True:
        car_num += 1
        yield env.timeout(IAT)
        env.process(car(env, "Car{0}".format(car_num), carwash))


env = simpy.Environment()
num_machines = 2
IAT = 2
washtime = 5

env.process(setup(env, num_machines, IAT, washtime))

env.run(until=60)