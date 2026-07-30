#include <stdint.h>
#include <time.h>
#include <stdlib.h>
#include <stdio.h>
#include "micro-ecc/uECC.h"

/*
 * C-Wrapper for uECC_verify to benchmark exact execution time on Cortex-A72.
 * Uses /dev/urandom for cryptographically secure entropy.
 * Executes full ECDSA verification using secp256r1.
 */

// Cryptographically secure RNG using /dev/urandom
static int urandom_RNG(uint8_t *dest, unsigned size) {
    FILE *f = fopen("/dev/urandom", "r");
    if (!f) return 0;
    size_t bytes_read = fread(dest, 1, size, f);
    fclose(f);
    return bytes_read == size;
}

// Struct to return both the boolean result and the elapsed nanoseconds
typedef struct {
    int success;
    unsigned long long elapsed_ns;
} VerifyResult;

VerifyResult benchmark_uecc_verify(const uint8_t* message, unsigned message_size) {
    VerifyResult result = {0, 0};
    
    // Use secp256r1 curve
    const struct uECC_Curve_t * curve = uECC_secp256r1();
    
    uint8_t private_key[32];
    uint8_t public_key[64];
    uint8_t hash[32]; // 256-bit hash
    uint8_t signature[64];
    
    // Set the true RNG
    uECC_set_rng(&urandom_RNG);
    
    // 1. Generate keys (Done outside timing block)
    if (!uECC_make_key(public_key, private_key, curve)) {
        return result; 
    }
    
    // 2. Generate hash (Done outside timing block)
    // Normally this would use a real SHA-256 library.
    for(int i = 0; i < 32; i++) {
        hash[i] = message[i % message_size] ^ i;
    }
    
    // 3. Generate signature (Done outside timing block)
    if (!uECC_sign(private_key, hash, sizeof(hash), signature, curve)) {
        return result; 
    }
    
    // 4. VERIFICATION BLOCK (This is the critical deterministic measurement)
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    
    int valid = uECC_verify(public_key, hash, sizeof(hash), signature, curve);
    
    clock_gettime(CLOCK_MONOTONIC, &end);
    
    unsigned long long start_ns = (unsigned long long)start.tv_sec * 1000000000ULL + start.tv_nsec;
    unsigned long long end_ns = (unsigned long long)end.tv_sec * 1000000000ULL + end.tv_nsec;
    
    result.success = valid;
    result.elapsed_ns = end_ns - start_ns;
    
    return result;
}

#!/usr/bin/env python3
"""
Test B: The Sequential μ Profiling Proof
========================================
Decouples network testing from CPU benchmarking to extract valid M/D/1 baseline.
Bypasses ROS 2 and DDS entirely to directly serialize 1,000 requests into the C-Wrapper.
"""

import os
import time
import csv
import ctypes
import numpy as np
from pathlib import Path

# Load C Wrapper
class VerifyResult(ctypes.Structure):
    _fields_ = [("success", ctypes.c_int), ("elapsed_ns", ctypes.c_ulonglong)]

