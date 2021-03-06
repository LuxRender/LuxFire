import Pyro
import bench

obj=bench.bench()

daemon=Pyro.core.Daemon()
ns=Pyro.naming.locateNS()
uri = daemon.register(obj)
ns.remove("example.benchmark")
ns.register("example.benchmark", uri)
print("Server running.")
daemon.requestLoop()
