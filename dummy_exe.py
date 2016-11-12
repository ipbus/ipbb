#!/bin/env python

import time
import random
import string

N=80
for i in xrange(50):
    time.sleep(0.2)
    print i,''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(N))