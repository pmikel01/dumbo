import random
import gevent
from gevent import Greenlet
from gevent.queue import Queue

from dumbomvba.core.provabledispersal import provabledispersalbroadcast
from crypto.threshsig import dealer


# CBC
def simple_router(N, maxdelay=0.01, seed=None):
    """Builds a set of connected channels, with random delay
    @return (receives, sends)
    """
    rnd = random.Random(seed)
    #if seed is not None: print 'ROUTER SEED: %f' % (seed,)

    queues = [Queue() for _ in range(N)]

    def makeSend(i):
        def _send(j, o):
            delay = rnd.random() * maxdelay
            #print 'SEND %8s [%2d -> %2d] %.2f' % (o[0], i, j, delay)
            gevent.spawn_later(delay, queues[j].put, (i,o))
            #queues[j].put((i, o))
        return _send

    def makeRecv(j):
        def _recv():
            (i,o) = queues[j].get()
            #print 'RECV %8s [%2d -> %2d]' % (o[0], i, j)
            return (i,o)
        return _recv

    return ([makeSend(i) for i in range(N)],
            [makeRecv(j) for j in range(N)])


def _test_pd(N=4, f=1, leader=None, seed=None):
    # Test everything when runs are OK
    sid = 'sidA'
    # Note thld siganture for CBC has a threshold different from common coin's
    PK, SKs = dealer(N, N - f)

    rnd = random.Random(seed)
    router_seed = rnd.random()
    if leader is None: leader = rnd.randint(0, N-1)
    print("The leader is: ", leader)
    sends, recvs = simple_router(N, seed=seed)

    threads = []
    leader_input = Queue(1)
    outputs = [Queue() for _ in range(N)]
    for i in range(N):
        input = leader_input.get if i == leader else None
        t = Greenlet(provabledispersalbroadcast, sid, i, N, f, PK, SKs[i], leader, input, outputs[i].put_nowait, recvs[i], sends[i])
        t.start()
        threads.append(t)

    m = "Hello! This is a test message."
    leader_input.put(m)
    gevent.joinall(threads)
    for t in threads:
        print(t.value)
    # Assert the CBC-delivered values are same to the input
    out = [Queue() for n in range(N)]
    print(outputs)
    for i in range(N):
        print("for node ", i)
        for j in range(len(outputs[i])):
            (mtype, context, sid, pid) = outputs[i].get()
            print(mtype, ":", context)
            out[i].put_nowait((mtype, context))
    print(out[1])
def test_pd(N, f, seed):
    _test_pd(N=N, f=f, seed=seed)


if __name__ == '__main__':
    test_pd(4, 1, None)