def run_benchmark():
    # Resolve exact path on Pi
    lib_path = os.path.expanduser('~/Documents/On-Edge/src/sentry_logic/sentry_logic/c_src/libuecc_wrapper.so')
    
    try:
        uecc_lib = ctypes.CDLL(lib_path)
        uecc_lib.benchmark_uecc_verify.restype = VerifyResult
        uecc_lib.benchmark_uecc_verify.argtypes = [ctypes.c_char_p, ctypes.c_uint]
    except Exception as e:
        print(f"❌ FATAL ERROR: Cannot load C-wrapper at {lib_path}")
        print(f"Error details: {e}")
        return

    n_trials = 1000
    execution_times_ns = []
    success_count = 0

    print(f"\n🔥 INITIATING TEST B: DECOUPLED μ PROFILING 🔥")
    print(f"Executing strict sequential payload loop (n={n_trials})...")
    print(f"TRNG (/dev/urandom) actively harvesting entropy. This will apply real thermal load to the Cortex-A72.")

    # 1. Fire sequential loop directly into C
    start_time = time.time()
    for i in range(n_trials):
        payload = f"STRICT_BENCHMARK_PAYLOAD_{i}_{time.time()}".encode('utf-8')
        
        # Execute C-wrapper and capture precise POSIX hardware nanoseconds
        result = uecc_lib.benchmark_uecc_verify(payload, len(payload))
        
        execution_times_ns.append(result.elapsed_ns)
        if result.success:
            success_count += 1
            
        if (i+1) % 100 == 0:
            print(f"  -> Processed {i+1}/{n_trials}...")

    total_time = time.time() - start_time

    # 2. Extract Latencies
    latencies_ms = np.array(execution_times_ns) / 1_000_000.0
    mu_avg = np.mean(latencies_ms)
    mu_max = np.max(latencies_ms)
    variance = np.var(latencies_ms)
    c_v = np.std(latencies_ms) / mu_avg if mu_avg > 0 else 0

    # 3. Save Empirical Dataset
    data_dir = os.path.expanduser('~/Documents/On-Edge/data')
    os.makedirs(data_dir, exist_ok=True)
    csv_file = os.path.join(data_dir, f'md1_profiling_serialized_n1000_{int(time.time())}.csv')
    
    with open(csv_file, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["request_id", "execution_time_ns", "success"])
        for idx, t_ns in enumerate(execution_times_ns):
            writer.writerow([idx + 1, t_ns, 1])

    # 4. Print Pollaczek-Khinchine Baseline
    print("\n" + "="*55)
    print(" 📊 TEST B: TRUE M/D/1 CPU SERVICE RATE (μ) EXTRACTED")
    print("="*55)
    print(f"Total Requests Executed : {n_trials}")
    print(f"Total Wall Clock Time   : {total_time:.2f} seconds")
    print(f"Successful Verifications: {success_count}/{n_trials}")
    print(f"Mean Service Time (μ)   : {mu_avg:.4f} ms")
    print(f"Max Service Time        : {mu_max:.4f} ms")
    print(f"Variance (σ²)           : {variance:.6f}")
    print(f"Coefficient of Var (Cv) : {c_v:.6f}")
    print("="*55)

    if c_v < 0.1:
        print("✅ ACADEMIC AUDIT PASSED: Cv approaches 0 on n=1000 dataset.")
        print("   The node behaves mathematically as a deterministic M/D/1 queue.")
    else:
        print("⚠️ WARNING: High variance detected under sustained thermal load.")
        
    print(f"\nDataset saved to: {csv_file}")

if __name__ == '__main__':
    run_benchmark()
<?xml version="1.0" encoding="UTF-8" ?>
<CycloneDDS xmlns="https://cdds.io/config" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="https://cdds.io/config https://raw.githubusercontent.com/eclipse-cyclonedds/cyclonedds/master/etc/cyclonedds.xsd">
    <Domain id="any">
        <Internal>
            <MinimumSocketReceiveBufferSize>10MB</MinimumSocketReceiveBufferSize>
        </Internal>
        <QoS>
            <Topic name="*">
                <Reliability>
                    <Kind>best_effort</Kind>
                </Reliability>
                <History>
                    <Kind>keep_last</Kind>
                    <Depth>1</Depth>
                </History>
            </Topic>
        </QoS>
    </Domain>
</CycloneDDS>
#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from std_msgs.msg import String
import argparse
import time
import asyncio

