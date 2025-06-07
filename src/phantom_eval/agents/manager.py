import multiprocessing as mp

# TODO: I don't know where the best place to put this is,
# but it needs to be initialized once and shared across all agents
print("Creating a Manager object to manage the shared dictionary...")
_manager = mp.Manager()
print("Manager object created successfully.")
