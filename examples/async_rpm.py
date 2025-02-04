import asyncio, time

class Counter:
    def __init__(self, rpm=2_000):
        self.start = self.value = time.time()
        self.rpm = rpm # the amount of time you want to wait in between API calls
    def increment(self):
        self.value += 60 / self.rpm
    def remaining(self):
        return self.value - time.time()
    def check(self):
        print(f"curr time={time.time()-self.start}, counter={self.value-self.start}")
        return time.time() >= self.value
    def __str__(self):
        return str(time.time() - self.start)

cond = asyncio.Condition()
counter = Counter()

SLEEP = 0.01
async def _call_api(i, counter):
    print(f"{counter}: Calling API for {i}")
    await asyncio.sleep(SLEEP)
    print(f"{counter}: Done with API for {i}")
    return i

async def generate_response(i, counter):
    # acquire the lock for the counter
    await cond.acquire()
    print(f"{counter}: Acquired lock for {i}")
    # sleep in necessary
    remaining = counter.remaining()
    if remaining > 0:
        print(f"Sleeping for {remaining}")
        await asyncio.sleep(remaining)
    try:
        # yield to other threads until condition is true
        await cond.wait_for(counter.check)
        # update counter
        counter.increment()
        print(f"{counter}: Updated counter")
        # schedule _call_api to run concurrently
        t = asyncio.create_task(_call_api(i, counter))
        print(f"{counter}: Done with {i}")
        # release underlying lock and wake up 1 waiting task
        cond.notify_all()
        print(f"{counter}: Notified all")
    finally:
        cond.release()
        print(f"{counter}: Released lock for {i}")
    # wait for the task to complete
    return await t

async def main(counter):
    tasks = [generate_response(i, counter) for i in range(1_000)]
    responses = await asyncio.gather(*tasks)
    return responses

responses = asyncio.run(main(counter))
print('responses:', responses)