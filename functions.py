from django.utils.translation import ugettext as TranslatedText
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.utils import translation
from django.http import HttpResponse
from django.http import JsonResponse
import requests, logging, random, json

#-------------------------#
#- Proxmox API Functions -#
#-------------------------#
## Proxmox API Info
# Example values need to be change. No this keys are not valid :)
TOKEN_NAME = 'root@pam!restapi'
API_TOKEN = 'eea680c4-4356-48c7-bdd3-d36a973cf56b'
API_URL = 'https://10.10.50.41:8006/api2/json'

## General Request Function
def Send_Request(Method, Func, Data={}):
    URL = API_URL + Func
    Headers = {
        'Authorization': 'PVEAPIToken={}={}'.format(TOKEN_NAME, API_TOKEN)
    }
    if Method == 'GET':
        Response = requests.get(URL, headers=Headers, verify=False)
    elif Method == 'POST':
        Response = requests.post(URL, headers=Headers, data=Data, verify=False)
    elif Method == 'PUT':
        Response = requests.put(URL, headers=Headers, data=Data, verify=False)
    elif Method == 'DELETE':
        Response = requests.delete(URL, headers=Headers, data=Data, verify=False)
    else:
        return 'Wrong HTTP Method given!'

    return HttpResponse(Response), Response, Response.text

## List Nodes in Cluster
def List_Nodes():
    return Send_Request('GET', '/nodes/')

## List VMs in Node
def List_VMs(NODE):
    return Send_Request('GET', '/nodes/{}/qemu'.format(NODE))

## Start VM
def Start_VM(NODE, VMID):
    return Send_Request('POST', '/nodes/{}/qemu/{}/status/start'.format(NODE, VMID))

## Reboot VM
def Reboot_VM(NODE, VMID):
    return Send_Request('POST', '/nodes/{}/qemu/{}/status/reboot'.format(NODE, VMID))

## Shutdown VM
def Shutdown_VM(NODE, VMID):
    return Send_Request('POST', '/nodes/{}/qemu/{}/status/shutdown'.format(NODE, VMID))

## Stop VM
def Stop_VM(NODE, VMID):
    return Send_Request('POST', '/nodes/{}/qemu/{}/status/stop'.format(NODE, VMID))

## Delete VM
def Delete_VM(NODE, VMID):
    Data = {
        'purge': 1
    }
    return Send_Request('DELETE', '/nodes/{}/qemu/{}'.format(NODE, VMID))

## Get VM Info
def Get_VM_Info(NODE, VMID):
    Func = '/nodes/{}/qemu/{}/status/current'.format(NODE, VMID)

    return Send_Request('GET', Func)

## Get VM Statistics
def Get_VM_RRD_Data(NODE, VMID, TimeFrame):
    Func = '/nodes/{}/qemu/{}/rrddata?timeframe={}'.format(NODE, VMID, TimeFrame)

    return Send_Request('GET', Func)

## Connect VM VNC (Not working right now)
def Get_VM_VNC(NODE, VMID):
    Func = '/nodes/{}/qemu/{}/vncproxy'.format(NODE, VMID)
    Data = {
        'websocket': 1
    }
    VNCProxy = json.loads(Send_Request('POST', Func, Data)[2])['data']
    return VNCProxy

## Resize VM Disk
def Resize_VM_Storage(NODE, VMID, Storage):
    Func = '/nodes/{}/qemu/{}/resize'.format(NODE, VMID)
    Data  = {
        'disk': 'scsi0',
        'node': NODE,
        'size': '{}G'.format(Storage),
        'vmid': VMID
    }

    return Send_Request('PUT', Func, Data)

## Configure VM
def Config_VM(NODE, VMID, Product):
    Func = '/nodes/{}/qemu/{}/config'.format(NODE, VMID)
    Data = {
        'node': NODE,
        'vmid': VMID,
        'cores': Product['CPU'],
        'memory': int(Product['RAM']) * 1024 ,
        'onboot': 1,
        'ostype': 'l26',
        'kvm': 0, # For test only. This required for my own test lab because of nested vm.
        'ciuser': 'root',
        'cipassword': 'dstlr',
        'sshkeys': '' # urlencoded
    }

    return Send_Request('POST', Func, Data), Resize_VM_Storage(NODE, VMID, Product['Storage'])

## Create VM
def Create_VM(NODE, Template_VMID, Product, VMID, NAME):
    print(NODE, Template_VMID, Product, VMID)
    Func = '/nodes/{}/qemu/{}/clone'.format(NODE, Template_VMID['Template_VMID'])
    Data  = {
        'newid': VMID,
        'node': NODE,
        'vmid': Template_VMID['Template_VMID'],
        'name': NAME, # Only num and letters
    }

    return Send_Request('POST', Func, Data), Config_VM(NODE, VMID, Product)

## List Snapshots
def List_Snapshots(NODE, VMID):
    Func = '/nodes/{}/qemu/{}/snapshot'.format(NODE, VMID)

    return Send_Request('GET', Func)

## Create Snapshots
def Create_Snapshot(NODE, VMID, Name):
    Func = '/nodes/{}/qemu/{}/snapshot'.format(NODE, VMID)
    Data = {
        'snapname': Name
    }

    return Send_Request('POST', Func, Data)
