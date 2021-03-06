import subprocess
import xml.etree.ElementTree as ET
import sys

#needed for warningdialog
from src.gui.dialogs.WarningDialog import WarningDialog
import gi; gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

def printError(message):
    print "\r\n\r\n!!!!!!!!!!\r\nERROR:\r\n", message, "\r\n!!!!!!!!!!\r\n"
    print "Exiting..."
    exit()


if len(sys.argv) < 2:
    print "Usage: python workshop-creator.py <input filename>"
    exit()

inputFilename = sys.argv[1]

tree = ET.parse(inputFilename)
root = tree.getroot()

pathToVirtualBox = root.find('vbox-setup').find('path-to-vboxmanage').text
vmset = root.find('testbed-setup').find('vm-set')

# ---here we look at each vmset
numClones = int(vmset.find('num-clones').text)
cloneSnapshots = vmset.find('clone-snapshots').text
linkedClones = vmset.find('linked-clones').text
baseGroupname = vmset.find('base-groupname').text

baseOutname = vmset.find('base-outname').text

vrdpBaseport = vmset.find('vrdp-baseport').text

try:
    baseAddress = vmset.find('base-address').text
except Exception:
    baseAddress = "128"
host_id = baseAddress

# Checking if IP addresses of the clones are between 0 and 255
if(int(baseAddress) <= 0 or (int(baseAddress) + int(numClones) - 1) >= 255):
    WarningDialog(Gtk.Window(), "Make sure all clone IP addresses are between 0-255")
    exit()


for vm in vmset.findall('vm'):
    myBaseOutname = baseOutname
    for i in range(1, numClones + 1):
        vmname = vm.find('name').text

        # check to make sure the vm exists:
        getVMsCmd = [pathToVirtualBox, "list", "vms"]
        vmList = subprocess.check_output(getVMsCmd)
        if vmname not in vmList:
            print "VM not found: ", vmname
            print "Exiting"
            exit()
        
        if len(vm.findall('internalnet-basename')) > 0:
            internalnets = vm.findall('internalnet-basename')
            internalnetNames = []
            for internalnet in internalnets:
                internalnetNames.append(internalnet.text+ myBaseOutname + str(i))
            print "Internal net names: ", internalnetNames
        if len(vm.findall('generic-driver')) > 0:
            generic_drivers = vm.findall('generic-driver')
            generic_driver_names = []
            for generic_driver in generic_drivers:
                generic_driver_names.append(generic_driver.text + str(i))
            print "Generic Driver names: ", generic_driver_names

        # clone the vm and give it a name ending with myBaseOutname
        cloneCmd = [pathToVirtualBox, "clonevm", vmname, "--register"]
        #NOTE, the following logic is not in error. Linked clone can only be created from a snapshot.
        if cloneSnapshots == 'true':
            if linkedClones == 'true':
                try:
                    # get the name of the newest snapshot
                    getSnapCmd = [pathToVirtualBox, "snapshot", vmname, "list", "--machinereadable"]
                    snapList = subprocess.check_output(getSnapCmd)
                    latestSnapUUID = snapList.split("CurrentSnapshotUUID=\"")[1].split("\"")[0]
                    cloneCmd.append("--snapshot")
                    cloneCmd.append(latestSnapUUID)
                    cloneCmd.append("--options")
                    cloneCmd.append("link")
                except Exception:
                    printError(
                        "Using the link clone option requires that VMs contain a snapshot. No snapshot found for vm:" + vmname)
                    WarningDialog(Gtk.Window(), "You need snapshots to clone!")
                    print "Exiting..."
                    exit()
            else:
                cloneCmd.append("--mode")
                cloneCmd.append("all")
        newvmName = vmname + myBaseOutname + str(i)
        cloneCmd.append("--name")
        cloneCmd.append(newvmName)
        print("\nexecuting: ")
        print(cloneCmd)
        try:
            result = subprocess.check_output(cloneCmd)
        except Exception:
            printError("Make sure that the clone does not already exist:" + newvmName)
            exit()
        print("\nresult: ")
        print(result)

        # internal network setup
        netNum = 1
        if len(vm.findall('internalnet-basename')) > 0:

            for internalnetName in internalnetNames:        
                intNetCmd = [pathToVirtualBox, "modifyvm", newvmName, "--nic"+str(netNum), "intnet", "--intnet"+str(netNum), internalnetName]
                print("\nsetting up internal network adapter")
                print("executing: ")
                print(intNetCmd)
                result = subprocess.check_output(intNetCmd)
                netNum+=1
                # commented out the next line because an error about non-mutable state is reported even thought it still completes successfully
                # print(result)
        if len(vm.findall('generic-driver')) > 0:
            
            for generic_driver_name in generic_driver_names:
                udpTunnelCmd = [pathToVirtualBox, "modifyvm", newvmName, "--nic"+str(netNum), "generic", "--nicgenericdrv"+str(netNum), "UDPTunnel", "--nicproperty"+str(netNum), ("dest=10.0.1."+host_id), "--nicproperty"+str(netNum), ("sport="+host_id), "--nicproperty"+str(netNum), ("dport="+host_id)]
                print("\nsetting up generic driver network adapter")
                print("executing: ")
                print(udpTunnelCmd)
                result = subprocess.check_output(udpTunnelCmd)
                netNum+=1
                host_id = str(int(host_id) + 1)


        # for some reason, the vms aren't placed into a group unless we execute an additional modify command
        try:
            groupCmd = [pathToVirtualBox, "modifyvm", newvmName, "--groups", "/" + baseGroupname + "/Unit" + str(i)]
            print("\nsetting up group for " + newvmName)
            print("\nexecuting: ")
            print(groupCmd)
            result = subprocess.check_output(groupCmd)
            print(result)
        except Exception:
            print "Could not move VM", newvmName, "to group:", netAdapterName

        # vrdp setup
        vrdpEnabled = vm.find('vrdp-enabled').text
        if vrdpEnabled and vrdpEnabled == 'true':
			#set interface to vrde
            vrdpCmd = [pathToVirtualBox, "modifyvm", newvmName, "--vrde", "on", "--vrdeport", str(vrdpBaseport)]
            print("\nsetting up vrdp for " + newvmName)
            print("\nexecuting: ")
            print(vrdpCmd)
            result = subprocess.check_output(vrdpCmd)
            print(result)
            vrdpBaseport = str(int(vrdpBaseport) + 1)
            
            #now these settings will help against the issue when users 
            #can't reconnect after an abrupt disconnect
            #https://www.virtualbox.org/ticket/2963
            vrdpCmd = [pathToVirtualBox, "modifyvm", newvmName, "--vrdereusecon", "on", "--vrdemulticon", "off"]
            print("\Fix vrde for " + newvmName)
            print("\nexecuting: ")
            print(vrdpCmd)
            result = subprocess.check_output(vrdpCmd)
            print(result)
                       
        # finally create a snapshot after the vm is setup
        try:
            snapCmd = [pathToVirtualBox, "snapshot", newvmName, "take", "ready"]
            print("\ntaking snapshot for " + newvmName)
            print("\nexecuting: ")
            print(snapCmd)
            result = subprocess.check_output(snapCmd)
            print(result)
        except Exception:
            print "Could not take snapshot for VM", newvmName

print """
**************************************************************************************
If you have the VirtualBox GUI open, you must restart it to see the workshop groupings
**************************************************************************************
"""
