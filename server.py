from bottle import *
import db
from subprocess import Popen, PIPE, call
import os, signal, time, json
app = Bottle()

class RoiData():
    def __init__(self):
        name = ""
        rois = []
        trackingType = 0
        
@app.route('/static/<filepath:path>')
def server_static(filepath):
    print (filepath)
    return static_file(filepath, root='static')

@app.route('/')
def index():
    _,status = checkPid()
    df = subprocess.Popen(["df", "./"], stdout=subprocess.PIPE)
    output = df.communicate()[0]
    print(output)
    device, size, used, available, percent, mountpoint = \
                                                   output.split(b"\n")[1].split()
    return template('index', machineId=mid, status=status, freeSpace = percent)

@app.route('/websocket')
def handle_websocket():
    #try:
    data = readData()
    return(data)
    #except:
        #print("error")
       


@app.post('/ROI')
def new_roi():
    roiData = request.json
    #load saved rois and then add the new one
    try:
        roiList = db.load()
        roiList[len(roiList)]=roiData
        db.save(roiList)
    except:
        """file does not exits yet"""
        db.save(roiData)
        



@app.get('/ROI')
def list_roi():
    response.content_type = 'application/json'
    roisSaved = db.load()
    dataToSend = {}
    dataToSend['name']="Rois Saved in SM"
    dataToSend['data'] = roisSaved
    
    print (dataToSend['data'])
    return (dataToSend)

@app.put('/started')
def starStop():
    try:
        data = request.json
        print (data)
    except:
        print ("no data")
    pid, isAlreadyRunning = checkPid()
    print(pid, isAlreadyRunning)
    if isAlreadyRunning:
        os.kill(pid,signal.SIGTERM)
        print(pid)
    else:
        db.writeMask(data)
        #f = open('mask.msk','wb')
        #pickle.dump(data['roi'], f)
        #f.close()
        pySolo = Popen(["python2","pvg_standalone.py", 
                        "-c", "pysolo_video.cfg",
                        "-i","0",
                        "-k", "mask.msk",
                        "-t", str(data['trackingType']),
                        "-o", "output.txt",
                        "--showmask",
                        "--trackonly"])
        
        #pySolo = Popen(["python2", "pvg.py"])# -c pysolo_video.cfg -i 0 -k mask.msk -t 0 -o output.txt", shell=True)
        
    
@app.get('/refresh')
def refresh():
    pid, isAlreadyRunning = checkPid()
    if isAlreadyRunning:
        #add a call to a function to update snapshot
        pass 
    else:
        pySolo = call(["python2","pvg_standalone.py", 
                        "-c", "pysolo_video.cfg",
                        "-i","0",
                        "--snapshot",])
    redirect("/")
    #_,status = checkPid()
    #return template('index', machineId=mid, status=status)


@app.route('/downloadData/<machineID>')
def downloadData(machineID):
    pid, isAlreadyRunning = checkPid()
    #Add a "last downloaded" and "free space available"
    return static_file('output.txt', root='')

@app.get('/visualizeData')
def visualizeData():
    pid, isAlreadyRunning = checkPid()   
    return static_file('output.txt', root='')

def checkPid():
    proc = Popen(["pgrep", "-f", "python2 pvg_standalone.py"], stdout=PIPE)
    try:
        pid=int(proc.stdout.readline())
        started=True
    except:
        started=False
        pid = None
    proc.stdout.close()
    print(pid)
    return pid, started

def checkMachineId():
    f = open('/etc/pt-machine-id','r')
    piId = f.read().rstrip()
    f.close()
    return piId
 
def readData():
    f = open('output.txt','r')
    lines = f.readlines()
    f.close()
    lastData = lines[-1]
    splitedData = lastData.split('\t')
    jsonData = json.dumps(splitedData)
    print (jsonData)
    return jsonData
    
roiList={}
mid= checkMachineId()
run(app,host='0.0.0.0', port=8088, debug=True)

#from gevent.pywsgi import WSGIServer
#from geventwebsocket.handler import WebSocketHandler
#server = WSGIServer(("0.0.0.0", 8088), app,
#                    handler_class=WebSocketHandler)
#server.serve_forever()