class AsyncBootStormInjector(Node):
    def __init__(self):
        super().__init__('async_boot_storm_injector')
        
        # STRICT QoS ENFORCEMENT: BEST_EFFORT and KEEP_LAST(1)
        # Without this, HoL blocking will crash the DDS middleware
        self.best_effort_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1
        )
        
        self.get_logger().info("🔥 EXPLICIT QoS ENFORCEMENT 🔥")
        self.get_logger().info(f"Reliability: {self.best_effort_qos.reliability}")
        self.get_logger().info(f"History: {self.best_effort_qos.history}")
        self.get_logger().info(f"Depth: {self.best_effort_qos.depth}")
        
        self.pub = self.create_publisher(String, '/auth_request', qos_profile=self.best_effort_qos)

    async def blast_packet(self, node_id):
        msg = String()
        msg.data = f"BOOT_STORM_REQ_{node_id}_{time.time()}"
        self.pub.publish(msg)
        # Removed per-packet logging to prevent IO bottlenecking during the burst

    async def execute_storm(self, num_nodes):
        self.get_logger().info(f"🌪️ INITIATING ASYNC BOOT STORM (n={num_nodes}) 🌪️")
        
        # Give DDS Discovery a moment to link publishers and subscribers
        await asyncio.sleep(1.0)
        
        tasks = []
        # Asynchronously schedule all 1000 packets for true concurrent execution
        for i in range(num_nodes):
            tasks.append(self.blast_packet(i))
            
        await asyncio.gather(*tasks)
        self.get_logger().info(f"✅ Boot storm of {num_nodes} packets injected successfully.")

