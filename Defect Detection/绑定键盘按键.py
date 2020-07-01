import tkinter
from tkinter import ttk


def xFunc1(event):
    print("事件触发键盘输入:",{event.char},"对应的ASCII码:",{event.keycode})
    if event.keycode == 38:
        print('up')
    if event.keycode == 40:
        print('down')


win = tkinter.Tk()
win.title("Kahn Software v1")  # #窗口标题
win.geometry("600x500+200+20")  # #窗口位置500后面是字母x
'''
响应所有事件(键盘)
<Key>   所有键盘按键会触发
'''
xLabel = tkinter.Label(win, text="KAHN Hello world")
xLabel.focus_set()
xLabel.pack()
xLabel.bind("<Key>", xFunc1)

win.mainloop()  # #窗口持久化