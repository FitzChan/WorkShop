import time

t1 = time.strftime('%H:%M',time.localtime(time.time()))
print(t1)
interval = 3600
t2 = time.strftime('%H:%M',time.localtime(time.time()+interval))
print(t2)
for i in range(2):
    print(i)