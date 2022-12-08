def check_tasks():
    import psutil

    processes = [p.cmdline() for p in psutil.process_iter() if p.name().lower() in ['python.exe'] and 'bg_task_checker.py' not in p.cmdline()[1]]
    #print(len(processes))
    streamAcquisitionDummy2 = [0]*len(processes)
    mechanical = [0]*len(processes)
    detect = [0]*len(processes)
    pylonFlask = [0]*len(processes)
    for i in range(len(processes)):
        if ("streamAcqusitionDummy2.py" in processes[i][1]):
            streamAcquisitionDummy2[i] = True
        elif("streamAcqusitionDummy2.py" not in processes[i][1]):
            streamAcquisitionDummy2[i] = False
        if ("mechanical.py" in processes[i][1]):
            mechanical[i] = True
        elif("mechanical.py" not in processes[i][1]):
            mechanical[i] = False
        if ("detect.py" in processes[i][1]):
            detect[i] = True
        elif("detect.py" not in processes[i][1]):
            detect[i] = False
        if ("pylonFlask.py" in processes[i][1]):
            pylonFlask[i] = True
        elif("pylonFlask.py" not in processes[i][1]):
            pylonFlask[i] = False
    if (True in streamAcquisitionDummy2):
        streamAcquisitionDummy2 = True
    else:
        streamAcquisitionDummy2 = False
    if (True in mechanical):
        mechanical = True
    else:
        mechanical = False
    if (True in detect):
        detect = True
    else:
        detect = False
    if (True in pylonFlask):
        pylonFlask = True
    else:
        pylonFlask = False
    return(streamAcquisitionDummy2, mechanical, detect, pylonFlask)

# import psutil
# print(psutil.cpu_percent(1))
# print(psutil.virtual_memory().percent)
# print(psutil.net_io_counters())
#
# import gpustat
# print(gpustat)