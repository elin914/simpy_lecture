import simpy

class Car():
    def __init__(self, env, parking_duration, trip_duration):
        self.env = env
        self.parking_duration = parking_duration
        self.trip_duration = trip_duration
        self.action = self.env.process(self.run())

    def run(self):
        while True:
            print("Start driving at", self.env.now)
            yield self.env.timeout(self.trip_duration)

            yield self.env.process(self.park())

    def park(self):
        print("Start parking at", self.env.now)
        yield self.env.timeout(self.parking_duration)

env = simpy.Environment()
parkingduration = 5
tripduration = 2

car = Car(env,parkingduration,tripduration)
env.run(until=15)