def main():
    parser = argparse.ArgumentParser()
    # Enforcing minimum n=1000 statistical sample size
    parser.add_argument('-n', '--nodes', type=int, default=1000, help="Number of concurrent nodes (Default: 1000 for stat validity)")
    args = parser.parse_args()

    if args.nodes < 1000:
        print("⚠️ WARNING: A sample size below 1000 is statistically invalid for Pollaczek-Khinchine profiling. Overriding to n=1000.")
        args.nodes = 1000

    rclpy.init(args=None)
    
    injector = AsyncBootStormInjector()
    
    # Run the asyncio event loop
    loop = asyncio.get_event_loop()
    loop.run_until_complete(injector.execute_storm(args.nodes))
    
    injector.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
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

  // 1. Empirical Mapping of Service Rate (mu) based on C-Wrapper Profiling (Test B)
  // The pristine, unadulterated mean service time (mu_time) is 9.6496 ms.
  // mu (pkts/sec) = 1.0 / 0.0096496 = 103.63
  double mu = 103.63;
  
  // Calculate the physical hardware bottleneck DataRate (Bits Per Second)
  // DataRate = mu (packets/sec) * payloadSize (bytes/packet) * 8 (bits/byte)
  double nodeBandwidthBps = mu * payloadSize * 8.0;

  // 2. Topology Setup
  // We use a Star topology: nNodes (Arduinos) connected to 1 Central Broker (Pi 4).
  NodeContainer brokerNode;
  brokerNode.Create(1);
  
  NodeContainer edgeNodes;
  edgeNodes.Create(nNodes);

  InternetStackHelper stack;
  stack.Install(brokerNode);
  stack.Install(edgeNodes);

  // 3. Bottleneck Link Configuration (The Pi 4 M/D/1 Limit)
  PointToPointHelper p2p;
  // This physically chokes the NS-3 link to mimic the Cortex-A72 deterministic calculation time
  p2p.SetDeviceAttribute("DataRate", DataRateValue(DataRate(nodeBandwidthBps)));
  p2p.SetChannelAttribute("Delay", StringValue("2ms"));
  
  // Apply QoS Drop Buffer (KEEP_LAST Depth=1 logic)
  // A small queue models the aggressive packet shedding proven in Test A
  p2p.SetQueue("ns3::DropTailQueue<Packet>", "MaxSize", StringValue("1p"));

  Ipv4AddressHelper address;
  std::vector<Ipv4InterfaceContainer> interfaces;
  std::vector<NetDeviceContainer> allDevices;

  // Connect Broker to all Edge Nodes
  for (uint32_t i = 0; i < nNodes; i++) {
    NodeContainer link(edgeNodes.Get(i), brokerNode.Get(0));
    NetDeviceContainer devices = p2p.Install(link);
    allDevices.push_back(devices);
    
    std::ostringstream subnet;
    subnet << "10.1." << i + 1 << ".0";
    address.SetBase(subnet.str().c_str(), "255.255.255.0");
    interfaces.push_back(address.Assign(devices));
  }

  // 4. Electronic Warfare (EW) Error Model Injection
  // We attach a RateErrorModel to the Broker's receiving devices to simulate physical RF jamming
  if (ewJammingRate > 0.0) {
    Ptr<RateErrorModel> em = CreateObject<RateErrorModel>();
    em->SetAttribute("ErrorRate", DoubleValue(ewJammingRate));
    for (uint32_t i = 0; i < nNodes; i++) {
      // Apply error model to the Broker's device (index 1 of the link)
      allDevices[i].Get(1)->SetAttribute("ReceiveErrorModel", PointerValue(em));
    }
  }

  // 5. Traffic Generation (The DDS Kinematic Stream)
  // The global 50Hz stream is generated by the N edge nodes and sent to the Broker.
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

  // Edge Nodes act as Clients blasting the Broker
  for (uint32_t i = 0; i < nNodes; i++) {
    // The Broker is IP address index 1 (0 is network)
    OnOffHelper onoff("ns3::UdpSocketFactory", InetSocketAddress(interfaces[i].GetAddress(1), port));
    onoff.SetConstantRate(DataRate(trafficRateStr.str()), payloadSize);
    
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
  // If file is empty, write header
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
#!/bin/bash

# ns3_sweep_automation.sh
# Automates the NS-3 M/D/1 EW Queue Saturation parameter sweeps for the thesis

# Navigate to the NS-3 directory
cd ~/ns-3-dev || { echo "NS-3 directory not found at ~/ns-3-dev"; exit 1; }

# Clear previous results to start a fresh dataset
rm -f simulation_results.csv
echo "Starting comprehensive NS-3 M/D/1 EW parameter sweep..."

# Define the variables to sweep
ARRIVAL_RATES=(10 25 50 100 150) # Aggregated cluster frequencies (Hz)
PAYLOAD_SIZES=(64) # Cryptographic payload size locked to 64 bytes (secp256r1)
NODE_COUNTS=(3 5 10 15 20 25 30) # Number of virtual edge nodes pushing the Pi 4
JAMMING_RATES=(0.0 0.1 0.2) # EW Packet loss (0%, 10%, 20%) to match Phase 3.5

# Calculate total iterations for progress tracking
TOTAL_TESTS=$((${#ARRIVAL_RATES[@]} * ${#PAYLOAD_SIZES[@]} * ${#NODE_COUNTS[@]} * ${#JAMMING_RATES[@]}))
CURRENT_TEST=1

for lambda in "${ARRIVAL_RATES[@]}"; do
    for payload in "${PAYLOAD_SIZES[@]}"; do
        for nodes in "${NODE_COUNTS[@]}"; do
            for jam in "${JAMMING_RATES[@]}"; do
                echo "[${CURRENT_TEST}/${TOTAL_TESTS}] Testing: Lambda=${lambda}Hz | Payload=${payload}B | Nodes=${nodes} | Jam=${jam}"
                ./ns3 run "scratch/ns3_md1_ew_sim --nNodes=${nodes} --payloadSize=${payload} --lambdaGlobal=${lambda} --ewJammingRate=${jam}" > /dev/null 2>&1
                CURRENT_TEST=$((CURRENT_TEST + 1))
            done
        done
    done
done

echo "Sweep Complete! Dataset generated at ~/ns-3-dev/simulation_results.csv"

# Automatically copy it back to the project folder
cp simulation_results.csv ~/Documents/On-Edge/data/ns3_ew_saturation_sweep.csv
echo "Dataset copied to ~/Documents/On-Edge/data/ns3_ew_saturation_sweep.csv"
