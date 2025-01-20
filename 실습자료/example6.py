import simpy

class Fuel_station():
    def __init__(self, env, IAT, charging_duration, stations):
        self.env = env
        self.IAT = IAT
        self.charging_duration = charging_duration
        self.stations = stations

        self.action = self.env.process(self.run())

    def run(self):
        car_index = 0
        for _ in range(4):
            car_index += 1
            self.env.process(self.car(car_index))
            yield self.env.timeout(self.IAT)

    def car(self, car_index):
        print("{0} arriving at".format(car_index), self.env.now)

        with self.stations.request() as req:
            yield req

            print("{0} starting to charge at".format(car_index), self.env.now)
            yield self.env.timeout(self.charging_duration)
            print("{0} leaving the station at".format(car_index), self.env.now)

env = simpy.Environment()
IAT = 2
charging_duration = 5
stations = simpy.Resource(env, capacity=2)

fuel_stations = Fuel_station(env,IAT,charging_duration,stations)

env.run()