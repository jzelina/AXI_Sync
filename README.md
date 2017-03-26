#Title: AXI_Sync
-----------------------------------------------------------
Script to connect with SIP-DECT system(s) via AXI
and perform, configuration, update or inventory operations.

About:
------
This tool connects via AXI to a given list of SIP-DECT systems (OMMs).
Depending on the configured mode the following actions can be performed:

- inventory: log some system information (good to test script as no changes are performed)
- update = Initiate a software and configuration update request. (Update Button)
- setconfig: Set the ConfigURL + UpdateTime + Credentials if provided

Deployment / Configution:
-------------------------

1) Requirements:

- Deployed SIP-DECT systems in Release 6.0 or higher.
- Operating system e.g. Windows or Linux with python (e.g. 2.7) installed.

To Install python on Windows:
1) Go to www.python.org and Download your python version (e.g. 2.7)
2) Start the installer and continue with the defaults, option step: enable register path option

2) Configution

Create a list of OMM IP-Addresses in config/ip.csv
# File format per line: OMM-IP;UpdateMinute(optional)
# 10.10.1.100;1
# 10.10.1.101;

Edit the configuration file /config/config.cfg
- Set username and password to match your OMMs.
- Set the mode (none,setconfig,update)
- Set the delay (pause) per system
- If mode is set to setconfig: Configure ConfigURL, Credentials, UpdateHour

3) Run script

Execute the axi_sync.py script.
E.g.: 
python axi_sync.py
C:\Python27\python.exe axi_sync.py
(if python is not registered via path in your system, use the full path to python.exe)


disclaimer
----------
This applications are provided "as is" and any express or implied warranties, including, but not limited to, the implied warranties 
of merchantability and fitness for a particular purpose are disclaimed.
