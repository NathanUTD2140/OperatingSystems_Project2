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
customerLeft = [threading.Semaphore(0) for _ in range(NumberOfTellers)] #signal for customer to leave

manager = threading.Semaphore(1) #one instance of manager
safe = threading.Semaphore(2) #only two tellers at time, limit of 2
door = threading.Semaphore(2) #only two customers in at a time

queueLock = threading.Lock() #Maybe should have put one generic lock, but this tells me what it is for
customerQueue = [] #queue to be determined of customers

assignedTeller = [-1] * NumberOfCustomers #will later be stored with the customer
customerTransactions = [""] * NumberOfCustomers #initialization of desired transaction

bank_open = True #Open bank for closing later

def teller_thread(tid):
    global customersLeft, bank_open, tellersReady

    # Force startup in order
    tellerStartup[tid].acquire()

    # Print start messages
    log(f"Teller {tid} [Teller {tid}]: ready to serve")
    log(f"Teller {tid} [Teller {tid}]: waiting for a customer")

    # Mark this teller as fully ready
    with tellersReadyLock:
        tellersReady += 1
        if tellersReady == NumberOfTellers:
            tellersReadyEvent.set()

    # Allow next teller to start
    if tid + 1 < NumberOfTellers:
        tellerStartup[tid + 1].release()

    # Start customers
    while True:

        tellerWaiting[tid].acquire() #Makes sure tellers are open, basically insurance nothing crashed
        if not bank_open:
            break

        # Find which customer belongs to the teller
        with queueLock:
            cid = None
            for i in range(NumberOfCustomers):
                if assignedTeller[i] == tid: #if a teller is assigned, break out
                    cid = i #marks the customer ID
                    break

        if cid is None:
            continue ##effectively an infinite loop

        # Ask for transaction once someone is successful
        log(f"Teller {tid} [Customer {cid}]: asks for transaction")

        # Wait for transaction info
        transactionFromCustomer[tid].acquire() #gets the transaction info
        txn = customerTransactions[cid]

        # Withdraw requires manager
        if txn == "Withdraw": #if the customer wants the manager
            log(f"Teller {tid} [Customer {cid}]: going to the manager")
            manager.acquire() #get the manager semaphore
            log(f"Teller {tid} [Customer {cid}]: getting manager's permission")
            time.sleep(random.uniform(0.005, 0.030)) #simulate rest time
            log(f"Teller {tid} [Customer {cid}]: got manager's permission")
            manager.release() # release it back

        # Safe step
        log(f"Teller {tid} [Customer {cid}]: going to safe")
        safe.acquire() # checks to see if the safe is open
        log(f"Teller {tid} [Customer {cid}]: enter safe")
        time.sleep(random.uniform(0.010, 0.050)) #simulate wait time
        log(f"Teller {tid} [Customer {cid}]: leaving safe")
        safe.release() # release semaphore

        # Tell the customer it's done
        log(f"Teller {tid} [Customer {cid}]: informs customer transaction is complete")
        transactionDone[tid].release() #releases it back

        # Wait for customer to leave
        customerLeft[tid].acquire() #waits for this to be true to signal if teller is free
        # Teller is free again
        tellerAvailable[tid].release()

        # Reduce remaining customers down by 1
        with queueLock:
            customersLeft -= 1
            if customersLeft == 0: #once we reach 0, we are done for the day
                bank_open = False #Bank close
                for t in tellerWaiting:
                    t.release() #release all teller semaphores once done

        if not bank_open:
            break #otherwise just break out
