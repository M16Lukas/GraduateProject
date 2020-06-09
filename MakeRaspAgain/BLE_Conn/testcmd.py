import sys
import os
import time
import subprocess
import threading

class Distance(threading.Thread):
    def __init__(self, rssi, txpower):
        threading.Thread.__init__(self)
        self.rssi = rssi
        self.txpower = txpower
        
    def run(self):
        if self.rssi == 0:
            return -1.0 # if we can't determine accuracy, return -1
        
        ratio = self.rssi*1.0/self.txpower
        if ratio < 1.0:
            y = pow(ratio, 10)
        else:
            y = (0.89976)*pow(ratio, 7.7095)+0.111
        return y
