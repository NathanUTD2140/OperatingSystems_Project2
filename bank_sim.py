import threading
import random
import time

# Log system, not thread dependent unless we lock it. 
logLock = threading.Lock()

def log(msg):
    """ Logs atomically to both the terminal and an output file. """
    with logLock:
        print(msg) #Terminal output
        with open("output.txt", "a") as f: #What to write out to the file
            f.write(msg + "\n") # message that is passed to log
          
# GLOBAL CONSTANTS & SYNCHRONIZATION OBJECTS

NumberOfTellers = 3
NumberOfCustomers = 50
customersLeft = NumberOfCustomers ##will be decremented later as customers leave

# Ordered Teller Startup
tellerStartup = [threading.Semaphore(0) for _ in range(NumberOfTellers)] # Set it as just for the one
tellerStartup[0].release()   # Teller 0 starts immediately, since we want the program to go

# Tellers Ready setting
tellersReady = 0 # we are not ready ay first
tellersReadyLock = threading.Lock() #Lock for the ready
tellersReadyEvent = threading.Event() #sets events that we will declare later on!

#Synchronization Semaphores
tellerAvailable = [threading.Semaphore(1) for _ in range(NumberOfTellers)] #Teller availability will be set, only one instance for all tellers
tellerWaiting = [threading.Semaphore(0) for _ in range(NumberOfTellers)] #We will need to wait occasionally for all tellers
transactionFromCustomer = [threading.Semaphore(0) for _ in range(NumberOfTellers)] #tranascation for this process
transactionDone = [threading.Semaphore(0) for _ in range(NumberOfTellers)] #completion of transacion, need to signal back

manager = threading.Semaphore(1) #one instance of manager
safe = threading.Semaphore(2) #only two tellers at time, limit of 2
door = threading.Semaphore(2) #only two customers in at a time

queueLock = threading.Lock() #Maybe should have put one generic lock, but this tells me what it is for
customerQueue = [] #queue to be determined of customers

assignedTeller = [-1] * NumberOfCustomers #will later be stored with the customer
customerTransactions = [""] * NumberOfCustomers #initialization of desired transaction

bank_open = True #Open bank for closing later
