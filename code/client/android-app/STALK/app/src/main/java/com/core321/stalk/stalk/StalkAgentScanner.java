// StalkAgentScanner

package com.core321.stalk.stalk;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.util.List;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Date;
import android.util.Log;


public class StalkAgentScanner {
    static final int BROADCAST_PORT = 8988;
    static final String PREFIX = "STALKAGENT@";

    public interface Listener {
        void agentListChanged();
    };

    private Listener listener;
    private final ArrayList<StalkAgent> agents = new ArrayList<StalkAgent>();
    private final HashMap<String, StalkAgent> hostToAgents = new HashMap<String, StalkAgent>();
    private Thread networkThread;
    private boolean stopThread;


    public List<StalkAgent> getAgents() {
        synchronized(this) {
            return agents;
        }
    }

    public void start(Listener listener) {
        this.listener = listener;

        createUDPSocket();

        //
        new Thread(new Runnable() {
            @Override
            public void run() {
                while(true) {
                    sweepGarbages();
                    try {
                        Thread.sleep(10 * 1000);
                    }
                    catch(InterruptedException e) {

                    }
                }

            }
        }).start();
    }

    private void sweepGarbages() {
        Date cut = new Date();
        cut.setTime(cut.getTime() - 10 * 1000);


        ArrayList<String> names = null;
        ArrayList<StalkAgent> agents = null;

        for(String hostName : hostToAgents.keySet()) {
            StalkAgent agent = hostToAgents.get(hostName);
            if (agent.updateTime.before(cut)) {
                if (names == null) {
                    names = new ArrayList<>();
                }
                names.add(hostName);

                if (agents == null) {
                    agents = new ArrayList<>();
                }
                agents.add(agent);
            }
        }

        if (names != null && agents != null) {
            for(String hostName : names) {
                this.hostToAgents.remove(hostName);
            }
            for(StalkAgent agent : agents) {
                this.agents.remove(agent);
            }

            if (names.size() > 0) {
                if (listener != null) {
                    listener.agentListChanged();
                }
            }
        }
    }

    private void createUDPSocket() {
        if (networkThread != null) {
            stopThread = true;
            try {
                networkThread.join();
            }
            catch(java.lang.InterruptedException e) {

            }
            networkThread = null;
        }

        networkThread = new Thread(new Runnable(){
            @Override
            public void run() {
                try {
                    DatagramSocket s = new DatagramSocket(BROADCAST_PORT);
                    while(!stopThread) {
                        byte[] buf = new byte[1024];
                        DatagramPacket packet = new DatagramPacket(buf, buf.length);
                        s.receive(packet);
                        String msg = new String(packet.getData(), 0, packet.getLength());

                        updateAgents(msg, packet.getAddress());
                    }

                } catch(Exception e) {
                    Log.d("STALK", e.getMessage());

                }
            }
        });
        networkThread.start();
    }

    void updateAgents(String msg, InetAddress inetAddress) {
        if (msg.startsWith(PREFIX)) {

            String ipAddress = inetAddress.toString().substring(1);
            String hostName = null;
            int webUiPort = 0;
            int webSshPort = 0;

            String[] lines = msg.split("\n");

            if (lines.length > 0) {
                // first line
                String s = lines[0];
                int index = PREFIX.length();
                hostName = s.substring(index);

                // remaining lines
                for(int i = 1; i < lines.length; ++i) {
                    s = lines[i];
                    if (s.startsWith("WEB_UI:")) {
                        index = "WEB_UI:".length();
                        webUiPort = Integer.parseInt(s.substring(index));
                    }
                    else if (s.startsWith("WEB_SSH:")) {
                        index = "WEB_SSH:".length();
                        webSshPort = Integer.parseInt(s.substring(index));
                    }
                }

                StalkAgent res = hostToAgents.get(hostName);
                if (res != null) {
                    res.updateTime = new Date();
                    boolean dirty = false;

                    if (res.webUiPort != webUiPort) {
                        res.webUiPort = webUiPort;
                        dirty = true;
                    }
                    if (res.webSshPort != webSshPort) {
                        res.webSshPort = webSshPort;
                        dirty = true;
                    }
                    if (!res.ipAddress.equals(ipAddress)) {
                        res.ipAddress = ipAddress;
                        dirty = true;
                    }

                    if (dirty && listener != null) {
                        listener.agentListChanged();
                    }
                }
                else {
                    res = new StalkAgent();
                    res.hostName = hostName;
                    res.webUiPort = webUiPort;
                    res.webSshPort = webSshPort;
                    res.ipAddress = ipAddress;
                    res.updateTime = new Date();
                    synchronized(this) {
                        hostToAgents.put(hostName, res);
                        agents.add(res);
                    }

                    if (listener != null) {
                        listener.agentListChanged();
                    }
                }
            }
        }
    }

}
