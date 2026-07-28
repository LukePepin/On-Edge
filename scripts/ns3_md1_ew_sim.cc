#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/flow-monitor-helper.h"
#include "ns3/ipv4-flow-classifier.h"
#include "ns3/error-model.h"
#include <iostream>
#include <fstream>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("ZkpLivelockSimulation");

int main (int argc, char *argv[])
{
  uint32_t nNodes = 10;
  uint32_t payloadSize = 64; // In Bytes
  double lambdaGlobal = 50.0; // 50Hz UR5 Kinematic Loop
  double ewJammingRate = 0.0; // Electronic Warfare packet drop rate (0.0 to 1.0)

  CommandLine cmd (__FILE__);
  cmd.AddValue ("nNodes", "Number of ZKP Edge Nodes generating the load", nNodes);
  cmd.AddValue ("payloadSize", "Cryptographic Payload Size in Bytes (64 for ECDSA/ZKP)", payloadSize);
  cmd.AddValue ("lambdaGlobal", "Global Arrival Rate / Kinematic Speed in Hz (Default: 50.0)", lambdaGlobal);
  cmd.AddValue ("ewJammingRate", "Electronic Warfare Packet Loss Ratio (0.0 to 1.0)", ewJammingRate);
  cmd.Parse (argc, argv);

  // 1. Empirical Mapping of Service Rate (mu) based on C-Wrapper Profiling
  // mu (pkts/sec) = 1.0 / 0.0096496 = 103.63
  double mu = 103.63;
  double nodeBandwidthBps = mu * payloadSize * 8.0;

  // 2. Topology Setup (Gateway Architecture for true M/D/1 queuing)
  NodeContainer brokerNode;
  brokerNode.Create(1);
  
  NodeContainer gatewayNode;
  gatewayNode.Create(1);
  
  NodeContainer edgeNodes;
  edgeNodes.Create(nNodes);

  InternetStackHelper stack;
  stack.Install(brokerNode);
  stack.Install(gatewayNode);
  stack.Install(edgeNodes);

  // 3. Bottleneck Link Configuration (Gateway to Broker)
  PointToPointHelper bottleneckP2P;
  bottleneckP2P.SetDeviceAttribute("DataRate", DataRateValue(DataRate(nodeBandwidthBps)));
  bottleneckP2P.SetChannelAttribute("Delay", StringValue("2ms"));
  bottleneckP2P.SetQueue("ns3::DropTailQueue<Packet>", "MaxSize", StringValue("1p"));

  NodeContainer bottleneckLink(gatewayNode.Get(0), brokerNode.Get(0));
  NetDeviceContainer bottleneckDevices = bottleneckP2P.Install(bottleneckLink);
  
  // High-speed LAN links for Edge -> Gateway
  PointToPointHelper lanP2P;
  lanP2P.SetDeviceAttribute("DataRate", StringValue("1Gbps"));
  lanP2P.SetChannelAttribute("Delay", StringValue("0.1ms"));
  
  Ipv4AddressHelper address;
  std::vector<Ipv4InterfaceContainer> edgeInterfaces;
  
  // Subnet 10.1.1.0 for the bottleneck link
  address.SetBase("10.1.1.0", "255.255.255.0");
  Ipv4InterfaceContainer bottleneckInterfaces = address.Assign(bottleneckDevices);

  // Subnets 10.1.x.0 for Edge -> Gateway links
  for (uint32_t i = 0; i < nNodes; i++) {
    NodeContainer lanLink(edgeNodes.Get(i), gatewayNode.Get(0));
    NetDeviceContainer lanDevices = lanP2P.Install(lanLink);
    
    std::ostringstream subnet;
    subnet << "10.1." << i + 2 << ".0";
    address.SetBase(subnet.str().c_str(), "255.255.255.0");
    edgeInterfaces.push_back(address.Assign(lanDevices));
  }

  // Populate Routing Tables
  Ipv4GlobalRoutingHelper::PopulateRoutingTables();

  // 4. Electronic Warfare (EW) Error Model Injection
  // We attach a RateErrorModel to the Broker's receiving device to simulate physical RF jamming
  if (ewJammingRate > 0.0) {
    Ptr<RateErrorModel> em = CreateObject<RateErrorModel>();
    em->SetAttribute("ErrorRate", DoubleValue(ewJammingRate));
    bottleneckDevices.Get(1)->SetAttribute("ReceiveErrorModel", PointerValue(em));
  }

  // 5. Traffic Generation (The DDS Kinematic Stream)
  double lambdaPerNode = lambdaGlobal / nNodes;
  double trafficRateBps = lambdaPerNode * payloadSize * 8.0;
  std::ostringstream trafficRateStr;
  trafficRateStr << trafficRateBps << "bps";

  uint16_t port = 9;
  
  // Broker acts as Sink
  PacketSinkHelper sink("ns3::UdpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), port));
  ApplicationContainer sinkApp = sink.Install(brokerNode.Get(0));
  sinkApp.Start(Seconds(0.0));
  sinkApp.Stop(Seconds(10.0));

  // Edge Nodes act as Clients blasting the Broker (via Gateway)
  for (uint32_t i = 0; i < nNodes; i++) {
    OnOffHelper onoff("ns3::UdpSocketFactory", InetSocketAddress(bottleneckInterfaces.GetAddress(1), port));
    onoff.SetConstantRate(DataRate(trafficRateStr.str()), payloadSize);
    
    // Eliminate OnOffHelper jitter by forcing ConstantRandomVariable
    onoff.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1.0]"));
    onoff.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0.0]"));
    
    ApplicationContainer clientApp = onoff.Install(edgeNodes.Get(i));
    clientApp.Start(Seconds(1.0));
    clientApp.Stop(Seconds(9.0));
  }

  // 6. Flow Monitor to track Livelock and Queue Saturation
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

  // 7. Mathematical Thesis Output
  std::cout << "\n==================================================================" << std::endl;
  std::cout << "          M/D/1 QUEUE SATURATION SIMULATION (EW JAMMING)          " << std::endl;
  std::cout << "==================================================================" << std::endl;
  std::cout << "Payload Size       : " << payloadSize << " Bytes" << std::endl;
  std::cout << "Active Edge Nodes  : " << nNodes << std::endl;
  std::cout << "EW Jamming Rate    : " << (ewJammingRate * 100.0) << "% Packet Loss" << std::endl;
  std::cout << "Service Rate (μ)   : " << mu << " pkts/sec (Total System Capacity)" << std::endl;
  std::cout << "Arrival Rate (λ)   : " << lambdaGlobal << " pkts/sec (Aggregated Global)" << std::endl;
  std::cout << "Traffic Intensity  : " << lambdaGlobal / mu << " (ρ = λ / μ)" << std::endl;
  std::cout << "------------------------------------------------------------------" << std::endl;
  std::cout << "Packets Sent       : " << totalTx << std::endl;
  std::cout << "Packets Received   : " << totalRx << std::endl;
  std::cout << "Packets Dropped    : " << totalDropped << " (" << dropRate << "% Drop Rate)" << std::endl;
  std::cout << "Average Queue Delay: " << avgDelayMs << " ms" << std::endl;
  
  if (dropRate > (ewJammingRate * 100.0) + 1.0 || (lambdaGlobal / mu) >= 1.0) {
    std::cout << "\n[RESULT] SYSTEM SATURATED! Traffic Intensity ρ > 1.0." << std::endl;
    std::cout << "The M/D/1 Queue cannot keep up. Data loss exceeds pure EW Jamming." << std::endl;
  } else {
    std::cout << "\n[RESULT] SYSTEM STABLE! Traffic Intensity ρ < 1.0." << std::endl;
    std::cout << "The deterministic cluster successfully load-balanced the stream." << std::endl;
  }
  std::cout << "==================================================================\n" << std::endl;

  // 8. CSV Export for Thesis Graphs
  std::ofstream csvFile;
  csvFile.open("simulation_results.csv", std::ios_base::app); // Append mode
  std::ifstream checkFile("simulation_results.csv");
  checkFile.seekg(0, std::ios::end);
  if (checkFile.tellg() == 0) {
      csvFile << "Nodes,PayloadSize,ServiceRate,ArrivalRate,TrafficIntensity,AvgDelayMs,DropRate,EWJammingRate,SystemCrash\n";
  }
  checkFile.close();
  
  int systemCrash = (dropRate > (ewJammingRate * 100.0) + 1.0 || (lambdaGlobal / mu) >= 1.0) ? 1 : 0;
  
  csvFile << nNodes << "," << payloadSize << "," << mu << "," << lambdaGlobal << "," << (lambdaGlobal / mu) << "," << avgDelayMs << "," << dropRate << "," << ewJammingRate << "," << systemCrash << "\n";
  csvFile.close();
  std::cout << "Results appended to simulation_results.csv" << std::endl;

  Simulator::Destroy();
  return 0;
}
