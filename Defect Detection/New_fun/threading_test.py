import tkinter,time,random
from threading import Thread
import queue
class GuiPart():
    def __init__(self,master,queue,endCommand):
        self.queue=queue
        tkinter.Button(master,text='Done',command=endCommand).pack()
    def processIncoming(self):
        while self.queue.qsize():
            try:
                msg=self.queue.get(0)
                print (msg)
            except queue.Empty:
                pass

class ThreadedClient():
    def __init__(self,master):
        self.master=master
        self.queue=queue.Queue()
        self.gui=GuiPart(master,self.queue,self.endApplication)
        self.running=True
        self.thread1=Thread(target=self.workerThread1)
        self.thread1.start()
        self.periodicCall()
    def periodicCall(self):
        self.master.after(200,self.periodicCall)
        self.gui.processIncoming()
        if not self.running:
            self.master.destroy()
    def workerThread1(self):
        #self.ott=Tkinter.Tk()
        #self.ott.mainloop()
        while self.running:
            time.sleep(rand.random()*1.5)
            msg=rand.random()
            self.queue.put(msg)
    def endApplication(self):
        self.running=False
rand=random.Random()
root=tkinter.Tk()
client=ThreadedClient(root)
root.mainloop()