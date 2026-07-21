#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/flow-monitor-helper.h"
#include "ns3/ipv4-flow-classifier.h"
#include <iostream>
#include <fstream>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("ZkpLivelockSimulation");

int main (int argc, char *argv[])
{
  uint32_t nNodes = 10;
  uint32_t payloadSize = 64; // In Bytes
  double lambdaGlobal = 50.0; // 50Hz UR5 Kinematic Loop

  CommandLine cmd (__FILE__);
  cmd.AddValue ("nNodes", "Number of ZKP Edge Nodes sharing the load", nNodes);
  cmd.AddValue ("payloadSize", "Cryptographic Payload Size in Bytes (1, 8, 32, 64)", payloadSize);
  cmd.Parse (argc, argv);

  // 1. Empirical Mapping of Service Rate (mu) based on CSV Evaluation
  double mu = 0.0;
  if (payloadSize == 1) mu = 8.65;
  else if (payloadSize == 8) mu = 7.22;
  else if (payloadSize == 32) mu = 4.60;
  else if (payloadSize == 64) mu = 3.10;
  else {
    std::cout << "Error: Payload size must be 1, 8, 32, or 64 to match empirical data." << std::endl;
    return 1;
  }

  // Calculate the physical hardware bottleneck DataRate (Bits Per Second)
  // DataRate = mu (packets/sec) * payloadSize (bytes/packet) * 8 (bits/byte)
  double nodeBandwidthBps = mu * payloadSize * 8.0;

  // 2. Topology Setup
  // We use a Star topology: 1 Central Broker connected to nNodes.
  NodeContainer brokerNode;
  brokerNode.Create(1);
  
  NodeContainer edgeNodes;
  edgeNodes.Create(nNodes);

  InternetStackHelper stack;
  stack.Install(brokerNode);
  stack.Install(edgeNodes);

  // 3. Bottleneck Link Configuration (The ZKP Cortex-M4 Limit)
  PointToPointHelper p2p;
  // This physically chokes the NS-3 link to mimic the Cortex-M4 ZKP calculation time
  p2p.SetDeviceAttribute("DataRate", DataRateValue(DataRate(nodeBandwidthBps)));
  p2p.SetChannelAttribute("Delay", StringValue("2ms"));
  
  // The Arduino Nano 33 BLE has incredibly limited RAM. We limit the Queue to 10 packets.
  p2p.SetQueue("ns3::DropTailQueue<Packet>", "MaxSize", StringValue("10p"));

  Ipv4AddressHelper address;
  std::vector<Ipv4InterfaceContainer> interfaces;

  // Connect Broker to all Edge Nodes
  for (uint32_t i = 0; i < nNodes; i++) {
    NodeContainer link(brokerNode.Get(0), edgeNodes.Get(i));
    NetDeviceContainer devices = p2p.Install(link);
    
    std::ostringstream subnet;
    subnet << "10.1." << i + 1 << ".0";
    address.SetBase(subnet.str().c_str(), "255.255.255.0");
    interfaces.push_back(address.Assign(devices));
  }

  // 4. Traffic Generation (The DDS Kinematic Stream)
  // The global 50Hz stream is load-balanced (sharded) across the N nodes.
  double lambdaPerNode = lambdaGlobal / nNodes;
  double trafficRateBps = lambdaPerNode * payloadSize * 8.0;
  std::ostringstream trafficRateStr;
  trafficRateStr << trafficRateBps << "bps";

  uint16_t port = 9;
  for (uint32_t i = 0; i < nNodes; i++) {
    PacketSinkHelper sink("ns3::UdpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), port));
    ApplicationContainer sinkApp = sink.Install(edgeNodes.Get(i));
    sinkApp.Start(Seconds(0.0));
    sinkApp.Stop(Seconds(10.0));

    OnOffHelper onoff("ns3::UdpSocketFactory", InetSocketAddress(interfaces[i].GetAddress(1), port));
    onoff.SetConstantRate(DataRate(trafficRateStr.str()), payloadSize);
    
    ApplicationContainer clientApp = onoff.Install(brokerNode.Get(0));
    clientApp.Start(Seconds(1.0));
    clientApp.Stop(Seconds(9.0));
  }

  // 5. Flow Monitor to track Livelock and Queue Saturation
  FlowMonitorHelper flowmon;
  Ptr<FlowMonitor> monitor = flowmon.InstallAll();

  Simulator::Stop(Seconds(10.0));
  Simulator::Run();

  monitor->CheckForLostPackets();
  Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier>(flowmon.GetClassifier());
  std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats();

  uint32_t totalTx = 0;
  uint32_t totalRx = 0;
  uint32_t totalDropped = 0;
  double totalDelay = 0.0;

  for (std::map<FlowId, FlowMonitor::FlowStats>::const_iterator i = stats.begin(); i != stats.end(); ++i) {
    totalTx += i->second.txPackets;
    totalRx += i->second.rxPackets;
    totalDropped += i->second.lostPackets;
    if (i->second.rxPackets > 0) {
      totalDelay += i->second.delaySum.GetSeconds();
    }
  }

  double avgDelayMs = (totalRx > 0) ? (totalDelay / totalRx) * 1000.0 : 0.0;
  double dropRate = (totalTx > 0) ? ((double)totalDropped / totalTx) * 100.0 : 0.0;

  // 6. Mathematical Thesis Output
  std::cout << "\n==================================================================" << std::endl;
  std::cout << "               M/M/1 QUEUE SATURATION SIMULATION                  " << std::endl;
  std::cout << "==================================================================" << std::endl;
  std::cout << "Payload Size       : " << payloadSize << " Bytes" << std::endl;
  std::cout << "Active Edge Nodes  : " << nNodes << std::endl;
  std::cout << "Service Rate (μ)   : " << mu << " pkts/sec (Per Node)" << std::endl;
  std::cout << "Arrival Rate (λ)   : " << lambdaPerNode << " pkts/sec (Per Node)" << std::endl;
  std::cout << "Traffic Intensity  : " << lambdaPerNode / mu << " (ρ = λ / μ)" << std::endl;
  std::cout << "------------------------------------------------------------------" << std::endl;
  std::cout << "Packets Sent       : " << totalTx << std::endl;
  std::cout << "Packets Received   : " << totalRx << std::endl;
  std::cout << "Packets Dropped    : " << totalDropped << " (" << dropRate << "% Drop Rate)" << std::endl;
  std::cout << "Average Queue Delay: " << avgDelayMs << " ms" << std::endl;
  
  if (dropRate > 0.0 || (lambdaPerNode / mu) >= 1.0) {
    std::cout << "\n[RESULT] SYSTEM CRASH! Traffic Intensity ρ > 1.0." << std::endl;
    std::cout << "The M/M/1 Queue has grown to infinity resulting in Livelock." << std::endl;
  } else {
    std::cout << "\n[RESULT] SYSTEM STABLE! Traffic Intensity ρ < 1.0." << std::endl;
    std::cout << "The decentralized cluster successfully load-balanced the 50Hz stream." << std::endl;
  }
  std::cout << "==================================================================\n" << std::endl;

  // 7. CSV Export for Thesis Graphs
  std::ofstream csvFile;
  csvFile.open("simulation_results.csv", std::ios_base::app); // Append mode
  // If file is empty, write header
  std::ifstream checkFile("simulation_results.csv");
  checkFile.seekg(0, std::ios::end);
  if (checkFile.tellg() == 0) {
      csvFile << "Nodes,PayloadSize,ServiceRate,ArrivalRate,TrafficIntensity,AvgDelayMs,DropRate\n";
  }
  checkFile.close();
  csvFile << nNodes << "," << payloadSize << "," << mu << "," << lambdaPerNode << "," << (lambdaPerNode / mu) << "," << avgDelayMs << "," << dropRate << "\n";
  csvFile.close();
  std::cout << "Results appended to simulation_results.csv" << std::endl;

  Simulator::Destroy();
  return 0;
}
