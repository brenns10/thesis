Testing
=======

Prerequisites for this are [SETUP_CLIENT.md](SETUP_CLIENT.md)
and [SETUP_DETOUR.md](SETUP_DETOUR.md).

The process for a full, end-to-end test is simple enough. It requires the two
machines above (client and detour---they must be different). The client needs to
have a free ethernet port, along with a wireless port. The ethernet port will be
bridged to by the vm (covered in the docs).

1. First, on your detour machine, run `sudo python detour.py`. It will
   immediately output the following:
   
   ```
   net.ipv4.ip_forward = 1
   ```
   
   This informs you that the kernel will forward packets that are not addressed
   to it. The detour server will listen for requests over UDP
   (see [MPROXY.md](MPROXY.md) for documentation on the protocol). For each one
   it will create a detour and respond back with the details. It will also
   produce a line of output for every request.
   
2. Next, on your client machine, run the following command (within the `src`
   directory of this repository). Note that this assumes you have got the bridge
   set up properly on your machine.
   
   ```
   vido --kvm --kernel ~/repos/mptcp/arch/x86_64/boot/bzImage --bridge bridge0 -- sh
   ```
   
3. Once the VM boots (very quickly) you will have a shell prompt. Your first
   step ought to be `ip addr` to ensure that you have DHCP'd an IP address. If
   not, it's time to debug the VM.
   
3. Within the VM, first run the following command:

   ```
   sudo ./client daemon IP_OF_DETOUR >output 2>&1 &
   ```
   
   This will run the daemon, and it will do so in the background, and it will
   save its output in `output` so that you can see what happened.
   
4. If you have monitoring set up, now is a great time to make sure you have your
   Wireshark tunneled and running, according
   to [SETUP_MONITORING.md](SETUP_MONITORING.md).
   
5. Within the VM, do a `telnet multipath-tcp.org 80`. Type out the HTTP request:

   ```
   GET / HTTP/1.1
   Host: multipath-tcp.org
   
   
   ```
   
6. Once the response finishes and the connection is closed, check your dmesg
   output. You should see something like this:
   
   ```
   [   17.238110] detour create_subflow_worker() begins
   [   17.238119] request_detour()
   [   17.238128] Finding matching detour for 130.104.230.45:20480
   [   17.238129] detour create_subflow_worker() ends
   [   17.303670] Adding a detour to the entry list.
   [   17.303719] detour create_subflow_worker() begins
   [   17.303721] Finding matching detour for 130.104.230.45:20480
   [   17.303723] Checking detour=192.168.0.2:20480 remote=130.104.230.45:20480
   [   17.303723] yes
   [   17.303900] detour create_subflow_worker() ends
   ```
   
   (the port number 20480 is a bug, I need to `ntohs` before printing)
   
   Your packet capture should further reflect the fact that there are two
   subflows in the connection, and both are being used for data correctly. Be
   sure to use Wireshark's coloring tools to help organize the connections. Note
   that Wireshark will see 3 TCP flows, not 2! Color the flow from client to
   detour and detour to server in similar colors, and then the master subflow
   (i.e. client to server) in a dissimilar color. It helps!
   
The basic flow of events:
- User space program creates connection.
- Once the MPTCP flow is fully established, the kernel calls the path manager,
  and we queue work to establish our subflows.
- The first time our worker is called, it notes that we haven't requested a
  detour from the netlink socket just yet. So, we request the detour, and then
  we move on with searching for a detour. Since we see no available detour, we
  exit out.
- The user-space daemon hears this request and sends a UDP request to the detour
  server.
- The detour server receives this request, executes the proper iptables commands
  to set up a NAT tunnel, and then sends back a response with the details.
- The user-space daemon receives this response and sends the details back to the
  kernel through the netlink socket.
- Upon receiving this information, the kernel wakes up its subflow workers.
- This time, the subflow worker does not send a new request. Instead, it
  searches for a detour, and this time finds one. It establishes a subflow!

The next thing to get working is OpenVPN tunneling!
