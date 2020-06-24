
import winreg # to use windows registry to ID guids given by netifaces
import netifaces # used to identify netwrok interafces on a system and returning the ocrresponding guid
import pickle # used to save the model for further testing and use
import csv #python standard for csv work
import pyshark # tshark wrapper used to capture and parse packets
import time #allows for time be used
import datetime #allows for dates to be used
import pandas # data handler for input into Aritificial neural network
from timeit import default_timer as timer
from sklearn.preprocessing import LabelEncoder
from DrawAnnv2 import DrawNN

def main():
        print(__doc__)
        int = netifaces.interfaces()
        mlp_live_iteration = 0
        allowed_IP = ['192.168.1.1', '192.168.1.2', '192.168.1.3', '192.168.1.4']
        cap = pyshark.FileCapture('test.pcap') # For training

        def get_ip_layer_name(pkt): #allows the program to differentiate between ipv4 and ipv6, needed for correct parsing of packets
            for layer in pkt.layers:
                if layer._layer_name == 'ip':
                    return 4
                elif layer._layer_name == 'ipv6':
                    return 6
        
        def packet_info(cap): # Goes through each packet in capture or live_capture, displays various information about each packet
            start_time = time.time()
            try:
                i = 1
                for pkt in cap:
                    i += 1
                    try:
                            if pkt.highest_layer != 'ARP':
                                ip = None
                                ip_layer = get_ip_layer_name(pkt)
                                if ip_layer == 4:
                                    ip = pkt.ip
                                elif ip_layer == 6:
                                    ip = pkt.ipv6
                                print ('Packet %d' % i)
                                print (pkt.highest_layer)
                                print (pkt.transport_layer)
                                print('Time', time.strftime("%Y-%m-%d %H:%M:%S"))
                                print ('Layer: ipv%d' % get_ip_layer_name(pkt))
                                print ('Source IP:', ip.src)
                                print ('Destination IP:', ip.dst)
                                print ('Length: ', pkt.length)
                                try:
                                    print ('Source Port', pkt[pkt.transport_layer].srcport)
                                    print ('Destination Port', pkt[pkt.transport_layer].dstport)
                                except AttributeError:
                                    print ('Source Port: ', 0)
                                    print ('Destination Port: ', 0)
                                print (i/(time.time() - start_time))
                                print ('')
                            else:
                                arp = pkt.arp
                                print(pkt.highest_layer)
                                print(pkt.transport_layer)
                                print('Layer: ipv4' )
                                print('Time', time.strftime("%Y-%m-%d %H:%M:%S"))
                                print('Source IP: ', arp.src_proto_ipv4)
                                print('Destination IP: ', arp.dst_proto_ipv4)
                                print ('Length: ', pkt.length)
                                print ('Source Port: ', 0)
                                print ('Destination Port: ', 0)
                                print (i/(time.time() - start_time))
                                print()
                    except (AttributeError, UnboundLocalError, TypeError) as e:
                            pass
                return
            except KeyboardInterrupt:
                pass
       
        def csvgather(cap): # creates/rewrites 'test.csv' file - writes header row - goes through packets, writing a row to the csv for each packet
            start_time = time.time()
            with open('Data.csv', 'w', newline='') as csvfile:
                filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                filewriter.writerow(
                    ['Highest Layer', 'Transport Layer', 'Source IP', 'Dest IP', 'Source Port', 'Dest Port',
                     'Packet Length', 'Packets/Time', 'target'])

                i = 0
                start = timer()
                for pkt in cap:
                    end = timer()
                    try:
                                if pkt.highest_layer != 'ARP':
                                    ip = None
                                    ip_layer = get_ip_layer_name(pkt)
                                    if ip_layer == 4:
                                        ip = pkt.ip
                                        ipv = 0  # target test
                                        if pkt.transport_layer == None:
                                            transport_layer = 'None'
                                        else:
                                            transport_layer = pkt.transport_layer
                                    elif ip_layer == 6:
                                        ip = pkt.ipv6
                                        ipv = 1  # target test

                                    try:
                                        if ip.src not in allowed_IP:
                                            ipcat = 1
                                            target = 1
                                        else:
                                            ipcat = 0
                                            target = 0
                                        filewriter.writerow([pkt.highest_layer, transport_layer, ipcat, ip.dst,
                                                             pkt[pkt.transport_layer].srcport,
                                                             pkt[pkt.transport_layer].dstport,
                                                             pkt.length, i / (time.time() - start_time), target])
                                        #print("Time: ", time.time() - start_time)
                                        #print("Packets Collected:", i)
                                        i += 1
                                    except AttributeError:
                                        if ip.src not in allowed_IP:
                                            ipcat = 1
                                            target = 1
                                        else:
                                            ipcat = 0
                                            target = 0
                                        filewriter.writerow(
                                            [pkt.highest_layer, transport_layer, ipcat, ip.dst, 0, 0,
                                             pkt.length, i / (time.time() - start_time), target])
                                        print("Time: ", time.time() - start_time)
                                        print("Packets Collected:", i)
                                        i += 1

                                else:
                                    if pkt.arp.src_proto_ipv4 not in allowed_IP:
                                        ipcat = 1
                                        target = 1
                                    else:
                                        ipcat = 0
                                        target = 0
                                    arp = pkt.arp
                                    filewriter.writerow(
                                        [pkt.highest_layer, transport_layer, ipcat, arp.dst_proto_ipv4, 0, 0,
                                         pkt.length, i / (time.time() - start_time), target])
                                    print("Time: ", time.time() - start_time)
                                    print("Packets Collected:", i)
                                    i += 1
                    except (UnboundLocalError, AttributeError) as e:
                        pass

        def int_names(int_guids): # Looks up the GUID of the network interfaces found in the registry, then converts them into an identifiable format
            int_names = int_names = ['(unknown)' for i in range(len(int_guids))]
            reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            reg_key = winreg.OpenKey(reg, r'SYSTEM\CurrentControlSet\Control\Network\{4d36e972-e325-11ce-bfc1-08002be10318}')
            for i in range(len(int_guids)):
                try:
                    reg_subkey = winreg.OpenKey(reg_key, int_guids[i] + r'\Connection')
                    int_names[i] = winreg.QueryValueEx(reg_subkey, 'Name')[0]
                except FileNotFoundError:
                    pass
            return int_names
                
        def LabelEncoding(data): # encodes the categorical data within the csv used for training, turns the categorical values into integer values

            data = pandas.read_csv('TestingData.csv', delimiter=',')
            columnsToEncode = list(data.select_dtypes(include=['category', 'object']))  
            #print(data.dtypes) #Prints each columns d_type
            #print(columnsToEncode) #Prints categorical features
            
            le = LabelEncoder()
            for feature in columnsToEncode:
                try:
                    data[feature] = le.fit_transform(data[feature])
                    #print(data[feature])
                except:
                    print ('error' + feature)
            return data
        
        def csv_data_check(): # Displays the data within the chosen csv, allows the user to view ALL data, ONLY NUMERICAL or ONLY CATEGORICAL
            l_data = input("Name of csv file: ")
            data = pandas.read_csv(l_data, delimiter=',')
            read_choice = input("""How would you like to view the data?
                                
                                All (a)
                                Numerical Only (n)
                                Categorical Only (c)
                                
                                """)
            if read_choice == "a":
                print(data)
            elif read_choice == "n":
                print(data._get_numeric_data())
            elif read_choice == "c":
                print(data.select_dtypes(include='object'))
        
        def Load_model(): # loads a saved model to use for both training 

            filename = input("Model to load?")
            loaded_model = pickle.load(open(filename, 'rb'))
            print(loaded_model.coefs_)
            print(loaded_model.loss_)
            
            return loaded_model

        def int_choice(): #allows the user to choose interface
            for i, value in enumerate(int_names(int)):
                print(i, value)
            print('\n')
            iface = input("Please select interface: ")
            cap = pyshark.LiveCapture(interface= iface)
            cap.sniff_continuously(packet_count=None)
            
            return cap  

        def MLP(): #Primarily used for training either a new model or updating a previous model

            l_data = input("Name of CSV file? ") # User inputs name of Dataset CSV file
            
            load = input("Load model?") # Asks user if thye want to train a saved algorithm, if no, new model is created and trained
            if load == 'y':
                mlp = Load_model()

            else:
                from sklearn.neural_network import MLPClassifier #imports the neural network class from Sci-kit learn
                mlp = MLPClassifier(hidden_layer_sizes=(100,100),activation='logistic', max_iter=1000, verbose=True, tol=0.00000001, early_stopping = True, shuffle = True) # Designates the setting of the model before training
                #hidden_layer_sizes = array of the hidden layer of the network, (5) = one layer of 5 nodes, (5,5) = 2 layers, both with 5 nodes
                #activation = activation function, 'logistic' is equivalent ot the sigmoid activation function
                #max_iter = max3imum amoung of iterations that the model will do
                #Verbose = whether the model prints the iteration and loss function per iteration
                #tol = the decimal place the use wants the loss function to reach

            data = pandas.read_csv(l_data, delimiter=',')# reads CSV
            data = LabelEncoding(data) #Encodes the categorical data into int input data the model can use

            X = data[['Highest Layer', 'Transport Layer', 'Source IP', 'Dest IP', 'Source Port', 'Dest Port','Packet Length', 'Packets/Time']] # Data used to train

            y = data['target'] # targets for the MLP

            
            from sklearn.model_selection import train_test_split #Needed to split the data into the training and testing
            from sklearn.preprocessing import StandardScaler #required to so that all the inputs are in a comparable range
            X_train, X_test, y_train, y_test = train_test_split(X, y)
            scaler = StandardScaler()
            
            scaler.fit(X_train)
            X_train = scaler.transform(X_train)
            X_test = scaler.transform(X_test)
            
            print(X_train) # Training data (Features)
            print(X_test) # Testing data (features
            start_time = timer()
            mlp.fit(X_train, y_train) # fit is used to actually train the model
            print(mlp.predict(X_test))
            end_time = timer()
            time_taken = end_time - start_time
            predictions = mlp.predict(X_test)
            print()
            print("First 50 Predictions: ", "\n" ,mlp.predict(X_test)[0:50]) #Prints first 50 predictions
            print()
            print("First 50 Probabilities: ", "\n",mlp.predict_proba(X_test)[0:50])#Prints first 50 probabilities
            print()
            print("Number of Iterations: ", mlp.n_iter_)
            print()
            hostile = 0
            safe = 0
            for check in predictions:
                if check == 1:
                    hostile += 1
                else:
                    safe += 1
            print("Safe Packets: ", safe)
            print("Hostile Packets: ", hostile)
            print("Time Taken:", time_taken)
                                        
            from sklearn.metrics import classification_report,confusion_matrix
            print("Confusion Matrix: ", "\n", confusion_matrix(y_test,predictions))
            print()

            print ("Classification Report: ", "\n",  classification_report(y_test,predictions))
            print()

            ci = input("do you want to see weights and intercepts? " )
            if ci == 'y':
                print("Model Coefficients (Weights): ", "\n", mlp.coefs_)
                print()
                print("Model Intercepts (Nodes): ", "\n", mlp.intercepts_)
            else:
                pass
            
            save = input("Save model? ")
            if save == 'y':
                        filename = input("Filename for saving?: ")
                        pickle.dump(mlp, open(filename, 'wb'))
            
        def MLP_Live_predict(cap, modelname, mlp_live_iteration):  # similar to MLP(), used for real-time classification and not for training             
                
            data = pandas.read_csv('LiveAnn.csv', delimiter=',') # reads CSV
            data = LiveLabelEncoding(data)
            print("Processing Data", "\n")
            print(data)
            X = data[['Highest Layer', 'Transport Layer', 'Source IP', 'Dest IP', 'Source Port', 'Dest Port','Packet Length', 'Packets/Time' ]] # Data used to train

            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            scaler.fit(X)
            X = scaler.transform(X)

            loaded_model = pickle.load(open(modelname, 'rb')) # loads model
            print("Model Coeffcients ", loaded_model.coefs_) # load model coefs

            lmlp = loaded_model

            predictions = lmlp.predict(X) # preditcions made by model

            hostile = 0 # this block counts how many 'hostile' packets have been predicted by the model
            safe = 0
            for check in predictions:
                if check == 1: # change to 0 to force ddos attack
                    hostile += 1
                else:
                    safe += 1
            print("Safe Packets: ", safe)
            print("Possible Hostile Packets: ", hostile)
            print(100 * hostile/(safe + hostile))
            print ("\n")
            mlp_live_iteration += 1

            if hostile >= ((safe + hostile)/2):
                testwrite = open('log.txt', 'a+')
                testwrite.write('Attack Detected at: ')
                testwrite.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
                testwrite.write('\n')
                testwrite.write('Packets collected: ')
                testwrite.write(str(safe + hostile))
                testwrite.write('\n')
                return ("Attack")
            else:
                testwrite = open('log.txt', 'a+')
                testwrite.write('Normal Activity Detected at: ')
                testwrite.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
                testwrite.write('\n')
                testwrite.write('Packets collected: ')
                testwrite.write(str(safe + hostile))
                testwrite.write('\n \n')

                return mlp_live_iteration
            print("Predictions")
            print (predictions)
            from sklearn.metrics import classification_report,confusion_matrix

            print(confusion_matrix(y,predictions))
            print(classification_report(y,predictions))


        def csv_interval_gather(cap): # creates/rewrites 'Live.csv' file with 30 second intervals- writes header row - goes through packets, writing a row to the csv for each packet
            start_time = time.time()
            with open ('LiveAnn.csv', 'w', newline='') as csvfile:
                filewriter = csv.writer(csvfile, delimiter=',' , quotechar='|', quoting=csv.QUOTE_MINIMAL)
                filewriter.writerow(['Highest Layer', 'Transport Layer', 'Source IP', 'Dest IP', 'Source Port', 'Dest Port','Packet Length', 'Packets/Time'])

                i = 0
                start = timer()
                for pkt in cap:
                    end = timer()
                    if (end - start < 30):
                        try:
                                if pkt.highest_layer != 'ARP':
                                    print("Packets Collected:", i)
                                    if pkt.highest_layer != 'ARP':
                                        ip = None
                                        ip_layer = get_ip_layer_name(pkt)
                                        if ip_layer == 4:
                                            ip = pkt.ip
                                            #ipv = 0 # target test
                                            if pkt.transport_layer == None:
                                                transport_layer = 'None'
                                            else:
                                                transport_layer = pkt.transport_layer
                                        elif ip_layer == 6:
                                            ip = pkt.ipv6
                                            #ipv = 1 # target test
                                        try:
                                            if ip.src not in allowed_IP:
                                                    ipcat = 1
                                            else:
                                                    ipcat = 0
                                            filewriter.writerow([pkt.highest_layer, transport_layer, ipcat, ip.dst, pkt[pkt.transport_layer].srcport, pkt[pkt.transport_layer].dstport,pkt.length, i/(time.time() - start_time)])
                                            print ("Time: ", time.time() - start_time)
                                            i += 1
                                        except AttributeError:
                                            if ip.src not in allowed_IP:
                                                    ipcat = 1
                                            else:
                                                    ipcat = 0
                                            filewriter.writerow([pkt.highest_layer, transport_layer, ipcat, ip.dst, 0, 0, pkt.length, i/(time.time() - start_time)])
                                            print ("Time: ", time.time() - start_time)
                                            i += 1

                                    else:
                                        if pkt.arp.src_proto_ipv4 not in allowed_IP:
                                                ipcat = 1
                                        else:
                                                ipcat = 0
                                        arp = pkt.arp
                                        filewriter.writerow([pkt.highest_layer , transport_layer, ipcat, arp.dst_proto_ipv4, 0, 0, pkt.length, i/(time.time() - start_time)])
                                        print ("Time: ", time.time() - start_time)
                                        i += 1
                        except (UnboundLocalError, AttributeError) as e:
                                pass
                    else:
                        return
                    
        def LiveLabelEncoding(data): # same as LabelEncoding(), but use for realtime
            data = pandas.read_csv('LiveAnn.csv', delimiter=',') 
            columnsToEncode = list(data.select_dtypes(include=['category', 'object']))  
            print(columnsToEncode)
            le = LabelEncoder()
            for feature in columnsToEncode:
                try:
                    data[feature] = le.fit_transform(data[feature])
                    #print(data[feature])
                except:
                    print ('error ' + feature)
            return data
            
        def menu(): #Basic Menu           
            ans = True
            live = True
            while ans:
                print ("""
                1. Visual Packet Sniffer
                2. ANN Data gatherer
                3. Neural Network Trainer
                4. Data Check
                5. Live Neural Network
                6. Visual Model 
                7. Exit
                """)
    
                ans = input("What would you like to do? ") 
                if ans=="1":
                    cap = int_choice()
                    packet_info(cap)
                elif ans=="2":
                    cap = int_choice()
                    print("Now Gathering data....")
                    csvgather(cap)
                elif ans=="3":
                    MLP()
                elif ans =="4":
                    csv_data_check()
                elif ans == "5":
                    cap = int_choice()
                    modelname = input("Please input model: ")
                    try:
                        while live:                                      
                            csv_interval_gather(cap)
                            if MLP_Live_predict(cap, modelname, mlp_live_iteration) == "Attack": #if an attack had been detectedm then print date and time of the attack
                                live = False
                                print("DDoS ATTACK DETECTED! @ ", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
                                MLP_Live_predict(cap, modelname, mlp_live_iteration) == 0
                    except KeyboardInterrupt:
                        pass                            
                elif ans == "6":
                    network = DrawNN([8,100,100,1])
                    network.draw()
    
                elif ans == "7":
                    break
        menu()
main()
