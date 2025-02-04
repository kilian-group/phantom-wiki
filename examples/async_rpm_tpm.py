import asyncio, time

RPM_LIMIT = 2_000
TPM_LIMIT = 4_000_000
class Counter:
    def __init__(self):
        self.start = self.end_rpm = self.end_tpm = time.time()
        self.token_usage_per_minute = 0
    def increment(self):
        now = time.time()
        # set the next rpm deadline to be 1 interval from now
        if now > self.end_rpm:
            self.end_rpm = now + 60 / RPM_LIMIT
        if now > self.end_tpm:
            self.end_tpm = now + 60 # set the next tpm deadline to be 1 minute
            self.token_usage_per_minute = 0 # reset token_usage_per_minute if new minute has started
    async def sleep_rpm(self):
        """Sleep if the RPM limit is exceeded"""
        remaining = self.end_rpm - time.time()
        print(f"Sleeping for {remaining} to satisfy RPM limit")
        return await asyncio.sleep(max(remaining, 0))
    async def sleep_tpm(self, input_tokens):
        """Sleep if the input_tokens will exceed the TPM limit"""
        if input_tokens + self.token_usage_per_minute > TPM_LIMIT:
            remaining = self.end_tpm - time.time()
            print(f"Sleeping for {remaining} to satisfy TPM limit")
            await asyncio.sleep(max(remaining, 0))
            self.token_usage_per_minute = 0 # reset token_usage_per_minute if new minute has started
            return
    def check(self, input_tokens):
        now = time.time()
        print(f"curr time={now-self.start}, rpm counter={self.end_rpm-self.start}, tpm counter={self.end_tpm-self.start}, token_usage_per_minute={self.token_usage_per_minute}")
        return now >= self.end_rpm and input_tokens + self.token_usage_per_minute <= TPM_LIMIT
    def __str__(self):
        return str(time.time() - self.start)

cond = asyncio.Condition()
counter = Counter()

SLEEP = 0.1
async def _call_api(i, counter):
    print(f"{counter}: Calling API for {i}")
    await asyncio.sleep(SLEEP)
    print(f"{counter}: Done with API for {i}")
    return i

async def generate_response(i, counter):
    input_tokens = 100_000
    if input_tokens > TPM_LIMIT:
        raise ValueError(f"Input tokens {input_tokens} exceeds TPM limit {TPM_LIMIT}")

    # acquire the lock for the counter
    await cond.acquire()
    print(f"{counter}: Acquired lock for {i}")
    # ensure that counter.check(input_tokens) will be satisfied
    await counter.sleep_rpm()
    await counter.sleep_tpm(input_tokens)
    try:
        # yield to other threads until condition is true
        await cond.wait_for(lambda : counter.check(input_tokens))
        # schedule _call_api to run concurrently
        t = asyncio.create_task(_call_api(i, counter))
        # update counter
        counter.increment()
        counter.token_usage_per_minute += input_tokens
        print(f"{counter}: Updated counter")
        # release underlying lock and wake up 1 waiting task
        cond.notify()
        print(f"{counter}: Notified 1")
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